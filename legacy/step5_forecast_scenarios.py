"""Step 5 — exploratory country religion-share simulations from Pew 2020 to 3026.

Run beside Steps 3 and 4:  .\\.venv\\Scripts\\python.exe step5_forecast_scenarios.py

This is NOT a validated prediction of the third millennium. After 2100, country
populations, fertility, age, and secularization rely on explicit scenarios.
WRP-trained LightGBM is downweighted after 2100 and disabled by 2200 in the
Monte Carlo simulations. Monte Carlo bands express assumed scenario/residual
variation; they are not calibrated statistical prediction intervals.
"""
from __future__ import annotations
import argparse
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from step3_engineer_features import geographic_reference
from step4_train_validate import CATEGORIES, SHARES, apply_clr_delta, simplex_projection

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'forecasts'
RAW = ROOT / 'data' / 'processed'
FEATURE = ROOT / 'data' / 'features'
MODEL = ROOT / 'data' / 'models'
K = len(CATEGORIES)
TARGET_YEARS = [2020, 2050, 2100, 2200, 2500, 3026]
YEARS = sorted(set(range(2020, 3031, 5)) | {3026})
SCENARIOS = [('converge', 'continues'), ('converge', 'plateaus'),
             ('persist', 'continues'), ('persist', 'plateaus')]
PEW_2050_PCT = {'Christianity': 31.4, 'Islam': 29.7, 'Hinduism': 14.9,
    'Buddhism': 5.2, 'Judaism': 0.2, 'Folk_Traditional': 4.8,
    'Other': 0.7, 'Unaffiliated': 13.2}
PEW_PROJ_URL = 'https://www.pewresearch.org/religion/2015/04/02/population-projections-by-religious-group/'


