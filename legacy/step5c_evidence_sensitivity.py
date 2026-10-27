"""Step 5C: transparent Pew-momentum and demographic sensitivity experiments.

NOT a validated religious demographic forecast. The 2010-2020 Pew changes are
net changes, not direct measures of religious switching. The fertility and
migration mechanisms are explicitly hypothetical, not country estimates.
Existing Steps 5/5B remain untouched.

Run: .\\.venv\\Scripts\\python.exe step5c_evidence_sensitivity.py --runs 120 --seed 62
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import step5_forecast_scenarios as prior

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'forecasts_step5c'
SCENARIOS = (
    'persistence_benchmark',
    'pew_observed_momentum',
    'group_growth_sensitivity',
    'europe_migration_sensitivity',
)
YEARS = prior.YEARS
CATEGORIES = prior.CATEGORIES
K = len(CATEGORIES)
ISLAM = CATEGORIES.index('Islam')


def simplex(x):
    a = np.maximum(np.asarray(x, dtype=float), 0.0)
    return a / np.maximum(a.sum(axis=1, keepdims=True), 1e-14)


def momentum_from_pew(current, decade):
    """Net compositional movement per five years, capped at 10 pp TV per decade.

    Do NOT infer whether differences arose from births, deaths or switching.
    The Folk/Other split uses a proxy and is not independently Pew-observed.
    """
    m = current - decade
    # Folk & Other were not independently estimated by Pew: permit only the
    # *combined* difference, split in proportion to their 2020 shares.
    i, j = CATEGORIES.index('Folk_Traditional'), CATEGORIES.index('Other')
    combined = m[:, i] + m[:, j]
    weights = current[:, [i, j]] / np.maximum(current[:, [i, j]].sum(axis=1,keepdims=True), 1e-12)
    m[:, i] = combined * weights[:, 0]
    m[:, j] = combined * weights[:, 1]
    total_variation = 0.5 * np.abs(m).sum(axis=1)
    m = m * np.minimum(1.0, 0.10/np.maximum(total_variation,1e-12))[:,None]
    return .5 * m


def relative_growth_proxies():
    """Illustrative *global* fertility ordering, NOT within-country group TFR.

    Components are centered in simulation. Countries' national TFR is used
    only as a bounded scaling proxy; actual religious TFR by country is missing.
    Unknown categories have neutral offsets rather than invented fertility.
    """
    proxy = {
        'Christianity': .3, 'Islam': .7, 'Buddhism': -.8,
        'Unaffiliated': -.7,
    }
    return np.array([proxy.get(x, 0.) for x in CATEGORIES],float)


def scenario_params(rng, scenario):
    return dict(
        momentum_half_life=float(rng.uniform(25, 65)),
        momentum_strength=float(rng.uniform(.45,.9)),
        growth_strength=float(rng.uniform(.5,1.3)) if scenario=='group_growth_sensitivity' else 0.,
        # No evidence that this is the share of future migrants who will be Muslim:
        hypothetical_europe_arrival_muslim_share=float(rng.uniform(.25,.50))
            if scenario=='europe_migration_sensitivity' else None,
        residual_scale=float(rng.uniform(.025,.075)) if scenario!='persistence_benchmark' else 0.,
        tfr_shift=float(rng.normal(0,.13)),
        fertility_mode='converge',
    )


def simulate(initial, current, pew2010, residuals, rng, scenario, pars, continent_codes):
    state = initial.clone()
    movement5 = momentum_from_pew(current,pew2010)
    n = len(state.ids)
    growth = relative_growth_proxies()
    results = {2020:(state.shares.copy(),state.dem['wpp_population'].copy())}
    for year in range(2025,3031,5):
        base = state.shares.copy()
        change = np.zeros_like(base)
        if scenario != 'persistence_benchmark':
            years_elapsed = year - 2020
            decay = 2 ** (-years_elapsed / pars['momentum_half_life'])
            change = pars['momentum_strength'] * movement5 * decay
        proposed = simplex(base + change)

        if scenario == 'group_growth_sensitivity':
            # Hypothesis test for relative growth, not religious fertility data.
            # Damp after 2100 rather than extrapolate historic group gaps forever.
            fade = 1. if year <= 2100 else np.exp(-(year-2100)/75.)
            national_scale = np.clip(state.dem['tfr']/2.1, .7,1.4)
            logits = np.log(np.maximum(proposed,1e-12))
            logits += (0.015 * pars['growth_strength'] * fade * national_scale[:,None] * growth[None,:])
            proposed = simplex(np.exp(logits-logits.max(axis=1,keepdims=True)))

        if scenario == 'europe_migration_sensitivity' and year <= 2100:
            # Net UN migration lacks migrant origins/faith. This is an
            # intentional what-if assumption, Europe only, NOT estimated flows.
            is_europe = np.array([continent_codes.get(cid)=='Europe' for cid in state.ids])
            flow = np.maximum(state.dem['net_migrations'],0.)
            pop = np.maximum(state.dem['wpp_population'],1.)
            weight = np.where(is_europe,np.clip(5*flow/pop,0,.03),0.)
            continental_mean = np.asarray(state.cmat @ base)
            for j in np.where((weight>0)&(state.cn>0))[0]:
                target = continental_mean[j].copy()
                non_islam = target.copy(); non_islam[ISLAM]=0
                total = non_islam.sum()
                if total<=0:continue
                target = non_islam / total * (1-pars['hypothetical_europe_arrival_muslim_share'])
                target[ISLAM] = pars['hypothetical_europe_arrival_muslim_share']
                proposed[j]=(1-weight[j])*proposed[j] + weight[j]*target
            proposed = simplex(proposed)

        if scenario != 'persistence_benchmark':
            # Perturb within the compositional simplex. WRP residuals are not
            # calibrated predictive errors for 2020/3026; purely stress tests.
            decay_noise = 1. if year<=2100 else np.exp(-(year-2100)/80.)
            sampled = residuals[rng.integers(0,len(residuals),size=n)]
            proposed = simplex(np.maximum(proposed + pars['residual_scale']*decay_noise*sampled,0))

        state.step(proposed,year,pars['fertility_mode'],pars)
        results[year]=(state.shares.copy(),state.dem['wpp_population'].copy())
    s25,p25=results[3025]; s30,p30=results[3030]
    results[3026]=(.8*s25+.2*s30,np.exp(.8*np.log(p25)+.2*np.log(p30)))
    return results


def summarize_scenarios(shares, ids, labels, years):
    rows=[]; country_rows=[]
    labels=np.asarray(labels)
    i0=years.index(2020)
    for scenario in SCENARIOS:
        take=np.flatnonzero(labels==scenario)
        start=np.asarray(shares[take,i0],float).mean(axis=0)
        start_dom=start.argmax(axis=1)
        for t,year in enumerate(years):
            data=np.asarray(shares[take,t],float)
            means=data.mean(axis=0)
            predictions=data.argmax(axis=2)
            modal=[]
            for j,cid in enumerate(ids):
                freq=np.bincount(predictions[:,j],minlength=K)
                best=int(freq.argmax())
                modal.append(best)
                if year in prior.TARGET_YEARS:
                    country_rows.append({'scenario':scenario,'country_id':cid,'year':year,
                        'most_likely_dominant':CATEGORIES[best],
                        'dominant_agreement_fraction':float(freq[best]/len(take)),
                        **{f'mean_{c}':float(means[j,k]) for k,c in enumerate(CATEGORIES)}})
            tv=.5*np.abs(means-start).sum(axis=1)
            rows.append({'scenario':scenario,'year':year,'countries':len(ids),
                'countries_changed_dominant':int(np.sum(np.array(modal)!=start_dom)),
                'median_share_redistribution':float(np.median(tv)),
                'mean_share_redistribution':float(np.mean(tv))})
    return pd.DataFrame(rows),pd.DataFrame(country_rows)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=int,default=120)
    p.add_argument('--seed',type=int,default=62)
    p.add_argument('--test-small',action='store_true',help=argparse.SUPPRESS)
    args=p.parse_args()
    if args.runs%4 or (args.runs<100 and not args.test_small):
        p.error('Runs must be divisible by 4 and >=100')
    OUT.mkdir(exist_ok=True,parents=True)
    anchor,current,lag5,pew2010,missing,wpp,bundle,predictors,residuals,continents,neighbors=prior.load_sources()
    ids=anchor.country_id.astype(str).tolist()
    initial=prior.GeographyState(anchor,current,lag5,pew2010,prior.wpp_arrays(ids,wpp),
                                *prior.spatial_matrices(ids,continents,neighbors),predictors)
    rng=np.random.default_rng(args.seed)
    n,m=len(ids),len(YEARS)
    mem_sh=np.lib.format.open_memmap(OUT/'ensemble_shares_float32.npy',mode='w+',dtype='float32',shape=(args.runs,m,n,K))
    mem_pop=np.lib.format.open_memmap(OUT/'ensemble_populations_float32.npy',mode='w+',dtype='float32',shape=(args.runs,m,n))
    labels=[];params=[]
    for run in range(args.runs):
        sc=SCENARIOS[run%4]
        par=scenario_params(rng,sc)
        result=simulate(initial,current,pew2010,residuals,rng,sc,par,continents)
        for t,yr in enumerate(YEARS):
            s,pop=result[yr]
            mem_sh[run,t]=s.astype('float32');mem_pop[run,t]=pop.astype('float32')
        labels.append(sc)
        params.append({'run':run,'scenario':sc,**par})
        if (run+1)%20==0:print(f'Completed {run+1}/{args.runs} scenarios',flush=True)
    mem_sh.flush();mem_pop.flush()
    country,world=prior.group_outputs(mem_sh,mem_pop,ids,labels,YEARS)
    global_unc=prior.write_global_uncertainty(world)
    by_sc,sc_country=summarize_scenarios(mem_sh,ids,labels,YEARS)
    country.to_csv(OUT/'country_year_uncertainty.csv',index=False)
    world.to_csv(OUT/'global_share_by_run.csv',index=False)
    global_unc.to_csv(OUT/'global_share_uncertainty.csv',index=False)
    by_sc.to_csv(OUT/'scenario_change_summary.csv',index=False)
    sc_country.to_csv(OUT/'scenario_country_maps.csv',index=False)
    pd.DataFrame(params).to_csv(OUT/'scenario_parameters.csv',index=False)
    report={'generated_utc':datetime.now(timezone.utc).isoformat(),'runs':args.runs,
       'countries':n,'years':YEARS,'scenarios':SCENARIOS,
       'interpretation':'Sensitivity experiments, not statistically calibrated future outcome probabilities',
       'assumptions':[
           'Pew 2010->2020 observed net change, damped over 25-65 years, is NOT a directly measured switching rate.',
           'No universal forced secularization. The unaffiliated group can rise or fall with observed net changes.',
           'Pew Folk/Other separate values rely on proxies; their combined change is redistributed proportionally.',
           'Group growth differences based on illustrative global ordering, NOT observed within-country religion fertility.',
           'Europe migrant religion proportions are explicit what-if assumptions, NOT religious composition of UN migrants.',
           'Only UN country total population projections through 2100; 2100+ is hypothetical demography.',
           'Neither 2010/2020 Pew anchors nor old WRP model establish validated 2200-3026 results.',
           '3026 is an interpolation from 3025 and 3030 simulated shares.',
           'Original Steps 5 and 5B outputs remain unmodified.'
       ]}
    (OUT/'step5c_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('\nSTEP 5C — Country dominant-group transitions from 2020')
    chosen=by_sc[by_sc.year.isin([2050,2100,2200,2500,3026])]
    print(chosen[['scenario','year','countries_changed_dominant','median_share_redistribution']]
            .to_string(index=False,float_format=lambda x:f'{x:.1%}'))
    print(f'\nWrote Step 5C separately to {OUT}')

if __name__=='__main__':main()
