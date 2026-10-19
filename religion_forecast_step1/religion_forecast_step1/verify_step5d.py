"""Integrity checks for Step 5D, plus the diagnostics that say how far to trust it."""
import json

import numpy as np
import pandas as pd

from step5d_cohort_forecast import OUT, ROOT, YEARS, CATEGORIES, SCENARIOS

report = json.loads((OUT / 'step5d_report.json').read_text(encoding='utf8'))
R, N = int(report['runs']), int(report['countries'])
HEAD = report['headline_scenario']
s = np.load(OUT / 'ensemble_shares_float32.npy', mmap_mode='r')
p = np.load(OUT / 'ensemble_populations_float32.npy', mmap_mode='r')
assert s.shape == (R, len(YEARS), N, len(CATEGORIES)) and p.shape == (R, len(YEARS), N)
for t, y in enumerate(YEARS):
    sh = np.asarray(s[:, t], float)
    assert np.isfinite(sh).all() and (sh >= -1e-7).all() and (sh <= 1 + 1e-7).all(), y
    assert np.allclose(sh.sum(-1), 1, atol=2e-6), y
    assert np.isfinite(p[:, t]).all() and (p[:, t] > 0).all(), y
assert np.allclose(s[:, YEARS.index(3026)], .8 * s[:, YEARS.index(3025)] + .2 * s[:, YEARS.index(3030)], atol=2e-6)
summary = pd.read_csv(OUT / 'scenario_change_summary.csv')
assert set(summary.scenario) == set(SCENARIOS) and len(summary) == len(SCENARIOS) * len(YEARS)
assert summary.median_share_redistribution.between(0, 1).all()
country = pd.read_csv(OUT / 'country_year_uncertainty.csv')   # headline scenario, read by Step 6 maps
assert len(country) == len(YEARS) * N and not country.duplicated(['country_id', 'year']).any()
assert np.allclose(country[[f'mean_{c}' for c in CATEGORIES]].sum(axis=1), 1, atol=2e-6)
allsc = pd.read_csv(OUT / 'country_year_uncertainty_by_scenario.csv')
assert len(allsc) == len(SCENARIOS) * len(YEARS) * N
assert np.allclose(allsc[[f'mean_{c}' for c in CATEGORIES]].sum(axis=1), 1, atol=2e-6)
params = pd.read_csv(OUT / 'scenario_parameters.csv')
runs = pd.read_csv(OUT / 'global_share_by_run.csv')
assert set(runs.run) == set(params.run), 'run numbers in global_share_by_run.csv must match scenario_parameters.csv'
print(f'PASS: Step 5D {R} runs, {N} countries, {len(SCENARIOS)} scenarios; shares, population, 3026 interpolation, '
      'summaries, run numbering.')

print('\nDIAGNOSTICS (read these before using any result)')
print(f"- Countries with WPP defaults in 2020: {report['countries_with_wpp_defaults_2020']}; "
      f"without a Pew 2010 baseline (zero switching): {report['countries_without_pew_2010_baseline_zero_switching']}")
drift = params.mean_abs_log_rescale_to_2100
print(f'- Rescale to WPP totals per 5-year step (mean |log factor|): median {drift.median():.3f}, max {drift.max():.3f}. '
      'Large values mean the cohort engine disagrees with WPP population growth.')

diag = pd.read_csv(OUT / 'hindcast_diagnostics.csv')
print('- Hindcast 2010->2020 (global pop-weighted, percentage points of error vs Pew 2020):')
print(diag[['religion', 'persistence_error_pp', 'demography_only_error_pp',
            'countries_where_demography_gets_sign_right']].round(3).to_string(index=False))
better = (diag.demography_only_error_pp.abs() < diag.persistence_error_pp.abs()).sum()
print(f'  demography-only beats persistence for {better} of {len(diag)} religions at the global level.')

scan = pd.read_csv(OUT / 'hindcast_phi_scan.csv')
spread = float(scan.pop_weighted_tv_pp.max() - scan.pop_weighted_tv_pp.min())
phi_lo, phi_hi = json.loads((ROOT / 'step5d_assumptions.json').read_text(encoding='utf8'))[
    'parameter_ranges']['phi']['range']
if spread < 0.05:
    print(f'- Within-country fertility gap (phi): NOT IDENTIFIED. Error changes by only {spread:.3f} pp '
          'across phi 0-1 in the Pew 2010-2020 hindcast, so the sampled range is a judgement.')
else:
    best = scan.loc[scan.pop_weighted_tv_pp.idxmin()]
    print(f'- Within-country fertility gap (phi): best phi {best.phi:.2f} in the Pew 2010-2020 hindcast '
          f'(error {best.pop_weighted_tv_pp:.2f} pp); sampled range {phi_lo}-{phi_hi}.')