def validate_simplex(shares, where):
    arr = np.asarray(shares, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != K or not np.isfinite(arr).all():
        raise ValueError(f'{where}: invalid shape or non-finite shares')
    if (arr < -1e-8).any() or (arr > 1+1e-8).any() or not np.allclose(arr.sum(1), 1, atol=1e-7):
        raise ValueError(f'{where}: shares not in simplex')


def wpp_loader():
    wpp = pd.read_csv(RAW / 'wpp_country_year.csv', low_memory=False)
    required = {'country_id','year','tfr','median_age','wpp_population',
                'net_migrations','crude_net_migration_rate'}
    missing = required - set(wpp.columns)
    if missing:
        raise ValueError(f'WPP columns missing: {sorted(missing)}')
    wpp = wpp[list(required)].copy()
    wpp['year'] = pd.to_numeric(wpp['year'], errors='raise').astype(int)
    if wpp.duplicated(['country_id','year']).any():
        raise ValueError('Duplicate WPP country-years')
    return wpp


def load_sources():
    anchors = pd.read_csv(FEATURE / 'pew_2020_anchor_context.csv', low_memory=False)
    anchors = anchors[anchors.year.eq(2020)].copy().sort_values('country_id').reset_index(drop=True)
    if anchors.empty or anchors.country_id.duplicated().any():
        raise ValueError('No unique Pew 2020 country anchors')
    validate_simplex(anchors[SHARES].to_numpy(float), 'Pew 2020')
    # No Pew 2015 measurement exists: explicit straight-line approximation.
    lag10cols = [f'pew_2010_{col}' for col in SHARES]
    if not set(lag10cols).issubset(anchors.columns):
        raise ValueError('Missing Pew 2010 shares in Step 3 anchor context')
    current = anchors[SHARES].to_numpy(float)
    decade = anchors[lag10cols].to_numpy(float)
    missing_decade = ~np.isfinite(decade).all(axis=1)
    decade[missing_decade] = current[missing_decade]
    validate_simplex(decade, 'Pew 2010')
    lag5 = 0.5 * (current + decade)  # 2015 artificial initialization only
    wpp = wpp_loader()
    bundle = joblib.load(MODEL / 'lightgbm_all_wrp.joblib')
    if bundle.get('model_name') != 'lightgbm' or bundle.get('estimator') is None:
        raise ValueError('Expected trained LightGBM in lightgbm_all_wrp.joblib')
    predictors = bundle['predictors']
    if bundle.get('shares') != SHARES:
        raise ValueError('Model categories differ from Step 3')
    resid_file = MODEL / 'one_step_predictions.csv'
    pred = pd.read_csv(resid_file, low_memory=False)
    pred = pred[pred.model.eq('lightgbm')].copy()
    if pred.empty:
        raise ValueError('No out-of-fold LightGBM residuals available')
    resid = (pred[[f'actual_{cat}' for cat in CATEGORIES]].to_numpy(float)
        - pred[[f'pred_{cat}' for cat in CATEGORIES]].to_numpy(float))
    # Empirical residuals are centered; these are not country-specific credible intervals.
    resid -= resid.mean(axis=0, keepdims=True)
    resid -= resid.mean(axis=1, keepdims=True)
    continents, neighbors = geographic_reference()
    return anchors, current, lag5, decade, missing_decade, wpp, bundle, predictors, resid, continents, neighbors


def spatial_matrices(ids, continents, neighbors):
    index = {str(cid): i for i, cid in enumerate(ids)}
    n = len(ids)
    def from_lists(f):
        ri, ci, data, counts = [], [], [], np.zeros(n, dtype=int)
        for i, cid in enumerate(ids):
            eligible = sorted({int(index[c]) for c in f(str(cid)) if c in index and index[c] != i})
            counts[i] = len(eligible)
            if eligible:
                ri.extend([i]*len(eligible)); ci.extend(eligible)
                data.extend([1.0/len(eligible)]*len(eligible))
        return csr_matrix((data, (ri,ci)), shape=(n,n)), counts
    border, border_n = from_lists(lambda cid: neighbors.get(cid, []))
    grouped = {}
    for cid in ids:
        if cid in continents:
            grouped.setdefault(continents[cid], []).append(str(cid))
    continent, continent_n = from_lists(lambda cid: grouped.get(continents.get(cid), []))
    return border, border_n, continent, continent_n


def wpp_arrays(ids, wpp):
    # WPP medium projected values are used only up to 2100.
    frame = pd.MultiIndex.from_product([list(ids), list(range(2020,2101,5))],
                                       names=['country_id','year']).to_frame(index=False)
    frame = frame.merge(wpp, on=['country_id','year'], how='left', validate='one_to_one')
    return {y: frame[frame.year.eq(y)].set_index('country_id').reindex(ids)
            for y in range(2020, 2101, 5)}


def nan_fallback(a, b, fallback):
    return np.where(np.isfinite(a), a, np.where(np.isfinite(b), b, fallback))


class GeographyState:
    def __init__(self, anchors, current, lag5, lag10, wpp_by_year,
                 border, border_n, continent, continent_n, predictors):
        self.ids = anchors.country_id.astype(str).tolist()
        self.anchors = anchors
        self.shares = current.copy()
        self.lag5 = lag5.copy()
        self.lag10 = lag10.copy()
        self.wpp = wpp_by_year
        self.bmat, self.bn, self.cmat, self.cn = border, border_n, continent, continent_n
        self.predictors = predictors
        self.year = 2020
        self.dem = self.base_demographics()
        self.initial_pop = self.dem['wpp_population'].copy()
        self.dem2100 = None
        self.growth2100 = None

    def base_demographics(self):
        src = self.wpp[2020]
        a = self.anchors
        apop = pd.to_numeric(a.get('population_source', pd.Series(np.nan,index=a.index)),errors='coerce').to_numpy(float)
        pop = nan_fallback(src.wpp_population.to_numpy(float), apop, 1e6)
        pop = np.maximum(pop, 1.)
        return dict(tfr=nan_fallback(src.tfr.to_numpy(float), a.tfr.to_numpy(float), 2.1),
          median_age=nan_fallback(src.median_age.to_numpy(float), a.median_age.to_numpy(float), 30.),
          wpp_population=pop,
          net_migrations=nan_fallback(src.net_migrations.to_numpy(float), a.net_migrations.to_numpy(float), 0.),
          crude_net_migration_rate=nan_fallback(src.crude_net_migration_rate.to_numpy(float),
             a.crude_net_migration_rate.to_numpy(float), 0.))

    def clone(self):
        obj = object.__new__(GeographyState)
        obj.__dict__ = self.__dict__.copy()
        obj.shares = self.shares.copy(); obj.lag5 = self.lag5.copy(); obj.lag10 = self.lag10.copy()
        obj.dem = {k: v.copy() for k,v in self.dem.items()}
        obj.initial_pop = self.initial_pop.copy()
        obj.dem2100 = None; obj.growth2100 = None
        return obj

    def frame(self):
        base = {col: self.shares[:,j] for j,col in enumerate(SHARES)}
        for j,col in enumerate(SHARES):
            base['lag5_'+col] = self.lag5[:,j]
            base['lag10_'+col] = self.lag10[:,j]
            base['change5_'+col] = self.shares[:,j]-self.lag5[:,j]
            base['change10_'+col] = self.shares[:,j]-self.lag10[:,j]
        base.update(self.dem)
        base['log_population'] = np.log1p(np.maximum(self.dem['wpp_population'],0))
        for k in ('tfr','median_age','wpp_population','net_migrations','crude_net_migration_rate'):
            base['missing_'+k] = np.zeros(len(self.ids),dtype=int)
        bmean = np.asarray(self.bmat @ self.shares)
        cmean = np.asarray(self.cmat @ self.shares)
        for j,col in enumerate(SHARES):
            base['border_mean_'+col] = np.where(self.bn>0,bmean[:,j], np.nan)
            base['continent_mean_'+col] = np.where(self.cn>0,cmean[:,j], np.nan)
        base.update(border_mean_missing=(self.bn==0).astype(int),
                    continent_mean_missing=(self.cn==0).astype(int),
                    n_land_neighbors_observed=self.bn,
                    n_continent_peers_observed=self.cn)
        frame = pd.DataFrame(base)
        missing = set(self.predictors) - set(frame.columns)
        if missing: raise ValueError(f'Model expects missing feature columns: {sorted(missing)}')
        return frame[self.predictors]

    def update_demographics(self, end_year, fertility_mode, parameter):
        last = self.dem
        if end_year <= 2100:
            src = self.wpp[end_year]
            new = {}
            for k, default in [('tfr',2.1),('median_age',30.),('wpp_population',1e6),
                ('net_migrations',0.),('crude_net_migration_rate',0.)]:
                a = src[k].to_numpy(float)
                new[k] = nan_fallback(a,last[k],default)
            new['wpp_population'] = np.maximum(new['wpp_population'],1.)
            self.dem = new
            if end_year == 2100:
                self.dem2100 = {k:v.copy() for k,v in new.items()}
                oldpop = np.maximum(self.wpp[2095].wpp_population.to_numpy(float),1.)
                oldpop = nan_fallback(oldpop,np.maximum(self.dem['wpp_population'],1.),1.)
                self.growth2100 = np.clip(np.log(np.maximum(new['wpp_population'],1.)/oldpop)/5,-0.015,0.015)
            return
        if self.dem2100 is None:
            # Used only if caller incorrectly jumps beyond 2100 without simulating it.
            raise AssertionError('Must pass through UN 2100 before extrapolating')
        dt = end_year-2100
        t0 = self.dem2100['tfr']
        if fertility_mode=='converge':
            tfr = 2.1+(t0-2.1)*np.exp(-dt/140) + parameter['tfr_shift']*(1-np.exp(-dt/160))
        else:
            tfr = t0 + parameter['tfr_shift']*(1-np.exp(-dt/160))
        tfr = np.clip(tfr,0.9,4.5)
        target_age = np.clip(41 + 4*(2.1-tfr), 24, 57)
        age = np.clip(self.dem2100['median_age'] +
                      (target_age-self.dem2100['median_age'])*(1-np.exp(-dt/110)),18,62)
        # Stylized population continuation: 2100 growth fades and sensitivity
        # to fertility deviations also fades. No UN prediction beyond 2100.
        annual_log_growth = np.clip(self.growth2100*np.exp(-dt/60)
            +0.003*(tfr-2.1)*np.exp(-dt/120),-0.012,0.012)
        population = np.maximum(1., last['wpp_population']*np.exp(5*annual_log_growth))
        migrations = self.dem2100['net_migrations']*np.exp(-dt/65)
        self.dem = dict(tfr=tfr, median_age=age, wpp_population=population,
            net_migrations=migrations, crude_net_migration_rate=1000*migrations/population)

    def step(self, predicted_shares, next_year, fertility_mode, parameter):
        current=self.shares.copy()
        self.lag10=self.lag5.copy()
        self.lag5=current
        self.shares=np.asarray(predicted_shares,dtype=float).copy()
        validate_simplex(self.shares, f'{next_year} forecast')
        self.year=next_year
        self.update_demographics(next_year,fertility_mode,parameter)


def get_lgbm_prediction(state, estimator):
    base = state.shares
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='X does not have valid feature names', category=UserWarning)
        y=np.asarray(estimator.predict(state.frame()),dtype=float)
    if y.shape != base.shape: raise ValueError('LightGBM output shape wrong')
    return apply_clr_delta(base,y)


