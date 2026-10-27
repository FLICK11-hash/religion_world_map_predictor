"""Step 7 comparison report: what improved, by how much, and what remains uncertain.

Run after run.py backtest and run.py project:
    .\\.venv\\Scripts\\python.exe run.py report            # outputs/comparison_report.md
    .\\.venv\\Scripts\\python.exe run.py report --export   # also copies small result files to results/
Writes outputs/comparison_report.md from the files in data/validation/ and
data/projections/ (and Step 5D results when present), so the report always matches the run.
--export writes results/ (small CSVs, the report and a README) that can be committed to share a run.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from religion_forecast import config

V = config.VALIDATION
F = config.PROJECTIONS
X = config.EXPERIMENTS
OUT = config.PROJECT / 'outputs' / 'comparison_report.md'
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
    for p in (config.DATA / 'forecasts_step5d' / 'global_share_uncertainty.csv',
              config.LEGACY_RESULTS / 'global_share_uncertainty.csv'):
        if p.exists():
            d = pd.read_csv(p)
            if 'scenario' in d:
                d = d[d.scenario.eq('demography_only')]
            return d, p.relative_to(config.PROJECT)
    return None, None


EXPORT = config.RESULTS
SMALL = ['global_share_by_scenario.csv', 'components_world_period.csv', 'dominant_change.csv',
         'uncertainty_model_vs_scenario.csv', 'switching_check_vs_pew.csv', 'switching_rates_2020.csv',
         'world_population_by_scenario.csv', 'parameter_provenance.csv', 'migration_corridors_reference.csv',
         'world_share_shift_share.csv', 'adherents_by_country.csv', 'fertility_evidence.csv',
         'group_fertility_2020_2025.csv', 'benchmark_vs_pew2015.csv', 'benchmark_pew2015_skill.csv',
         'run_outcomes.csv', 'projection_report.json']
SMALL_X = ['ablation_effects.csv', 'sensitivity_coefficients.csv', 'migrant_sorting_effect.csv']
SMALL_V = ['validation_summary.csv', 'validation_by_window.csv', 'data_ablations_summary.csv',
           'switching_fit_by_fold.csv', 'out_of_sample_choices.csv', 'migration_foreign_born_check.csv',
           'interval_calibration.csv', 'interval_calibration_windows.csv',
           'migration_foreign_born_by_country.csv', 'migration_corridor_check.csv', 'validation_report.json']


def export_results():
    import shutil
    EXPORT.mkdir(exist_ok=True)
    made = []
    for old in EXPORT.glob('*'):
        shutil.rmtree(old) if old.is_dir() else old.unlink()
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
    for name in SMALL_X:
        if (X / name).exists():
            shutil.copy2(X / name, EXPORT / name)
            made.append(name)
    ref = json.loads((F / 'projection_report.json').read_text()).get('reference_scenario', 'stabilising') \
        if (F / 'projection_report.json').exists() else 'stabilising'
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
        shutil.copy2(OUT, EXPORT / 'comparison_report.md')
        made.append('comparison_report.md')
    # Figures travel with the results. outputs/ is git-ignored because it is rewritten on every
    # run, but a shared run is unreadable without its maps, so the exported copy is tracked.
    if config.FIGURES.exists():
        shutil.copytree(config.FIGURES, EXPORT / 'figures')
        n = sum(1 for _ in (EXPORT / 'figures').rglob('*.svg'))
        made.append(f'figures/ ({n} SVG figures, open figures/index.html)')
    # reproducibility stamp: the commit the run was made at, and the integrity checks it passed
    import subprocess
    stamp = {}
    try:
        stamp['git_commit'] = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=config.PROJECT,
                                             capture_output=True, text=True, timeout=20).stdout.strip()
        dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=config.PROJECT,
                               capture_output=True, text=True, timeout=20).stdout.strip()
        stamp['working_tree'] = 'clean' if not dirty else f'{len(dirty.splitlines())} uncommitted changes'
    except Exception as exc:
        stamp['git_commit'] = f'unavailable ({exc})'
    try:
        from religion_forecast import checks
        import contextlib, io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = checks.main([])
        (EXPORT / 'integrity_checks.txt').write_text(buf.getvalue(), encoding='utf8')
        made.append('integrity_checks.txt')
        stamp['integrity_checks'] = 'all passed' if not code else f'{code} failed'
    except Exception as exc:
        stamp['integrity_checks'] = f'not run ({exc})'
    stamp['exported_utc'] = datetime.now(timezone.utc).isoformat()
    (EXPORT / 'run_stamp.json').write_text(json.dumps(stamp, indent=2), encoding='utf8')
    made.append('run_stamp.json')
    (EXPORT / 'README.md').write_text(
        '# Results of one run\n\nSmall copies of one complete run, written by `run.py report --export`, so a '
        'reader can check the numbers without re-running anything. The full outputs stay in data/ and are '
        'git-ignored.\n\nStart with `comparison_report.md`. `run_stamp.json` records the commit the run was made '
        'at and whether the integrity checks passed; `integrity_checks.txt` is their captured output. Open `figures/index.html` to browse every figure.\n\n' + '\n'.join(f'- {m}' for m in made) + '\n', encoding='utf8')
    print(f'Exported {len(made)} files to {EXPORT}')


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--export', action='store_true')
    args = ap.parse_args(argv)
    L = [f'# Step 7 comparison report\n\nGenerated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC from '
         '`data/validation/` and `data/projections/`.\n']
    rep = json.loads((F / 'projection_report.json').read_text()) if (F / 'projection_report.json').exists() else {}
    vrep = json.loads((V / 'validation_report.json').read_text()) if (V / 'validation_report.json').exists() else {}
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
    if (V / 'interval_calibration.csv').exists():
        cal = pd.read_csv(V / 'interval_calibration.csv')
        L.append('\n### 2b. Are the intervals honest?\n')
        L.append('The same Monte Carlo run on historical decades: how often the observed country x religion '
                 'share fell inside the model interval. A 90% interval should contain the truth 90% of the '
                 'time.\n')
        L.append(md(cal[['window', 'nominal', 'coverage', 'coverage_with_measurement_error',
                         'median_interval_width_pp']], 3))
        if (V / 'interval_calibration_windows.csv').exists():
            cw = pd.read_csv(V / 'interval_calibration_windows.csv')
            g = cw.groupby('religion')[['abs_error_median_pp', 'abs_error_q90_pp',
                                        'model_half_width_q90_pp', 'widening_needed']].mean().reset_index()
            L.append('\nOut-of-sample error at a ten-year horizon, against the width the model claims. '
                     'The last column is how much wider the intervals would have to be.\n')
            L.append(md(g, 2))
            L.append('\n**The published 5-95%% bands are the spread of model outputs under parameter '
                     'uncertainty, not forecast intervals.** Most of the forecast error is measurement '
                     'variation in the sources and country-level change the model has no mechanism for. '
                     'For a near-term error bar use the out-of-sample numbers above.\n')
    if (F / 'benchmark_pew2015_skill.csv').exists():
        sk = pd.read_csv(F / 'benchmark_pew2015_skill.csv')
        L.append('\n### 2c. An outside yardstick\n')
        L.append("Pew's 2015 report projected 2020; Pew's 2025 report measured it. Scoring one against the "
                 "other shows how much of the apparent error in this field is data revision rather than "
                 "forecasting.\n")
        L.append(md(sk, 2))
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
                 'share with the UN 2020 stocks. The circulation range in config/assumptions.json is calibrated on this '
                 'test.\n')
        L.append(md(fb, 3))
        L.append('')
    if (V / 'migration_corridor_check.csv').exists():
        L.append('Corridors 1990-2020 by margin softness (margin_rho; 1 = WPP margins exact): origin mix of simulated '
                 'inflows into the 25 largest destinations against the growth of UN bilateral stocks. The forecast draws '
                 'margin_rho per run (range in config/assumptions.json).\n')
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
        L.append('\n### 8b. Why migration changes diversity the way it does (`run.py experiments`)\n')
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
                    rows.append({'year': y, 'religion': c, 'earlier_model_demography_only': 100 * float(a.iloc[0]),
                                 'this_model': 100 * float(b.iloc[0]),
                                 'difference_pp': 100 * float(b.iloc[0] - a.iloc[0])})
        L.append(f'\n## 9. Against the earlier cohort model (Step 5D `demography_only`, from `{src}`)\n')
        L.append('The earlier model had no religious switching, so the gap between the two is almost entirely '
                 'what switching adds.\n')
        L.append(md(pd.DataFrame(rows), 2))
    if (F / 'world_share_shift_share.csv').exists():
        ss = pd.read_csv(F / 'world_share_shift_share.csv')
        y = 2100 if 2100 in set(ss.year) else int(ss.year.max())
        L.append(f'\n## 10. Where world-share change comes from, 2020-{y}\n')
        L.append('An exact split of each religion\'s change in WORLD share into countries\' own shares '
                 'changing and country populations growing at different rates. This is a different question '
                 'from the mechanism accounting above, and for several groups the two parts point in '
                 'opposite directions.\n')
        L.append(md(ss[ss.year.eq(y)][['religion', 'change_pp', 'within_country_pp',
                                       'population_weighting_pp', 'interaction_pp']], 2))
    if (X / 'ablation_effects.csv').exists():
        eff = pd.read_csv(X / 'ablation_effects.csv')
        L.append('\n## 11. What each mechanism contributes\n')
        L.append('The full model minus the same run with one mechanism switched off, paired run by run on '
                 'identical draws. Percentage points of world population.\n')
        show = eff[eff.year.isin([2050, 2100]) & eff.outcome.isin(
            ['world_Christianity', 'world_Islam', 'world_Unaffiliated', 'world_Hinduism',
             'dominant_changed_countries'])]
        piv = show.pivot_table(index=['outcome', 'year'], columns='mechanism', values='contribution_mean')
        piv.loc[[i for i in piv.index if not str(i[0]).startswith('dominant')]] *= 100
        L.append(md(piv.round(2).reset_index(), 2))
        L.append('\n(`dominant_changed_countries` is a count, not a percentage.)\n')
    if (X / 'sensitivity_coefficients.csv').exists():
        sc = pd.read_csv(X / 'sensitivity_coefficients.csv')
        sc = sc[sc.basis.eq('rank')]
        L.append('\n## 12. Which assumptions move the results\n')
        L.append('Standardised rank regression coefficients from a separate Monte Carlo design: how many '
                 'standard deviations an outcome moves when one parameter moves by one. Top five per '
                 'outcome.\n')
        for y in [v for v in (2100, 3026) if v in set(sc.year)]:
            top = (sc[sc.year.eq(y) & sc.outcome.isin(['world_Christianity', 'world_Islam',
                                                       'world_Unaffiliated', 'diversity_within_pop_weighted'])]
                   .sort_values('abs_coefficient', ascending=False).groupby('outcome').head(5))
            L.append(f'\n**{y}**\n')
            L.append(md(top[['outcome', 'parameter', 'coefficient', 'model_r2']], 3))
    if (X / 'migrant_sorting_effect.csv').exists():
        so = pd.read_csv(X / 'migrant_sorting_effect.csv')
        L.append('\n## 13. Does more migration make countries more mixed?\n')
        L.append('Rising minus low migration, paired by run, under three assumptions about where migrants '
                 'go. Positive means more migration leaves countries more religiously mixed.\n')
        L.append(md(so, 4))
    if (F / 'fertility_evidence.csv').exists():
        fe = pd.read_csv(F / 'fertility_evidence.csv')
        cov = (fe.groupby('evidence_tier').population_2020.sum() / fe.population_2020.sum() * 100)
        L.append('\n## 14. How much of the fertility input is measured\n')
        L.append('Share of 2020 world population whose religion-specific fertility comes from each evidence '
                 'tier.\n')
        L.append(md(cov.round(1).rename('percent_of_world_population').reset_index(), 1))
    L.append('\n## 15. What remains uncertain\n')
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