print(f"  Persistence (no change) scores {scan.persistence_pop_weighted_tv_pp.iloc[0]:.2f} pp; the demographic "
      'model should beat it. Step 5E history tests show demography only slightly better than no change.')
print(pd.read_csv(OUT / 'global_vs_pew2015_2050.csv').to_string(index=False))

print('\nSENSITIVITY: which parameters move the headline shares in 2050? (correlation across headline runs)')
head = runs[runs.scenario.eq(HEAD) & runs.year.eq(2050)].merge(params, on='run', suffixes=('', '_par'))
cols = ['Unaffiliated', 'Christianity', 'Islam']
rows = []
for name in ['psi', 'phi', 'w_add', 'Hf', 'e0', 'tfr_shift', 'lam_nb', 'lam_od', 'lam']:
    if name in head and head[name].nunique() > 1:
        rows.append({'parameter': name, **{c: round(float(np.corrcoef(head[name], head[c])[0, 1]), 2) for c in cols}})
print(pd.DataFrame(rows).to_string(index=False))
print(f'  Based on {len(head)} headline runs. |correlation| under about 0.3 is noise at this run count.')

decomp = pd.read_csv(OUT / 'unaffiliated_decomposition.csv') if (OUT / 'unaffiliated_decomposition.csv').exists() else None
if decomp is not None:
    print('\nDECOMPOSITION (single deterministic runs; switch one mechanism off at a time)')
    for _, r in decomp.iterrows():
        print(f"  {r.setting:52s} unaffiliated {r.Unaffiliated_2020 * 100:5.1f}% -> {r.Unaffiliated_2050 * 100:5.1f}%"
              f"   Christianity {r.Christianity_2020 * 100:5.1f}% -> {r.Christianity_2050 * 100:5.1f}%")
    print('  If the unaffiliated share still falls with no fertility gaps and no migration, the cause is the starting '
          'age structure, not a fertility assumption.')
print('\nHEADLINE SHARES (global, population-weighted mean over runs)')
gu = pd.read_csv(OUT / 'global_share_uncertainty.csv')
mean = gu.pivot(index='year', columns='religion', values='mean')
change = (mean.loc[2050] - mean.loc[2020]) * 100
for c in ['Christianity', 'Islam', 'Hinduism', 'Unaffiliated']:
    print(f'  {c:13s} 2020 {mean.loc[2020, c] * 100:5.1f}%   2050 {mean.loc[2050, c] * 100:5.1f}%   change {change[c]:+5.1f} pp')
if change['Unaffiliated'] < -3:
    print('  WARNING: the headline unaffiliated share falls by more than 3 pp by 2050. History shows the unaffiliated '
          'rising since 1990, so this decline needs a clear cause. Check the sensitivity table above.')
if change['Christianity'] > 0:
    print('  NOTE: the headline has no switching, so Christianity rises here. Between 1990 and 2010 history shows '
          'Christianity falling through switching, not demography.')

print('\nMIGRATION (headline scenario, mean over runs, 2020-2100)')
od = report.get('bilateral_migration')
if isinstance(od, dict) and 'file' in od:
    print(f"- Migration matrix: bilateral table {od['file']} ({od['pairs_used']} pairs; "
          f"{od['destinations_with_bilateral_data']} of {od['destinations_total']} destinations covered)")
elif isinstance(od, dict):
    print(f"- Migration matrix: {od.get('source')} (geography only; read the README_STEP5D limits before using destination results)")
else:
    print(f'- Migration matrix: {od}')
mig = pd.read_csv(OUT / 'migration_by_religion.csv')
m = mig[mig.period.eq('2020-2100')]
glob = m.groupby('religion')[['inflow_persons', 'outflow_persons', 'net_persons']].sum()
glob = (glob / 1e6).round(2).sort_values('net_persons')
print('Global net migration by religion (millions of persons; negative = net emigration):')
print(glob.to_string())
per_country = m.groupby('country_id').net_persons.sum().sort_values()
print('Largest net emigration (persons, all religions):')
print(per_country[per_country < 0].head(8).round(-3).to_string())
print('Largest net immigration (persons, all religions):')
print(per_country[per_country > 0].tail(8).round(-3).to_string())
losers = per_country[per_country < 0].head(8).index
top = m.loc[m.groupby('country_id').outflow_persons.idxmax()].set_index('country_id').loc[losers]
print('Religion most often leaving each country (top 8 by outflow):')
print(top[['religion', 'outflow_persons']].round(-3).to_string())
print('WARNING: exploratory mechanism model, not a validated 3026 forecast.')