def transfer_to_unaffiliated(shares, annual_rate, years=5):
    # Pure assumption, not religious switching estimated by WPP.
    amount = 1-(1-np.clip(annual_rate,0,0.02))**years
    result=shares.copy()
    result[:,:-1] *= (1-amount)
    result[:,-1] = 1-result[:,:-1].sum(axis=1)
    return result


def model_weight(year, alpha):
    # Historical WRP model has poor long-horizon validation: disable by 2200.
    if year <= 2100: return alpha
    if year >= 2200: return 0.
    return alpha*(2200-year)/100.


def simulate(initial, estimator, resid, rng, fertility_mode, secular_mode,
             parameter, track, requested_years):
    state=initial.clone()
    record = {2020:(state.shares.copy(),state.dem['wpp_population'].copy())}
    # Build through 3030, then interpolate 3026 (NOT a measured one-year step).
    for year in range(2025,3031,5):
        base=state.shares
        if track=='persistence':
            proposed=base.copy()
        else:
            learn = track=='lightgbm' or (track=='scenario' and year<=2200)
            if learn:
                lgb=get_lgbm_prediction(state,estimator)
                alpha=1. if track=='lightgbm' else model_weight(year,parameter['alpha'])
                proposed=(1-alpha)*base+alpha*lgb
            else:
                proposed=base.copy()
            if track=='scenario':
                if year <= 2100 or secular_mode=='continues':
                    sec_rate=parameter['secular_annual']
                else:
                    sec_rate=parameter['secular_annual']*np.exp(-(year-2100)/25)
                proposed=transfer_to_unaffiliated(proposed,sec_rate)
                # Resample chronological out-of-fold WRP residuals as *assumed*
                # shocks. Dampen after 2100; never claim calibrated coverage.
                shock_scale = parameter['residual_scale'] * (1. if year<=2100 else np.exp(-(year-2100)/130))
                if shock_scale>1e-7:
                    ix = rng.integers(0,len(resid),size=len(base))
                    proposed = simplex_projection(proposed+shock_scale*resid[ix])
        state.step(proposed,year,fertility_mode,parameter)
        record[year]=(state.shares.copy(),state.dem['wpp_population'].copy())
    # The 3026 estimate is exactly 1/5 of the simulated 3025→3030 transition.
    s25,p25=record[3025]; s30,p30=record[3030]
    record[3026]=(0.8*s25+0.2*s30, np.exp(0.8*np.log(p25)+0.2*np.log(p30)))
    return {y:record[y] for y in requested_years}


