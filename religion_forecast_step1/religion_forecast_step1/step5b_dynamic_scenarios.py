"""Step 5B: sensitivity experiments for country religion shares, 2020--3026.

Run alongside Steps 3, 4, 5 and 6. Preserves ALL earlier Step 5 outputs.
Unlike Step 5's conservative simulations, four explicitly different mechanism
families are compared. The high-change cases are STRESS TESTS, not predictions.
No claim is made that national fertility measures religious-group fertility.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

import step5_forecast_scenarios as old

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'forecasts_step5b'
SCENARIOS = ('conservative', 'recent_momentum', 'differential_growth', 'structural_shocks')
YEARS = old.YEARS
CATEGORIES = old.CATEGORIES
K = len(CATEGORIES)


def close_simplex(x):
    # Use a small positive floor and renormalize; do not fabricate a new religion
    # when the original share is zero, except via the separate regional-mixing rule.
    x = np.maximum(np.asarray(x, dtype=float), 0.0)
    sums = x.sum(axis=1, keepdims=True)
    if (sums <= 0).any():
        raise ValueError('At least one simulated country has zero religion mass')
    return x / sums


def scenario_preparation(initial, current, decade, rng, continents):
    n = len(initial.ids)
    # Half of observed *ten-year* change is a five-year signal, capped so that
    # outliers or measurement breaks do not dominate the long-run simulation.
    delta10 = current - decade
    tv = 0.5*np.abs(delta10).sum(axis=1)
    scales = np.minimum(1, 0.12 / np.maximum(tv, 1e-12))
    momentum5 = 0.5 * delta10 * scales[:, None]
    # These relative-growth differences are hypothetical country/group-specific
    # sensitivities; they are NOT empirical fertility rates by religion.
    growth_advantage = rng.normal(0, 0.0025, size=(n, K))
    growth_advantage -= growth_advantage.mean(axis=1, keepdims=True)
    # Correlated shocks let a regional wave affect several countries at once.
    continent_labels = [continents.get(cid, 'Other') for cid in initial.ids]
    kinds = sorted(set(continent_labels))
    groups = np.array([kinds.index(c) for c in continent_labels], dtype=int)
    return momentum5, growth_advantage, groups, len(kinds)


def simulate_dynamic(initial, estimator, residuals, rng, scenario, pars,
                     current, decade, continents):
    state = initial.clone()
    momentum5, growth_adv, region_ids, num_regions = scenario_preparation(
        state, current, decade, rng, continents)
    n = len(state.ids)
    local_shock = np.zeros((n, K))
    regional_shock = np.zeros((num_regions, K))
    out = {2020: (state.shares.copy(), state.dem['wpp_population'].copy())}
    for year in range(2025, 3031, 5):
        base = state.shares.copy()
        if year <= 2200:
            learn = old.get_lgbm_prediction(state, estimator)
            alpha = old.model_weight(year, pars['alpha'])
            proposed = (1-alpha)*base + alpha*learn
        else:
            proposed = base.copy()

        # Country-specific *Pew-derived* 2010->2020 shift. It fades rather than
        # extrapolating a measured decade linearly for a thousand years.
        time_since_2020 = year - 2020
        halflife = {
            'recent_momentum': 35.,
            'differential_growth': 55.,
            'structural_shocks': 70.,
        }[scenario]
        decay = np.exp(-np.log(2)*time_since_2020/halflife)
        proposed += pars['momentum_multiplier']*momentum5*decay
        proposed = close_simplex(proposed)

        # Experiment-specific secularization: unlike original Step 5, these
        # paths taper toward zero by 2200. Momentum can point in either direction.
        sec_rate = pars['secular_annual']*np.exp(-max(year-2100,0)/100)
        proposed = old.transfer_to_unaffiliated(proposed, sec_rate)

        # Net inward migration is turned into a limited *proxy* for composition
        # mixing with peers on the same continent. Country-of-origin flows and
        # migrant faiths are unknown: do not interpret as empirically fitted.
        continent_mean = np.asarray(state.cmat @ base)
        pop = np.maximum(state.dem['wpp_population'],1.)
        flow = np.maximum(state.dem['net_migrations'],0.)
        weight = np.where(state.cn>0, np.clip(5*flow/pop, 0, 0.06),0.)
        proposed = (1-weight[:,None])*proposed + weight[:,None]*np.where(
            state.cn[:,None]>0,continent_mean,proposed)

        if scenario in ('differential_growth', 'structural_shocks'):
            # Multiplicative hypothetical group growth. Continues weakly beyond
            # 2100 for stress-testing; no religion-specific fertility data used.
            tfr_factor = np.clip(state.dem['tfr']/2.1, 0.6, 1.6)
            # 2100+ family differences are uncertain; attenuate, but do not force 0.
            attenuation = 1. if year <= 2100 else 0.28 + .72*np.exp(-(year-2100)/95)
            proposed *= np.exp(5*growth_adv*tfr_factor[:,None]*attenuation)
            proposed = close_simplex(proposed)

        if scenario == 'structural_shocks':
            # Temporally correlated, region-linked regime shifts. This explicitly
            # probes futures without an assumption that 2020 regimes stay fixed.
            # The shock intensity is hypothetical; not estimated from WRP.
            reg_draw = rng.normal(0,pars['regime_sd'],size=(num_regions,K))
            own_draw = rng.normal(0,pars['regime_sd'],size=(n,K))
            regional_shock = .76*regional_shock + np.sqrt(1-.76**2)*reg_draw
            local_shock = .70*local_shock + np.sqrt(1-.70**2)*own_draw
            total_shock = .60*regional_shock[region_ids] + .40*local_shock
            total_shock -= total_shock.mean(axis=1, keepdims=True)
            phase = .25 if year <= 2100 else 1.
            # Work in log shares so small groups are not disproportionately
            # clipped by adding the same number of percentage points everywhere.
            logits = np.log(np.maximum(proposed, 1e-8)) + phase * total_shock
            logits -= logits.max(axis=1,keepdims=True)
            proposed = close_simplex(np.exp(logits))

        # Near-term residual uncertainty; deliberately decays after 2100.
        shock_scale = pars['residual_scale']*(1. if year<=2100 else np.exp(-(year-2100)/130))
        if shock_scale > 1e-7:
            sampled = residuals[rng.integers(0,len(residuals),size=n)]
            proposed = old.simplex_projection(proposed+shock_scale*sampled)
        proposed = close_simplex(proposed)
        state.step(proposed, year, pars['fertility_mode'], pars)
        out[year]=(state.shares.copy(),state.dem['wpp_population'].copy())

    sh25,p25 = out[3025]; sh30,p30=out[3030]
    out[3026] = (0.8*sh25+0.2*sh30,np.exp(.8*np.log(p25)+.2*np.log(p30)))
    return out


def scenario_parameters(rng, scenario):
    out = old.sample_parameters(rng,'converge','continues')
    out['alpha'] = float(rng.uniform(.04,.13))
    out['secular_annual'] = float(rng.uniform(.00008,.00045))
    out['momentum_multiplier'] = float(rng.uniform(.6,1.15))
    out['regime_sd'] = float(rng.uniform(.025,.075)) if scenario == 'structural_shocks' else 0.
    out['fertility_mode'] = 'converge' if scenario in ('conservative','recent_momentum') else 'persist'
    return out


def scenario_summary(runs_share, ids, scenario_ids, years):
    labels=np.array(scenario_ids)
    rows=[]
    by_country=[]
    i0=years.index(2020)
    for sc in SCENARIOS:
        take=np.where(labels==sc)[0]
        for ti, year in enumerate(years):
            base=np.asarray(runs_share[take,i0],float).mean(axis=0)
            s=np.asarray(runs_share[take,ti],float)
            mean=s.mean(axis=0)
            base_dom=base.argmax(axis=1)
            modal=[]; agree=[]
            for j,cid in enumerate(ids):
                count=np.bincount(s[:,j,:].argmax(axis=1),minlength=K)
                m=int(count.argmax())
                modal.append(m)
                agree.append(float(count[m]/len(take)))
                if year in old.TARGET_YEARS:
                    by_country.append(dict(scenario=sc,country_id=cid,year=year,
                      most_likely_dominant=CATEGORIES[m],dominant_agreement_fraction=agree[-1],
                      **{f'mean_{cat}':float(mean[j,k]) for k,cat in enumerate(CATEGORIES)}))
            modal=np.asarray(modal,dtype=int)
            movement=.5*np.abs(mean-base).sum(axis=1)
            rows.append(dict(scenario=sc,year=year,countries=len(ids),
                countries_changed_dominant=int(np.sum(modal!=base_dom)),
                median_share_redistribution=float(np.median(movement)),
                mean_share_redistribution=float(np.mean(movement)),
                mean_scenario_agreement=float(np.mean(agree))))
    return pd.DataFrame(rows),pd.DataFrame(by_country)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs',type=int,default=120,help='Total runs, divisible by four, >=100')
    parser.add_argument('--seed',type=int,default=52)
    parser.add_argument('--test-small',action='store_true',help=argparse.SUPPRESS)
    a=parser.parse_args()
    if a.runs%4!=0 or (a.runs<100 and not a.test_small):parser.error('runs must be >=100 and divisible by 4')
    OUT.mkdir(exist_ok=True,parents=True)
    anchors,cur,lag5,decade,miss,wpp,bundle,predictors,resid,continents,neighbors=old.load_sources()
    ids=anchors.country_id.astype(str).tolist()
    mats=old.spatial_matrices(ids,continents,neighbors)
    initial=old.GeographyState(anchors,cur,lag5,decade,old.wpp_arrays(ids,wpp),*mats,predictors)
    rng=np.random.default_rng(a.seed)
    m=len(YEARS);n=len(ids)
    shares=np.lib.format.open_memmap(OUT/'ensemble_shares_float32.npy',mode='w+',dtype='float32',shape=(a.runs,m,n,K))
    pops=np.lib.format.open_memmap(OUT/'ensemble_populations_float32.npy',mode='w+',dtype='float32',shape=(a.runs,m,n))
    params=[]; labels=[]
    for run in range(a.runs):
        sc=SCENARIOS[run%len(SCENARIOS)]
        p=scenario_parameters(rng,sc)
        if sc=='conservative':
            res=old.simulate(initial,bundle['estimator'],resid,rng,p['fertility_mode'],
                'plateaus',p,'scenario',YEARS)
        else:
            res=simulate_dynamic(initial,bundle['estimator'],resid,rng,sc,p,cur,decade,continents)
        for i,yr in enumerate(YEARS):
            values,population=res[yr]
            shares[run,i]=values.astype('float32')
            pops[run,i]=population.astype('float32')
        labels.append(sc)
        params.append(dict(run=run,scenario=sc,**p))
        if (run+1)%20==0:print(f'Completed {run+1}/{a.runs} runs',flush=True)
    shares.flush();pops.flush()
    country,world=old.group_outputs(shares,pops,ids,labels,YEARS)
    global_unc=old.write_global_uncertainty(world)
    country.to_csv(OUT/'country_year_uncertainty.csv',index=False)
    world.to_csv(OUT/'global_share_by_run.csv',index=False)
    global_unc.to_csv(OUT/'global_share_uncertainty.csv',index=False)
    pd.DataFrame(params).to_csv(OUT/'scenario_parameters.csv',index=False)
    details,sc_country=scenario_summary(shares,ids,labels,YEARS)
    details.to_csv(OUT/'scenario_change_summary.csv',index=False)
    sc_country.to_csv(OUT/'scenario_country_maps.csv',index=False)
    report=dict(created_utc=datetime.now(timezone.utc).isoformat(),runs=a.runs,seed=a.seed,
      countries=n,years=YEARS,scenarios=list(SCENARIOS),
      methodology=[
       'Scenario families are assigned equal weight by design; frequencies are not statistical forecast probabilities.',
       'Pew 2010-to-2020 trend is damped over time and capped at 12 percentage points decade redistribution.',
       'Hypothetical religion-specific growth offsets and structural shocks are stress tests, not measured fertility or conversion rates.',
       'Demography through 2100 uses WPP2024 medium projections; after 2100 uses the original Step5 scenario assumptions.',
       'No independent validation of proposed high-change dynamics is possible after 2010/2020 with these data.',
       '3026 estimated by linear interpolation of simulated 3025/3030 religion shares.',
       'Model preserves original data/forecasts directory unchanged.',
       'Folk/Traditional vs Other split in Pew is partially proxy-derived.',
      ])
    (OUT/'step5b_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    short=details[details.year.isin(old.TARGET_YEARS)].copy()
    print('\nSTEP 5B — Changes by scenario (country count and median share redistribution)')
    print(short[['scenario','year','countries_changed_dominant','median_share_redistribution']].to_string(index=False,float_format=lambda x:f'{x:.1%}'))
    print(f'\nSaved separate outputs to {OUT}; Step 5 data were not overwritten.')

if __name__=='__main__': main()
