"""Step 7 comparison report: what improved, by how much, and what remains uncertain.

Run after step7_validate.py and step7_forecast.py:
    .\\.venv\\Scripts\\python.exe step7_report.py            # outputs/step7_comparison_report.md
    .\\.venv\\Scripts\\python.exe step7_report.py --export   # also copies small result files to results_step7/
Writes outputs/step7_comparison_report.md from the files in data/validation_step7/ and
data/forecasts_step7/ (and Step 5D results when present), so the report always matches the run.
--export writes results_step7/ (small CSVs, the report and a README) that can be committed to share a run.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
V = ROOT / 'data' / 'validation_step7'
F = ROOT / 'data' / 'forecasts_step7'
OUT = ROOT / 'outputs' / 'step7_comparison_report.md'
CATS = ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism', 'Folk_Traditional', 'Other', 'Unaffiliated']
TARGET = [2020, 2050, 2100, 2200, 2500, 3026]


def md(df, floatfmt=2):
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_float_dtype(df[c]):
            df[c] = df[c].map(lambda v: '' if pd.isna(v) else f'{v:.{floatfmt}f}')
    head = '| ' + ' | '.join(map(str, df.columns)) + ' |'
    sep = '|' + '|'.join('---' for _ in df.columns) + '|'
    body = ['| ' + ' | '.join(map(str, r)) + ' |' for r in df.itertuples(index=False)]
    return '\n'.join([head, sep] + body)


def step5d_world():
    for p in (ROOT / 'data' / 'forecasts_step5d' / 'global_share_uncertainty.csv',
              ROOT / 'results_step5' / 'global_share_uncertainty.csv'):
        if p.exists():
            d = pd.read_csv(p)
            if 'scenario' in d:
                d = d[d.scenario.eq('demography_only')]
            return d, p.relative_to(ROOT)
    return None, None


EXPORT = ROOT / 'results_step7'
SMALL = ['global_share_by_scenario.csv', 'components_world_period.csv', 'dominant_change.csv',
         'uncertainty_model_vs_scenario.csv', 'switching_check_vs_pew.csv', 'switching_rates_2020.csv',
         'world_population_by_scenario.csv', 'parameter_provenance.csv', 'migration_corridors_reference.csv',
         'sensitivity_migrant_sorting.csv', 'step7_report.json']
SMALL_V = ['validation_summary.csv', 'validation_by_window.csv', 'data_ablations_summary.csv',
           'switching_fit_by_fold.csv', 'out_of_sample_choices.csv', 'migration_foreign_born_check.csv',
           'migration_foreign_born_by_country.csv', 'migration_corridor_check.csv', 'step7_validation_report.json']


def export_results():
    import shutil
    EXPORT.mkdir(exist_ok=True)
    made = []
    for old in EXPORT.glob('*'):
        old.unlink()
    for name in SMALL:
        if (F / name).exists():
            if name == 'global_share_by_scenario.csv':
                pd.read_csv(F / name).round(5).to_csv(EXPORT / name, index=False)
            else:
                shutil.copy2(F / name, EXPORT / name)
            made.append(name)
    for name in SMALL_V:
        if (V / name).exists():
            shutil.copy2(V / name, EXPORT / ('validation_' + name if not name.startswith('validation') else name))
            made.append(name)
    ref = json.loads((F / 'step7_report.json').read_text()).get('reference_scenario', 'stabilising') \
        if (F / 'step7_report.json').exists() else 'stabilising'
    if (F / 'country_year_by_scenario.csv').exists():
        ct = pd.read_csv(F / 'country_year_by_scenario.csv')
        ct = ct[ct.year.isin(TARGET)]
        keep = ['scenario', 'country_id', 'year', 'mean_population', 'most_likely_dominant', 'dominant_agreement_fraction',
                'diversity_gini_simpson_mean', 'foreign_born_share_mean'] + [c for c in ct.columns if c.startswith('mean_') and c != 'mean_population']
        ct[keep].round(4).to_csv(EXPORT / 'country_target_years_by_scenario.csv', index=False)
        ct[ct.scenario.eq(ref)].round(4).to_csv(EXPORT / 'country_target_years_reference_with_bands.csv', index=False)
        made += ['country_target_years_by_scenario.csv', 'country_target_years_reference_with_bands.csv']
    if (F / 'components_country_period.csv').exists():
        cp = pd.read_csv(F / 'components_country_period.csv')
        cp = cp[cp.scenario.eq(ref) & cp.period.isin(['2020-2050', '2050-2100'])]
        cp = cp.groupby(['scenario', 'country_id', 'religion'], as_index=False).sum(numeric_only=True)
        cp.insert(1, 'period', '2020-2100')
        cp.round(3).to_csv(EXPORT / 'components_country_2020_2100_reference.csv', index=False)
        made.append('components_country_2020_2100_reference.csv')
    if OUT.exists():
        shutil.copy2(OUT, EXPORT / 'step7_comparison_report.md')
        made.append('step7_comparison_report.md')
    (EXPORT / 'README.md').write_text(
        '# Step 7 results (exported)\n\nSmall copies of one Step 7 run, written by `step7_report.py --export`. '
        'Full outputs are in data/forecasts_step7 and data/validation_step7 (git-ignored) on the machine that ran it. '
        'Start with step7_comparison_report.md.\n\n' + '\n'.join(f'- {m}' for m in made) + '\n', encoding='utf8')
    print(f'Exported {len(made)} files to {EXPORT}')


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--export', action='store_true')
    args = ap.parse_args()
    L = [f'# Step 7 comparison report\n\nGenerated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC from '
         '`data/validation_step7/` and `data/forecasts_step7/`.\n']
    rep = json.loads((F / 'step7_report.json').read_text()) if (F / 'step7_report.json').exists() else {}
    vrep = json.loads((V / 'step7_validation_report.json').read_text()) if (V / 'step7_validation_report.json').exists() else {}
    L.append('## 1. Inputs used in this run\n')
    rows = [{'input': k, 'status': v['status'], 'detail': v['detail']} for k, v in rep.get('inputs', {}).items()]
    if rows:
        L.append(md(pd.DataFrame(rows)))
    L.append(f"\nStart state: {rep.get('start_state', 'n/a')}. Runs per scenario: {rep.get('runs_per_scenario')}, "
             f"seed {rep.get('seed')}.\n")
    if (V / 'validation_summary.csv').exists():
        vs = pd.read_csv(V / 'validation_summary.csv')
        L.append('## 2. History tests (forward chaining; lower is better)\n')
        L.append('Population-weighted total-variation error in percentage points; negative change = better than '
                 'persistence. Switching and residual weights were chosen on earlier windows only.\n')
        keep = ['persistence', 'demography', 'demography_migration', 'switching_strength_0.5', 'switching_strength_1',
                'demography_migration_switching', 'demography_migration_switching_residual', 'demography_migration_momentum']
        t = vs[vs.model.isin(keep)][['scope', 'model', 'windows', 'popw_tv_pp', 'change_vs_persistence_pp',
                                     'dominant_accuracy', 'changed_true', 'changed_hit', 'false_alarm']]
        L.append(md(t, 3))
    if (V / 'data_ablations_summary.csv').exists():
        ab = pd.read_csv(V / 'data_ablations_summary.csv')
        L.append('\n### Does each new dataset improve the history tests?\n')
        L.append(md(ab[['scope', 'data_variant', 'model', 'popw_tv_pp', 'change_vs_persistence_pp']], 3))
        L.append('\nThe calibrated religion of migrants uses Pew 2020 migrant data, so its effect on the 1970-2010 windows '
                 'contains information from after those windows (labelled, not hidden).\n')
    ch = vrep.get('history_test_choices', vrep.get('choices_for_forecast', {}))
    if ch:
        r3 = lambda d: {k: round(v, 3) for k, v in (d or {}).items()}
        L.append(f"\nResidual learner weight chosen out of sample: {ch.get('residual')}.\n")
        L.append(f"Switching strength (multiplier on fitted rates), mean error: all four windows "
                 f"{r3(ch.get('switching_strength_scores_popw_tv_pp'))}; 1990-2010 "
                 f"{r3(ch.get('switching_strength_scores_1990_2010_popw_tv_pp'))}.\n")
        used = vrep.get('used_by_forecast', {})
        if used:
            L.append(f"Forecast: switching strength {used.get('switching_strength')}\n")
    L.append('## 3. Religious switching\n')
    sf = rep.get('switching_fit', {})
    L.append(f"Empirical Bayes fit: delta = {sf.get('delta')}, beta_d (development effect, logit per unit) = "
             f"{sf.get('beta_d')}, tau_u (country spread) = {sf.get('tau_u')}; median posterior effective sample "
             f"size {sf.get('median_posterior_ess', float('nan')):.0f} of {sf.get('latent_draws')} (closer to the "
             'maximum = data say less about that country).\n')
    if (F / 'switching_check_vs_pew.csv').exists():
        sc = pd.read_csv(F / 'switching_check_vs_pew.csv')
        L.append('Lifetime switching levels against Pew 2025 (adults 18-54, 117 countries; left per 100 raised). '
                 'Each run mixes the two model levels with a random weight.\n')
        L.append(md(sc, 2))
    if (F / 'switching_rates_2020.csv').exists():
        sr = pd.read_csv(F / 'switching_rates_2020.csv')
        d = sr[sr.rate.str.startswith('disaffiliation') & sr.religion.eq('Christianity')].sort_values('mean', ascending=False)
        L.append('\nHighest fitted lifetime disaffiliation of people raised Christian (history level, 2020 development):\n')
        L.append(md(d.head(10)[['country_id', 'mean', 'q05', 'q95', 'evidence']], 3))
    L.append('\n## 4. Migration\n')
    es = rep.get('emigration_selectivity')
    if es:
        L.append(f"Religion of migrants calibrated to Pew's published composition of migrants (19 targets): destination "
                 f"affinity kappa = {es.get('kappa')}, minority effect lambda = {es['lam']:.2f}; error {es['rmse_pp']:.2f} pp "
                 f"versus {es['rmse_if_mirror_origin_pp']:.2f} pp if migrants mirrored their origin.\n")
    if (V / 'migration_foreign_born_check.csv').exists():
        fb = pd.read_csv(V / 'migration_foreign_born_check.csv')
        L.append('Migration volumes against data: start from the UN 1990 foreign-born stocks, simulate 1990-2020 '
                 '(WPP demography, the migration model, no switching) and compare each country\'s 2020 foreign-born '
                 'share with the UN 2020 stocks. The circulation range in step7_assumptions.json is calibrated on this '
                 'test.\n')
        L.append(md(fb, 3))
        L.append('')
    if (V / 'migration_corridor_check.csv').exists():
        L.append('Corridors 1990-2020 by margin softness (margin_rho; 1 = WPP margins exact): origin mix of simulated '
                 'inflows into the 25 largest destinations against the growth of UN bilateral stocks. The forecast draws '
                 'margin_rho per run (range in step7_assumptions.json).\n')
        L.append(md(pd.read_csv(V / 'migration_corridor_check.csv'), 3))
        L.append('')
    if (F / 'migration_corridors_reference.csv').exists():
        co = pd.read_csv(F / 'migration_corridors_reference.csv')
        L.append('Largest simulated corridors 2020-2050 (reference scenario, persons over the period):\n')
        L.append(md(co[co.period.eq('2020-2050')].head(12)[['origin', 'destination', 'persons']], 0))
    L.append('\n## 5. World shares by scenario (%)\n')
    if (F / 'global_share_by_scenario.csv').exists():
        wt = pd.read_csv(F / 'global_share_by_scenario.csv')
        for y in (2050, 2100, 2500, 3026):
            p = wt[wt.year.eq(y)].pivot(index='scenario', columns='religion', values='mean')[CATS] * 100
            L.append(f'\n**{y}**' + (' (speculative)' if y >= 2500 else '') + '\n')
            L.append(md(p.reset_index(), 1))
    if (F / 'uncertainty_model_vs_scenario.csv').exists():
        us = pd.read_csv(F / 'uncertainty_model_vs_scenario.csv')
        L.append('\n### Model uncertainty versus scenario uncertainty (world shares, pp)\n')
        L.append('Within = mean 5-95% band inside a scenario (parameters, switching evidence, country noise). '
                 'Between = range of scenario means (assumptions).\n')
        L.append(md(us[us.year.isin([2050, 2100, 3026])], 2))
    if (F / 'components_world_period.csv').exists():
        wc = pd.read_csv(F / 'components_world_period.csv')
        ref = rep.get('reference_scenario', 'stabilising')
        w = wc[wc.scenario.eq(ref) & wc.period.isin(['2020-2050', '2050-2100'])].groupby('religion').sum(numeric_only=True).reindex(CATS)
        cols = [c for c in w.columns if c.startswith('world_share_pp_')]
        L.append(f'\n## 6. What changes world shares, 2020-2100 ({ref}; percentage points)\n')
        L.append('From the simulation\'s sequential sub-steps (they add up exactly to the total). Migration cancels worldwide.\n')
        L.append(md(w[cols].rename(columns=lambda c: c.replace('world_share_pp_', '')).reset_index(), 2))
    if (F / 'dominant_change.csv').exists():
        dc = pd.read_csv(F / 'dominant_change.csv')
        g = dc.groupby('scenario').agg(**{f'changed_by_{y}': (f'prob_changed_by_{y}', lambda s: int((s > 0.5).sum()))
                                          for y in (2050, 2100, 2200, 2500, 3026)}).reset_index()
        L.append('\n## 7. Countries whose dominant religion changes (most runs)\n')
        L.append(md(g, 0))
    if (F / 'country_year_by_scenario.csv').exists():
        ct = pd.read_csv(F / 'country_year_by_scenario.csv')
        c2 = ct[ct.year.isin(TARGET)].assign(w=lambda d: d.diversity_gini_simpson_mean * d.mean_population)
        g = (c2.groupby(['scenario', 'year']).w.sum() / c2.groupby(['scenario', 'year']).mean_population.sum()).rename('diversity')
        L.append('\n## 8. Religious diversity within countries (population-weighted Gini-Simpson)\n')
        L.append(md(g.reset_index().pivot(index='scenario', columns='year', values='diversity').reset_index(), 3))
    if (F / 'sensitivity_migrant_sorting.csv').exists():
        se = pd.read_csv(F / 'sensitivity_migrant_sorting.csv')
        L.append('\n### 8b. Why migration changes diversity the way it does (`step7_sensitivity.py`)\n')
        L.append(f'Population-weighted within-country diversity; median of {se.run.nunique()} runs. Every cell uses the '
                 'same random draws, so differences come from the assumption alone. *calibrated*: migrants favour '
                 'destinations where their religion is common (kappa) and minorities emigrate more (lambda), both '
                 'fitted to Pew; *no_affinity*: kappa = 0; *mirror*: migrants have their origin\'s religious mix.\n')
        t = se.groupby(['year', 'variant', 'scenario']).diversity_within_pop_weighted.median().unstack('scenario')
        L.append(md(t.reset_index(), 3))
        if {'rising_migration', 'low_migration'} <= set(se.scenario):
            pv = se.pivot_table(index=['year', 'variant', 'run'], columns='scenario',
                                values='diversity_within_pop_weighted').reset_index()
            pv['d'] = pv.rising_migration - pv.low_migration
            g = pv.groupby(['year', 'variant']).d.agg(median='median', runs_above_zero=lambda x: int((x > 0).sum()),
                                                      runs='size').reset_index()
            L.append('\nRising minus low migration, paired by run (positive = more migration, more diverse countries):\n')
            L.append(md(g, 3))
    d5, src = step5d_world()
    if d5 is not None and (F / 'global_share_uncertainty.csv').exists():
        s7 = pd.read_csv(F / 'global_share_uncertainty.csv')
        rows = []
        for y in (2050, 2100):
            for c in CATS:
                a = d5[(d5.year == y) & (d5.religion == c)]['mean']
                b = s7[(s7.year == y) & (s7.religion == c)]['mean']
                if len(a) and len(b):
                    rows.append({'year': y, 'religion': c, 'step5d_demography_only': 100 * float(a.iloc[0]),
                                 'step7_reference': 100 * float(b.iloc[0]),
                                 'difference_pp': 100 * float(b.iloc[0] - a.iloc[0])})
        L.append(f'\n## 9. Step 7 versus Step 5D (headline `demography_only`, from `{src}`)\n')
        L.append(md(pd.DataFrame(rows), 2))
    L.append('\n## 10. What remains uncertain\n')
    L.extend(['- Switching levels: rates fitted to net share changes are lower than Pew 2025 survey levels for Christians and '
              'Buddhists; runs span both. History tests at decade scale cannot settle which is right.',
              '- The religion of migrants is calibrated to aggregate Pew figures; corridor-level religion (Pew dataset, free '
              'account) would replace the calibration. Destination affinity (kappa) decides whether more migration makes '
              'countries more diverse (section 8b).',
              '- Circulation is calibrated to foreign-born stocks, so gross churn is understated (returning emigrants count '
              'as foreign-born). UN stocks also carry legacy corridors (for example India-Pakistan from 1947) into the network.',
              '- Group fertility gaps are damped Pew global ratios except where religion_fertility_observed.csv is supplied.',
              '- After 2100 all demography is assumption; 2500 and 3026 are speculative scenarios, not forecasts.',
              '- Folk/Traditional versus Other in Pew data is a WRP proxy; WRP and Pew classify much of China differently.'])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(L) + '\n', encoding='utf8')
    print(f'Wrote {OUT}')
    if args.export:
        export_results()


if __name__ == '__main__':
    main()