def sample_parameters(rng, fertility_mode, secular_mode):
    return dict(alpha=float(rng.uniform(.05,.18)),
        secular_annual=float(rng.uniform(.00015,.0009)),
        tfr_shift=float(rng.normal(0,.13)),
        residual_scale=float(rng.uniform(.06,.22)))


def group_outputs(runs_shares, runs_pops, ids, scenarios, years):
    countries=[]; world=[]
    n_runs, n_years, n_countries, n_group=runs_shares.shape
    assert n_group==K
    for i,year in enumerate(years):
        sh=np.asarray(runs_shares[:,i],dtype=float)  # [run,country,8]
        pop=np.asarray(runs_pops[:,i],dtype=float)   # [run,country]
        dominant=sh.argmax(axis=2)
        agree=np.zeros((n_countries,K),dtype=float)
        for c in range(K): agree[:,c]=np.mean(dominant==c,axis=0)
        best=agree.argmax(axis=1)
        means=sh.mean(axis=0)
        quant=np.quantile(sh,[.05,.5,.95],axis=0)
        for j,cid in enumerate(ids):
            row={'country_id':cid,'year':year, 'most_likely_dominant':CATEGORIES[best[j]],
                 'dominant_agreement_fraction':float(agree[j,best[j]]),
                 'mean_population':float(pop[:,j].mean())}
            for c,cat in enumerate(CATEGORIES):
                row[f'mean_{cat}']=float(means[j,c])
                row[f'q05_{cat}']=float(quant[0,j,c])
                row[f'q50_{cat}']=float(quant[1,j,c])
                row[f'q95_{cat}']=float(quant[2,j,c])
            countries.append(row)
        # Average religion shares globally after weighting each country's shares
        # by its scenario-specific population; do not confuse with country means.
        denominator=pop.sum(axis=1)
        weighted = np.einsum('nc,nck->nk',pop,sh)/denominator[:,None]
        for r in range(n_runs):
            rec={'run':r,'year':year,'scenario':scenarios[r],
                 'covered_population':float(denominator[r])}
            rec.update({cat:float(weighted[r,j]) for j,cat in enumerate(CATEGORIES)})
            world.append(rec)
    return pd.DataFrame(countries),pd.DataFrame(world)


