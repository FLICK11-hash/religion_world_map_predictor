"""Step 5D: religion-specific cohort-component forecast (fertility, age, migration, switching).

Run: .\\.venv\\Scripts\\python.exe step5d_cohort_forecast.py --runs 120 --seed 62

Replaces the arbitrary tilt in Step 5C with population mechanics: every country is
split into religious groups with their own age structure, fertility, migration share
and net switching (see step5d_engine.py and step5d_assumptions.json).
It is an exploratory model, NOT a validated forecast. Group fertility gaps and median
ages come from Pew GLOBAL figures damped to within-country values; no country x
religion fertility data are used. After 2100 national demography is the old stylised
rule from Step 5. Steps 5, 5B and 5C outputs are not touched.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import step5d_engine as eng

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'forecasts_step5d'
CATEGORIES = ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism',
              'Folk_Traditional', 'Other', 'Unaffiliated']
K = len(CATEGORIES)
SCENARIOS = ('demography_only', 'demography_plus_switching',
             'equal_fertility_counterfactual', 'no_migration_counterfactual')
YEARS = sorted(set(range(2020, 3031, 5)) | {3026})
HEADLINE = 'demography_plus_switching'
K = len(CATEGORIES)
TARGET_YEARS = [2020, 2050, 2100, 2200, 2500, 3026]
STEP_YEARS = list(range(2025, 3031, 5))
PEW_2050_PCT = {'Christianity': 31.4, 'Islam': 29.7, 'Hinduism': 14.9, 'Buddhism': 5.2,
                'Judaism': 0.2, 'Folk_Traditional': 4.8, 'Other': 0.7, 'Unaffiliated': 13.2}


def load_assumptions():
    a = json.loads((ROOT / 'step5d_assumptions.json').read_text(encoding='utf8'))
    rel = np.array([a['group_tfr_2010_15'][c] for c in CATEGORIES]) / a['world_tfr_2010_15']
    off = np.array([a['group_median_age_2010'][c] for c in CATEGORIES], float) - a['world_median_age_2010']
    return a, rel, off


def draw_params(rng, n, scenario, a):
    r = a['parameter_ranges']
    u = lambda k: float(rng.uniform(*r[k]['range']))
    return dict(phi=u('phi'), psi=u('psi'), w_add=u('w_add'), lam_nb=u('lam_nb'), lam_od=u('lam_od'), world_tfr=a['world_tfr_2010_15'], Hf=u('Hf'), e0=u('e0'), lam=u('lam'),
                switch_strength=u('switch_strength'), switch_half_life=u('switch_half_life'),
                tfr_shift=float(rng.normal(0, .13)),
                eps=rng.normal(0, r['eps_sd']['value'], size=(n, K)),
                equal_fertility=scenario == 'equal_fertility_counterfactual')


def hindcast_rho(inp, e, dems):
    """Net switching = Pew 2020 minus a no-switching demographic hindcast from Pew 2010."""
    h10, h15 = inp['dem_hist'][2010], inp['dem_hist'][2015]
    P = eng.initial_population(h10['wpp_population'], inp['pew2010'], h10['median_age'], e.median_offset)
    P, _ = e.step(P, h10, h15, -7.5)
    P, _ = e.step(P, h15, dems[2020], -2.5)
    pred = eng.shares_of(P)
    rho = eng.calibrate_switching(inp['current'], pred, CATEGORIES, valid=~inp['missing_2010'])
    return rho, pred


def simulate(inp, scenario, pars, rel_global, median_off):
    e = eng.Engine(rel_global, median_off, inp['cont'], pars, inp.get('adj'), inp.get('od'))
    dems = inp['dem_path'](pars['tfr_shift'])
    full = scenario == 'demography_plus_switching'
    rho = hindcast_rho(inp, e, dems)[0] if full else None
    P = eng.initial_population(dems[2020]['wpp_population'], inp['current'],
                               dems[2020]['median_age'], e.median_offset)
    out = {2020: (eng.shares_of(P), P.sum((1, 2)))}
    prev, drift = dems[2020], []
    n = len(inp['ids'])
    led = {k: np.zeros((n, K)) for k in ('out_2050', 'in_2050', 'out_2100', 'in_2100')}
    for year in STEP_YEARS:
        cur = dems[year]
        factor = .5 * pars['switch_strength'] * 2 ** (-(year - 2020) / pars['switch_half_life']) if full else 0.
        e.last_flows = None
        P, lg = e.step(P, prev, cur, year - 2022.5, rho, factor,
                       migration=scenario != 'no_migration_counterfactual')
        if year <= 2100:
            drift.append(float(lg.mean()))
        if e.last_flows is not None:
            outf, inf = e.last_flows
            for h in (2050, 2100):
                if year <= h:
                    led[f'out_{h}'] += outf
                    led[f'in_{h}'] += inf
        out[year] = (eng.shares_of(P), P.sum((1, 2)))
        prev = cur
    (s25, p25), (s30, p30) = out[3025], out[3030]
    out[3026] = (.8 * s25 + .2 * s30, np.exp(.8 * np.log(p25) + .2 * np.log(p30)))
    return out, float(np.mean(drift)), (None if rho is None else rho), led


# ------------------------------------------------------------------ real inputs
def wpp_slice(ids, wpp, year, fallback):
    f = wpp[wpp.year.eq(year)].set_index('country_id').reindex(ids)
    pick = lambda col, default: np.where(np.isfinite(f[col].to_numpy(float)),
                                         f[col].to_numpy(float), default)
    return dict(tfr=pick('tfr', fallback['tfr']), median_age=pick('median_age', fallback['median_age']),
                wpp_population=np.maximum(pick('wpp_population', fallback['wpp_population']), 1.),
                net_migrations=pick('net_migrations', 0.))


BILATERAL_FILE = ROOT / 'data' / 'raw' / 'migrant_bilateral.csv'


def load_bilateral(ids):
    """Optional bilateral migrant table: columns origin_iso3, dest_iso3, migrants (any positive
    measure, e.g. UN DESA International Migrant Stock 2020 or World Bank bilateral migrants).
    Returns a row-normalised [dest, origin] matrix over `ids` and a coverage report, or (None, {})."""
    if not BILATERAL_FILE.exists():
        return None, {}
    df = pd.read_csv(BILATERAL_FILE, dtype=str)
    need = {'origin_iso3', 'dest_iso3', 'migrants'}
    if not need.issubset(df.columns):
        raise ValueError(f'{BILATERAL_FILE.name} needs columns {sorted(need)}')
    df['migrants'] = pd.to_numeric(df['migrants'].str.replace(',', ''), errors='coerce')
    df = df.dropna(subset=['migrants'])
    df = df[df.migrants > 0]
    index = {cid: i for i, cid in enumerate(ids)}
    df = df[df.origin_iso3.isin(index) & df.dest_iso3.isin(index)]
    mat = np.zeros((len(ids), len(ids)))
    np.add.at(mat, (df.dest_iso3.map(index).to_numpy(), df.origin_iso3.map(index).to_numpy()),
              df.migrants.to_numpy(float))
    rows = mat.sum(1)
    od = mat / np.maximum(rows[:, None], 1e-300)
    report = {'file': BILATERAL_FILE.name, 'pairs_used': int(len(df)),
              'destinations_with_bilateral_data': int((rows > 0).sum()),
              'destinations_total': len(ids)}
    return od, report


def migration_table(mig_sum, ids, runs_headline):
    """Persons moving in and out by country and religion, mean over headline runs."""
    rows = []
    for period, h in (('2020-2050', 2050), ('2020-2100', 2100)):
        inflow = mig_sum[f'in_{h}'] / runs_headline
        outflow = mig_sum[f'out_{h}'] / runs_headline
        for j, cid in enumerate(ids):
            for k, cat in enumerate(CATEGORIES):
                rows.append({'period': period, 'country_id': cid, 'religion': cat,
                             'inflow_persons': float(inflow[j, k]), 'outflow_persons': float(outflow[j, k]),
                             'net_persons': float(inflow[j, k] - outflow[j, k])})
    return pd.DataFrame(rows)


def load_inputs():
    import step5_forecast_scenarios as prior
    anchor, current, lag5, pew2010, missing, wpp, bundle, predictors, resid, continents, neighbors = \
        prior.load_sources()
    ids = anchor.country_id.astype(str).tolist()
    by_year = prior.wpp_arrays(ids, wpp)
    border, border_n, continent, continent_n = prior.spatial_matrices(ids, continents, neighbors)
    initial = prior.GeographyState(anchor, current, lag5, pew2010, by_year,
                                   border, border_n, continent, continent_n, predictors)
    adj = (np.asarray(border.todense()) > 0).astype(float)
    base = initial.dem
    wpp_missing_2020 = int(by_year[2020][['wpp_population', 'tfr']].isna().any(axis=1).sum())
    names = sorted({v for v in continents.values() if isinstance(v, str)})
    cont = np.array([names.index(continents[c]) if isinstance(continents.get(c), str) else -1
                     for c in ids])

    def dem_path(tfr_shift):
        state = initial.clone()
        path = {2020: {k: v.copy() for k, v in state.dem.items()}}
        for year in STEP_YEARS:
            state.update_demographics(year, 'converge', {'tfr_shift': tfr_shift})
            path[year] = {k: v.copy() for k, v in state.dem.items()}
        return path

    od, od_report = load_bilateral(ids)
    return dict(ids=ids, current=current, pew2010=pew2010, missing_2010=np.asarray(missing, bool),
                cont=cont, adj=adj, od=od, od_report=od_report, dem_path=dem_path,
                dem_hist={y: wpp_slice(ids, wpp, y, base) for y in (2010, 2015)},
                wpp_missing_2020=wpp_missing_2020, missing_2010_n=int(np.sum(missing)))


# ------------------------------------------------------------------ summaries
def summarize(shares, pops, ids, labels, years):
    import step5_forecast_scenarios as prior
    labels = np.asarray(labels)
    i0 = years.index(2020)
    rows, country_rows, country_all, world_all = [], [], [], []
    for sc in SCENARIOS:
        take = np.flatnonzero(labels == sc)
        c, w = prior.group_outputs(shares[take], pops[take], ids, [sc] * len(take), years)
        c.insert(0, 'scenario', sc)
        w['scenario'] = sc
        country_all.append(c); world_all.append(w)
        start_dom = np.asarray(shares[take, i0], float).mean(0).argmax(1)
        start = np.asarray(shares[take, i0], float).mean(0)
        for t, year in enumerate(years):
            data = np.asarray(shares[take, t], float)
            means = data.mean(0)
            pred = data.argmax(2)
            modal = np.array([np.bincount(pred[:, j], minlength=K).argmax() for j in range(len(ids))])
            mean_dom = means.argmax(1)
            tv = .5 * np.abs(means - start).sum(1)
            rows.append({'scenario': sc, 'year': year, 'countries': len(ids),
                         'countries_changed_dominant': int((modal != start_dom).sum()),
                         'countries_changed_dominant_by_mean': int((mean_dom != start_dom).sum()),
                         'median_share_redistribution': float(np.median(tv)),
                         'mean_share_redistribution': float(tv.mean())})
            if year in TARGET_YEARS:
                for j, cid in enumerate(ids):
                    freq = np.bincount(pred[:, j], minlength=K)
                    country_rows.append({'scenario': sc, 'country_id': cid, 'year': year,
                                         'most_likely_dominant': CATEGORIES[int(modal[j])],
                                         'mean_dominant': CATEGORIES[int(mean_dom[j])],
                                         'dominant_agreement_fraction': float(freq[modal[j]] / len(take)),
                                         **{f'mean_{k}': float(means[j, m]) for m, k in enumerate(CATEGORIES)}})
    return (pd.DataFrame(rows), pd.DataFrame(country_rows),
            pd.concat(country_all, ignore_index=True), pd.concat(world_all, ignore_index=True))


def global_vs_pew2050(world):
    g = world[world.year.eq(2050)].groupby('scenario')[CATEGORIES].mean() * 100
    g.loc['Pew 2015 projection'] = pd.Series(PEW_2050_PCT)
    return g.round(2).reset_index().rename(columns={'index': 'scenario'})


def central_diagnostics(inp, a, rel, off):
    """One run at the midpoint of every range: how well does demography alone explain Pew 2010-2020?"""
    r = a['parameter_ranges']
    mid = lambda k: float(np.mean(r[k]['range']))
    pars = dict(phi=mid('phi'), psi=mid('psi'), w_add=mid('w_add'), lam_nb=mid('lam_nb'), world_tfr=a['world_tfr_2010_15'], Hf=mid('Hf'), e0=mid('e0'), lam=mid('lam'),
                switch_strength=mid('switch_strength'), switch_half_life=mid('switch_half_life'),
                tfr_shift=0., eps=None, equal_fertility=False)
    e = eng.Engine(rel, off, inp['cont'], pars, inp.get('adj'), inp.get('od'))
    dems = inp['dem_path'](0.)
    rho, pred = hindcast_rho(inp, e, dems)
    pop20 = dems[2020]['wpp_population']
    w = lambda s: (s * pop20[:, None]).sum(0) / pop20.sum()
    ok = ~inp['missing_2010']
    rows = [{'religion': c,
             'global_share_pew2010': float(w(inp['pew2010'])[j]),
             'global_share_pew2020': float(w(inp['current'])[j]),
             'global_share_demography_only_2020': float(w(pred)[j]),
             'persistence_error_pp': 100 * float(w(inp['pew2010'])[j] - w(inp['current'])[j]),
             'demography_only_error_pp': 100 * float(w(pred)[j] - w(inp['current'])[j]),
             'country_mean_abs_unexplained_pp': 100 * float(np.abs(inp['current'] - pred)[ok, j].mean()),
             'country_mean_abs_pew_change_pp': 100 * float(np.abs(inp['current'] - inp['pew2010'])[ok, j].mean()),
             'countries_where_demography_gets_sign_right': float(np.mean(
                 np.sign(pred[ok, j] - inp['pew2010'][ok, j]) == np.sign(inp['current'][ok, j] - inp['pew2010'][ok, j])))}
            for j, c in enumerate(CATEGORIES)]
    return pd.DataFrame(rows)


def phi_scan(inp, a, rel, off, grid=None):
    """Does the 2010->2020 hindcast prefer a particular within-country fertility gap (phi)?
    Error = total variation between hindcast and Pew 2020 shares, averaged over countries
    that have a Pew 2010 baseline. phi=0 means no within-country fertility differences."""
    grid = np.linspace(0, 1, 11) if grid is None else grid
    r = a['parameter_ranges']
    mid = lambda k: float(np.mean(r[k]['range']))
    dems = inp['dem_path'](0.)
    ok = ~inp['missing_2010']
    pop20 = dems[2020]['wpp_population']
    base = 0.5 * np.abs(inp['current'] - inp['pew2010']).sum(1)
    rows = []
    for phi in grid:
        pars = dict(phi=float(phi), psi=mid('psi'), w_add=mid('w_add'), lam_nb=mid('lam_nb'), world_tfr=a['world_tfr_2010_15'], Hf=mid('Hf'), e0=mid('e0'), lam=mid('lam'),
                    switch_strength=1., switch_half_life=60., tfr_shift=0., eps=None, equal_fertility=False)
        e = eng.Engine(rel, off, inp['cont'], pars, inp.get('adj'), inp.get('od'))
        pred = hindcast_rho(inp, e, dems)[1]
        tv = 0.5 * np.abs(inp['current'] - pred).sum(1)
        rows.append({'phi': float(phi), 'mean_country_tv_pp': 100 * float(tv[ok].mean()),
                     'pop_weighted_tv_pp': 100 * float((tv[ok] * pop20[ok]).sum() / pop20[ok].sum()),
                     'persistence_mean_country_tv_pp': 100 * float(base[ok].mean()),
                     'persistence_pop_weighted_tv_pp': 100 * float((base[ok] * pop20[ok]).sum() / pop20[ok].sum())})
    return pd.DataFrame(rows)


def calibrated_phi_range(scan, half_width=0.15):
    """Narrow the sampled phi range around the hindcast-best value (optional, --calibrate-phi)."""
    best = float(scan.loc[scan.mean_country_tv_pp.idxmin(), 'phi'])
    return best, [max(0.0, best - half_width), min(1.0, best + half_width)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs', type=int, default=120)
    p.add_argument('--seed', type=int, default=62)
    p.add_argument('--calibrate-phi', action='store_true',
                   help='sample phi around the value that best reproduces Pew 2010->2020 (risk: overfits one decade)')
    p.add_argument('--test-small', action='store_true', help=argparse.SUPPRESS)
    args = p.parse_args()
    if args.runs % 4 or (args.runs < 100 and not args.test_small):
        p.error('Runs must be divisible by 4 and >=100')
    OUT.mkdir(exist_ok=True, parents=True)
    a, rel, off = load_assumptions()
    inp = load_inputs()
    ids, n, m = inp['ids'], len(inp['ids']), len(YEARS)
    phi_note = None
    if args.calibrate_phi:
        best, rng_phi = calibrated_phi_range(phi_scan(inp, a, rel, off, grid=np.linspace(0, 1, 21)))
        a['parameter_ranges']['phi']['range'] = rng_phi
        phi_note = {'hindcast_best_phi': best, 'sampled_range': rng_phi}
        print(f'Calibrated phi: best {best:.2f}, sampling {rng_phi}')
    rng = np.random.default_rng(args.seed)
    sh = np.lib.format.open_memmap(OUT / 'ensemble_shares_float32.npy', mode='w+', dtype='float32', shape=(args.runs, m, n, K))
    pp = np.lib.format.open_memmap(OUT / 'ensemble_populations_float32.npy', mode='w+', dtype='float32', shape=(args.runs, m, n))
    labels, params = [], []
    mig_sum = {k: np.zeros((n, K)) for k in ('out_2050', 'in_2050', 'out_2100', 'in_2100')}
    for run in range(args.runs):
        sc = SCENARIOS[run % 4]
        par = draw_params(rng, n, sc, a)
        res, drift, _, led = simulate(inp, sc, par, rel, off)
        if sc == HEADLINE:
            for key in mig_sum:
                mig_sum[key] += led[key]
        for t, yr in enumerate(YEARS):
            sh[run, t] = res[yr][0].astype('float32'); pp[run, t] = res[yr][1].astype('float32')
        labels.append(sc)
        params.append({'run': run, 'scenario': sc, 'mean_abs_log_rescale_to_2100': drift,
                       **{k: v for k, v in par.items() if k != 'eps'}})
        if (run + 1) % 20 == 0:
            print(f'Completed {run + 1}/{args.runs} runs', flush=True)
    sh.flush(); pp.flush()
    by_sc, sc_country, country, world = summarize(sh, pp, ids, labels, YEARS)
    import step5_forecast_scenarios as prior
    # Step 6 map code expects ONE row per country-year, so the standard file names hold the
    # headline scenario only; every scenario is kept in the *_by_scenario files.
    head = country.scenario.eq(HEADLINE)
    country[head].drop(columns='scenario').to_csv(OUT / 'country_year_uncertainty.csv', index=False)
    country.to_csv(OUT / 'country_year_uncertainty_by_scenario.csv', index=False)
    prior.write_global_uncertainty(world[world.scenario.eq(HEADLINE)].drop(columns='scenario')) \
        .to_csv(OUT / 'global_share_uncertainty.csv', index=False)
    pd.concat([prior.write_global_uncertainty(g.drop(columns='scenario')).assign(scenario=sc)
               for sc, g in world.groupby('scenario')]).to_csv(
        OUT / 'global_share_uncertainty_by_scenario.csv', index=False)
    by_sc.to_csv(OUT / 'scenario_change_summary.csv', index=False)
    sc_country.to_csv(OUT / 'scenario_country_maps.csv', index=False)
    world.to_csv(OUT / 'global_share_by_run.csv', index=False)
    pd.DataFrame(params).to_csv(OUT / 'scenario_parameters.csv', index=False)
    migration_table(mig_sum, ids, args.runs // 4).to_csv(OUT / 'migration_by_religion.csv', index=False)
    diag = central_diagnostics(inp, a, rel, off)
    diag.to_csv(OUT / 'hindcast_diagnostics.csv', index=False)
    scan = phi_scan(inp, a, rel, off)
    scan.to_csv(OUT / 'hindcast_phi_scan.csv', index=False)
    cmp50 = global_vs_pew2050(world)
    cmp50.to_csv(OUT / 'global_vs_pew2015_2050.csv', index=False)
    report = {'generated_utc': datetime.now(timezone.utc).isoformat(), 'runs': args.runs, 'countries': n,
              'years': YEARS, 'scenarios': SCENARIOS, 'headline_scenario': HEADLINE,
              'countries_with_wpp_defaults_2020': inp['wpp_missing_2020'],
              'countries_without_pew_2010_baseline_zero_switching': inp['missing_2010_n'],
              'assumptions_file': 'step5d_assumptions.json', 'phi_calibration': phi_note,
              'bilateral_migration': inp['od_report'] or 'none (neighbour/continent/world pools only)', 'assumptions_status': a['status'],
              'interpretation': 'Exploratory mechanism model, not a validated forecast and not outcome probabilities',
              'assumptions': [
                  'Group fertility = national WPP TFR x (Pew global ratio damped to a within-country gap, blended additive/multiplicative by w_add), gaps converge, national aggregate TFR equals WPP.',
                  'One life table for all groups; each country rescaled to WPP (to 2100) or rule-based totals every step.',
                  'Leavers carry their origin country\'s adult religious mix. Arrivals take the religious mix of their origin countries when a bilateral migrant table is supplied (lam_od), otherwise a pool of land neighbours, same continent and world. WPP net migration sets how many move; the bilateral table only sets who arrives.',
                  'Net switching = Pew 2020 minus a no-switching 2010-2020 hindcast (absorbs all model and measurement error), capped at 10 pp/decade, decaying.',
                  'Folk/Other split is a proxy; their combined residual is split by 2020 shares.',
                  'After 2100 national demography is the Step 5 stylised rule; 3026 interpolates 3025 and 3030.',
                  'Counterfactual scenarios (equal fertility, no migration) isolate each mechanism; they are not forecasts.']}
    (OUT / 'step5d_report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print('\nSTEP 5D - hindcast: how much of Pew 2010->2020 does demography alone explain?')
    print(diag.round(3).to_string(index=False))
    print('\nHindcast fit by within-country fertility-gap fraction phi (lower is better; sampled range 0.3-0.7)')
    print(scan.round(3).to_string(index=False))
    print('\nGlobal 2050 shares (%) vs Pew 2015 projection')
    print(cmp50.to_string(index=False))
    print('\nCountries whose dominant group changes (modal), selected years')
    print(by_sc[by_sc.year.isin([2050, 2100, 2200, 3026])][['scenario', 'year', 'countries_changed_dominant']]
          .to_string(index=False))
    print(f'\nWrote Step 5D separately to {OUT}')


if __name__ == '__main__':
    main()
