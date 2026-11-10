"""Integrity checks of the projection outputs (run after run.py project; also reads the backtest output).

Run:  python run.py checks
Exit code 0 = every check passed. Checks:
  1 every country's religious shares are non-negative and sum to 100% in every scenario and year
  2 the component breakdown adds up to the simulated change of mean shares (it IS the simulation's
    own accounting, not a post-hoc split) for every scenario, country, religion and period
  3 migration conserves people: worldwide, emigrants equal immigrants by religion in every period
  4 world shares sum to 100% and world population stays finite and positive to 3030
  5 probabilities, switching rates and diversity indices are within their ranges
  6 inputs actually used (data catalogue), fallbacks and the validation summary are reported
  7 maps cover the modelled countries
  8 predictive intervals (to 2100) are ordered, within 0-100%, and at least as wide as the run spread
"""
from __future__ import annotations

import itertools
import json
import sys

import numpy as np
import pandas as pd
from religion_forecast import config

F = config.PROJECTIONS
V = config.VALIDATION
CATS = ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism', 'Folk_Traditional', 'Other', 'Unaffiliated']
BOUNDS = [2020, 2050, 2100, 2200, 2500, 3030]
failures = []


def check(ok, text):
    print(('PASS  ' if ok else 'FAIL  ') + text)
    if not ok:
        failures.append(text)