def write_global_uncertainty(world):
    rows=[]
    for year,g in world.groupby('year'):
        for cat in CATEGORIES:
            vals=g[cat].to_numpy(float)
            rows.append({'year':int(year),'religion':cat,'mean':float(vals.mean()),
               'q05':float(np.quantile(vals,.05)),'median':float(np.median(vals)),
               'q95':float(np.quantile(vals,.95))})
    return pd.DataFrame(rows)


def compare_pew_2050(global_uncertainty):
    g=global_uncertainty[global_uncertainty.year.eq(2050)].set_index('religion')
    out=[]
    for cat in CATEGORIES:
        model=100*float(g.loc[cat,'mean'])
        out.append({'religion':cat,'scenario_ensemble_2050_pct':model,
            'pew_2015_projection_2050_pct':PEW_2050_PCT[cat],
            'difference_pct_points':model-PEW_2050_PCT[cat],
            'comparison_note':'Different 2010/2020 Pew vintages and modeling assumptions; NOT independent validation'})
    return pd.DataFrame(out)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=int,default=120,
                   help='Total simulations, must be >=100 and divisible by four')
    p.add_argument('--seed',type=int,default=42)
    args=p.parse_args()
    if args.runs<100 or args.runs%4:
        p.error('--runs must be >=100 and divisible by 4 (balanced scenario grid)')
    OUT.mkdir(parents=True,exist_ok=True)
    anchors,cur,lag5,lag10,missing_2010,wpp,bundle,cols,resid,continents,neighbors=load_sources()
    ids=anchors.country_id.astype(str).tolist()
    mats=spatial_matrices(ids,continents,neighbors)
    wpp_years=wpp_arrays(ids,wpp)
    initial=GeographyState(anchors,cur,lag5,lag10,wpp_years,*mats,cols)
    rng=np.random.default_rng(args.seed)
    years=YEARS
    n=len(ids); m=len(years)
    # Memory-mapped arrays prevent storing all 120*203*201*8 values in RAM.
    share_file=OUT/'ensemble_shares_float32.npy'
    pop_file=OUT/'ensemble_populations_float32.npy'
    share_store=np.lib.format.open_memmap(share_file,mode='w+',dtype='float32',shape=(args.runs,m,n,K))
    pop_store=np.lib.format.open_memmap(pop_file,mode='w+',dtype='float32',shape=(args.runs,m,n))
    parameters=[]; scenario_labels=[]
    for i in range(args.runs):
        fertility,secular=SCENARIOS[i % len(SCENARIOS)]
        pars=sample_parameters(rng,fertility,secular)
        result=simulate(initial,bundle['estimator'],resid,rng,fertility,secular,
                        pars,'scenario',years)
        for ti,y in enumerate(years):
            sh,pp=result[y]
            share_store[i,ti]=sh.astype('float32')
            pop_store[i,ti]=pp.astype('float32')
        scenario_labels.append(f'{fertility}__{secular}')
        parameters.append({'run':i,'fertility_scenario':fertility,
            'secularization_scenario':secular,**pars})
        if (i+1)%20==0:print(f'  Completed {i+1}/{args.runs} scenario runs',flush=True)
    share_store.flush(); pop_store.flush()
    frame,world=group_outputs(share_store,pop_store,ids,scenario_labels,years)
    agg=write_global_uncertainty(world)
    sanity=compare_pew_2050(agg)
    frame.to_csv(OUT/'country_year_uncertainty.csv',index=False)
    world.to_csv(OUT/'global_share_by_run.csv',index=False)
    agg.to_csv(OUT/'global_share_uncertainty.csv',index=False)
    sanity.to_csv(OUT/'pew_2050_sanity_check.csv',index=False)
    pd.DataFrame(parameters).to_csv(OUT/'scenario_parameters.csv',index=False)
    # Deterministic benchmarks are separate tracks, not sampled probabilities.
    tracks=[]
    for track in ('persistence','lightgbm'):
        parameter=dict(alpha=1.,secular_annual=0.,tfr_shift=0.,residual_scale=0.)
        result=simulate(initial,bundle['estimator'],resid,rng,'persist','plateaus',
                        parameter,track,years)
        for y in years:
            sh,pp=result[y]
            for j,cid in enumerate(ids):
                row={'track':track,'year':y,'country_id':cid,'population':float(pp[j]),
                     'dominant':CATEGORIES[int(sh[j].argmax())]}
                row.update({cat:float(sh[j,k]) for k,cat in enumerate(CATEGORIES)})
                tracks.append(row)
    pd.DataFrame(tracks).to_csv(OUT/'deterministic_tracks.csv',index=False)
    report={
      'created_utc':datetime.now(timezone.utc).isoformat(),
      'ensemble_runs':args.runs,'rng_seed':args.seed,
      'religious_groups':CATEGORIES,'country_anchors':n,
      'forecast_anchor_year':2020,'wpp_used_through':2100,
      'forecast_output_years':years,'requested_map_years':TARGET_YEARS,
      'pew_2010_missing_baselines_initialized_from_2020':int(missing_2010.sum()),
      '2015_pew_share_initialization':'arithmetic midpoint of Pew 2010 and 2020, not observed',
      'model_source':'WRP 1945-2010, trained through Step 4 LightGBM',
      'simulation_scenarios':[{'fertility':f,'secularization':s,'runs':args.runs//4}
                              for f,s in SCENARIOS],
      'source_references':{'pew_2015_global_2050':PEW_PROJ_URL},
      'methodological_limits':[
        'No new historical evidence after Pew 2020; scenario ensembles are not calibrated predictive intervals.',
        'No religious-group-specific fertility, mortality, migration, or switching rates: TFR affects country population and model covariates, not religious fertility directly.',
        'One-step LightGBM was worse than persistence on WRP historical shares; ensemble trusts it only weakly and disables contribution by 2200.',
        'After 2100 fertility, age, migration, and population are rule-based scenario extrapolations, not UN data.',
        'Pew 2020 Other/Folk split was estimated using WRP as proxy for many countries.',
        'Countries missing WPP population use fallback 2020 Pew population with scenario behavior; check country coverage before interpreting global shares.',
        'Monte Carlo frequencies depend on four equally weighted scenario assumptions, not real-world probabilities.',
        'One-year 3026 estimate interpolates the 3025 and 3030 simulated states.',
        'Pew 2015 2050 projections are based on older religious estimates and population forecasts; sanity comparison is not external validation.',
        'Territories and political borders are held as in the 2020 country set.',
      ]}
    (OUT/'step5_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('\nSUCCESS: Step 5 scenario ensemble complete')
    print(f'Years: {years[0]}–{years[-1]} plus 3026 | Countries: {n} | Runs: {args.runs}')
    print('Pew 2050 comparison (percentage points):')
    print(sanity[['religion','scenario_ensemble_2050_pct','pew_2015_projection_2050_pct',
                 'difference_pct_points']].to_string(index=False,float_format=lambda x:f'{x:.2f}'))
    print('Outputs:',OUT)
    print('NEXT: run verify_step5.py. Maps will be drawn in Step 6.')

if __name__=='__main__':main()
