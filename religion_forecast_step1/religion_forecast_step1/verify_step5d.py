"""Integrity checks for Step 5D plus the diagnostics that say how far to trust it."""
import json
import numpy as np
import pandas as pd
from step5d_cohort_forecast import OUT, YEARS, CATEGORIES, SCENARIOS

report = json.loads((OUT / 'step5d_report.json').read_text(encoding='utf8'))
R, N = int(report['runs']), int(report['countries'])
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
print(f'PASS: Step 5D {R} runs, {N} countries, {len(SCENARIOS)} scenarios; shares, population, 3026 interpolation, summaries.')

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
best = scan.loc[scan.mean_country_tv_pp.idxmin()]
print(f"- Hindcast prefers phi={best.phi:.1f} (mean country TV {best.mean_country_tv_pp:.2f} pp vs "
      f"{best.persistence_mean_country_tv_pp:.2f} pp for 'nothing changes'). Sampled phi range is 0.3-0.7; "
      'if the best phi sits outside it, or demography does not beat persistence, revisit step5d_assumptions.json.')
print(pd.read_csv(OUT / 'global_vs_pew2015_2050.csv').to_string(index=False))
print('WARNING: exploratory mechanism model, not a validated 3026 forecast.')