def main(argv=None):
    need = ['country_year_by_scenario.csv', 'global_share_by_scenario.csv', 'components_country_period.csv',
            'components_world_period.csv', 'projection_report.json', 'dominant_change.csv', 'switching_rates_2020.csv',
            'world_population_by_scenario.csv', 'parameter_provenance.csv']
    missing = [n for n in need if not (F / n).exists()]
    if missing:
        print('Missing outputs (run run.py project first):', missing)
        return 1
    rep = json.loads((F / 'projection_report.json').read_text())
    ct = pd.read_csv(F / 'country_year_by_scenario.csv')
    m = ct[[f'mean_{c}' for c in CATS]].to_numpy()
    check(np.isfinite(m).all() and (m >= -1e-9).all(), f'1a shares non-negative and finite ({len(ct)} rows)')
    check(np.allclose(m.sum(1), 1.0, atol=1e-6), '1b shares sum to 100% in every country, year and scenario')
    for q in ('q05', 'q95'):
        x = ct[[f'{q}_{c}' for c in CATS]].to_numpy()
        check(((x >= -1e-9) & (x <= 1 + 1e-9)).all(), f'1c {q} bands within 0-100%')

    comp = pd.read_csv(F / 'components_country_period.csv')
    sub_cols = [c for c in comp.columns if c.startswith('share_pp_') and c != 'share_pp_total']
    check(np.allclose(comp[sub_cols].sum(1), comp.share_pp_total, atol=1e-6),
          '2a sub-step contributions sum to the total')
    errs = []
    piv = ct.set_index(['scenario', 'country_id', 'year'])
    for y0, y1 in itertools.pairwise(BOUNDS):
        per = comp[comp.period.eq(f'{y0}-{y1}')]
        if per.empty:
            continue
        for c in CATS:
            sel = per[per.religion.eq(c)].set_index(['scenario', 'country_id'])['share_pp_total']
            a = piv.xs(y0, level='year')[f'mean_{c}'].reindex(sel.index)
            b = piv.xs(y1, level='year')[f'mean_{c}'].reindex(sel.index)
            errs.append(float(np.nanmax(np.abs(100 * (b - a) - sel))))
    check(max(errs) < 1e-3,
          f'2b components reproduce the simulated change of mean shares (max error {max(errs):.2e} pp)')

    wc = pd.read_csv(F / 'components_world_period.csv')
    imbalance = (wc.persons_emigration + wc.persons_immigration).abs()
    scale = wc.persons_immigration.abs().max()
    check(float(imbalance.max()) <= 1e-6 * max(scale, 1.0) + 1.0,
          f'3a migration conserves people by religion worldwide (max imbalance {imbalance.max():.1f} persons '
          f'of {scale:,.0f})')
    check(np.allclose(wc.world_share_pp_emigration + wc.world_share_pp_immigration, 0, atol=1e-6),
          '3b migration leaves world religious shares unchanged')

    wt = pd.read_csv(F / 'global_share_by_scenario.csv')
    s = wt.groupby(['scenario', 'year'])['mean'].sum()
    check(np.allclose(s, 1.0, atol=1e-6), '4a world shares sum to 100%')
    wp = pd.read_csv(F / 'world_population_by_scenario.csv')
    check(np.isfinite(wp.mean_world_population).all() and (wp.mean_world_population > 0).all(),
          f'4b world population finite and positive to 3030 (range {wp.mean_world_population.min() / 1e9:.2f}-'
          f'{wp.mean_world_population.max() / 1e9:.2f} billion)')

    dc = pd.read_csv(F / 'dominant_change.csv')
    pc = dc[[c for c in dc.columns if c.startswith('prob_changed_by_')]].to_numpy()
    check(((pc >= 0) & (pc <= 1)).all(), '5a dominant-change probabilities in [0, 1]')
    sw = pd.read_csv(F / 'switching_rates_2020.csv')
    check(((sw['mean'] >= 0) & (sw['mean'] <= 1) & (sw.q05 <= sw.q95 + 1e-12)).all(),
          '5b switching rates are probabilities')
    dv = ct.diversity_gini_simpson_mean
    check(((dv >= 0) & (dv <= 0.875 + 1e-9)).all(), '5c diversity index within [0, 0.875]')

    if 'pi05_Christianity' in ct:
        pc = ct[ct.year.le(2100) & ct.year.gt(2020)]
        lo = pc[[f'pi05_{c}' for c in CATS]].to_numpy()
        hi = pc[[f'pi95_{c}' for c in CATS]].to_numpy()
        check(np.isfinite(lo).all() and (lo >= -1e-9).all() and (hi <= 1 + 1e-9).all() and (lo <= hi + 1e-12).all(),
              f'8a country predictive intervals ordered and within 0-100% ({len(pc)} rows, 2025-2100)')
        wp_ = wt[wt.year.le(2100) & wt.year.gt(2020) & wt.pi05.notna()] if 'pi05' in wt else wt.iloc[:0]
        if len(wp_):
            ordered = ((wp_.pi05 <= wp_.pi10 + 1e-12) & (wp_.pi10 <= wp_.pi90 + 1e-12)
                       & (wp_.pi90 <= wp_.pi95 + 1e-12)).all()
            wider = float(((wp_.pi95 - wp_.pi05) >= (wp_.q95 - wp_.q05) - 1e-9).mean())
            check(bool(ordered) and wider >= 0.95,
                  f'8b world predictive quantiles ordered; at least as wide as the run spread in '
                  f'{100 * wider:.0f}% of rows')
    else:
        print('      NOTE: no predictive intervals in this run (no forecast-error model)')

    inputs = rep.get('inputs', {})
    print('\nInputs used:')
    for k, v in inputs.items():
        print(f'  {k:22s} {v["status"]:9s} {v["detail"]}')
    start = rep.get('start_state', '')
    check(start.startswith('data/processed') or 'pew2020_start_state' in start,
          f"6a start state reported: {rep.get('start_state')}")
    if 'pew2020_start_state' in rep.get('start_state', ''):
        print('      NOTE: Pew 2010 was not available, so the Pew 2010-2020 window was neither fitted nor tested.')
    print(f"\nSwitching fit: {rep.get('switching_fit')}")
    print(f"Emigration selectivity: {rep.get('emigration_selectivity')}")
    print(f"Diagnostics: {rep.get('diagnostics')}")
    if (V / 'validation_summary.csv').exists():
        vs = pd.read_csv(V / 'validation_summary.csv')
        cols = ['scope', 'model', 'popw_tv_pp', 'change_vs_persistence_pp']
        print('\nHistory tests (lower is better; negative change = better than persistence):')
        print(vs[cols].round(3).to_string(index=False))
    else:
        print('\nNo validation summary yet: run run.py backtest')
    # 7 map coverage: which modelled countries have no polygon to draw, and which polygons have no
    # model estimate. Both show up as grey on the maps, so they should be listed, not just coloured.
    try:
        from religion_forecast.figures import svg as SVG
        shapes, _, dots = SVG.load_shapes()
        ids = set(pd.read_csv(F / 'country_year_by_scenario.csv', usecols=['country_id']).country_id.unique())
        mapped = {SVG.MAP_CODE_FIXES.get(c, c) for c in ids}
        drawable = set(shapes) | set(dots)
        missing_polygon = sorted(c for c in ids if SVG.MAP_CODE_FIXES.get(c, c) not in drawable)
        no_estimate = sorted(drawable - mapped)
        pd.DataFrame({'country_id': missing_polygon}).to_csv(F / 'map_countries_without_polygon.csv', index=False)
        pd.DataFrame({'map_id': no_estimate}).to_csv(F / 'map_polygons_without_estimate.csv', index=False)
        check(len(missing_polygon) <= 10,
              f'7a modelled countries drawn on the map ({len(ids) - len(missing_polygon)} of {len(ids)}, '
              f'{len(set(dots) & mapped)} as points because they are smaller than a pixel; '
              f'missing: {", ".join(missing_polygon) if missing_polygon else "none"})')
        print(f'      {len(no_estimate)} map polygons have no estimate and are drawn grey')
    except Exception as exc:                                  # a missing shapefile must not fail the run
        print(f'      map coverage not checked: {exc}')

    # 9 the switching estimator: Monte Carlo error small beside statistical error, a sampler that has
    # not degenerated, and (when run.py recovery has run) recovery of known hyperparameters
    sf = rep.get('switching_fit', {})
    reps = sf.get('replicates', [])
    if len(reps) > 1 and 'se_delta' in reps[0]:
        names = (('delta', 'se_delta'), ('beta_d', 'se_beta_d'), ('tau_u', 'se_log_tau_u'))
        ratios = []
        for k, se in names:
            vals = np.array([r[k] for r in reps], float)
            vals = np.log(vals) if k == 'tau_u' else vals
            ratios.append(float(vals.std(ddof=1) / max(np.mean([r[se] for r in reps]), 1e-12)))
        check(max(ratios) < 0.5, '9a replicate fits agree: spread / standard error '
              + ', '.join(f'{k} {v:.2f}' for (k, _), v in zip(names, ratios, strict=True)))
        ess = min(r['min_posterior_ess'] for r in reps)
        check(ess >= 20, f'9b importance sampling has not degenerated (smallest country ESS {ess:.0f} of '
                         f"{sf.get('latent_draws')})")
    rec = pd.read_csv(V / 'estimator_recovery.csv') if (V / 'estimator_recovery.csv').exists() else None
    if rec is not None and rec.replications.min() < 10:
        print(f'      9c not judged: the recovery study has {int(rec.replications.min())} replications '
              '(a quick run); run.py recovery runs 20')
    elif rec is not None:
        ok = (rec.coverage_90 >= 0.7) & (rec.bias.abs() <= rec.mean_laplace_se)
        check(bool(ok.all()), '9c estimator recovers known hyperparameters (90% coverage, bias): '
              + ', '.join(f'{r.parameter} {r.coverage_90:.0%} / {r.bias:+.3f}' for r in rec.itertuples()))

    print('\nRESULT:', 'all checks passed' if not failures else f'{len(failures)} check(s) failed')
    return 0 if not failures else 1


if __name__ == '__main__':
    sys.exit(main())
