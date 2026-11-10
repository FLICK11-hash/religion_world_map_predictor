"""The run report: every headline number of one run, written from the files it produced.

    python run.py report            outputs/comparison_report.md
    python run.py report --export   also writes results/ (small copies of the run, for committing)

Reads data/validation/, data/projections/ and data/experiments/, so the report always matches the
run it describes. Nothing here is re-estimated.
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


EXPORT = config.RESULTS
SMALL = ['global_share_by_scenario.csv', 'components_world_period.csv', 'dominant_change.csv',
         'uncertainty_model_vs_scenario.csv', 'switching_check_vs_pew.csv', 'switching_rates_2020.csv',
         'world_population_by_scenario.csv', 'parameter_provenance.csv', 'migration_corridors_reference.csv',
         'migration_corridor_concentration.csv', 'world_share_shift_share.csv', 'adherents_by_country.csv',
         'fertility_evidence.csv', 'group_fertility_2020_2025.csv', 'benchmark_vs_pew2015.csv',
         'benchmark_pew2015_skill.csv', 'run_outcomes.csv', 'predictive_sensitivity_centring.csv', 'projection_report.json']
SMALL_X = ['ablation_effects.csv', 'sensitivity_coefficients.csv', 'migrant_sorting_effect.csv']
SMALL_V = ['validation_summary.csv', 'validation_by_window.csv', 'validation_by_country.csv', 'inference.csv',
           'data_ablations_summary.csv', 'switching_fit_by_fold.csv', 'out_of_sample_choices.csv',
           'forecast_error_model.json', 'forecast_error_record.csv', 'predictive_calibration.csv',
           'predictive_calibration_world.csv', 'migration_foreign_born_check.csv',
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
            shutil.copy2(V / name, EXPORT / name)
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
        # results/ is what this export rewrites, so its own changes do not count against the code
        dirty = subprocess.run(['git', 'status', '--porcelain', '--', '.', ':(exclude)results'], cwd=config.PROJECT,
                               capture_output=True, text=True, timeout=20).stdout.strip()
        stamp['working_tree'] = 'clean' if not dirty else f'{len(dirty.splitlines())} uncommitted changes outside results/'
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


def _read(path):
    return pd.read_csv(path) if path.exists() else None


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--export', action='store_true')
    args = ap.parse_args(argv)
    rep = json.loads((F / 'projection_report.json').read_text()) if (F / 'projection_report.json').exists() else {}
    vrep = json.loads((V / 'validation_report.json').read_text()) if (V / 'validation_report.json').exists() else {}
    ref = rep.get('reference_scenario', 'stabilising')
    L = [f'# Run report\n\nGenerated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC from `data/validation/`, '
         '`data/projections/` and `data/experiments/`. Shares are in percent; differences in percentage points (pp).\n']

    L.append('## 1. Inputs\n')
    rows = [{'input': k, 'status': v['status'], 'detail': v['detail']} for k, v in rep.get('inputs', {}).items()]
    if rows:
        L.append(md(pd.DataFrame(rows)))
    L.append(f"\nStart state: {rep.get('start_state', 'n/a')}. Runs per scenario: {rep.get('runs_per_scenario')}, "
             f"seed {rep.get('seed')}, reference scenario `{ref}`.\n")

    vs = _read(V / 'validation_summary.csv')
    if vs is not None:
        L.append('## 2. History tests\n')
        L.append('Ten-year forecasts of every test decade, fitted only on earlier decades. Population-weighted '
                 'total-variation (TV) error of country shares, in pp; the change is against persistence.\n')
        L.append(md(vs[['scope', 'model', 'windows', 'popw_tv_pp', 'change_vs_persistence_pp',
                        'change_vs_persistence_percent', 'dominant_accuracy', 'changed_true', 'changed_hit',
                        'false_alarm']], 3))
    inf = _read(V / 'inference.csv')
    if inf is not None:
        L.append('\n### Country-level comparison with persistence\n')
        L.append('Population-weighted mean difference in TV error over every country-decade (negative = better), '
                 'with a 95% interval from a bootstrap over countries, and the exact decade-level sign-flip test.\n')
        L.append(md(inf[['scope', 'model', 'country_windows', 'mean_difference_pp', 'ci95_low_pp', 'ci95_high_pp',
                         'p_bootstrap', 'share_better', 'windows_better', 'windows', 'p_window']], 3))

    em = dict(vrep.get('forecast_error_model') or {})
    if (V / 'forecast_error_model.json').exists():
        em.update({k: v for k, v in json.loads((V / 'forecast_error_model.json').read_text()).items() if k != 'mean_u'})
    cal = _read(V / 'predictive_calibration.csv')
    if em or cal is not None:
        L.append('\n## 3. Forecast errors and predictive intervals\n')
    if em:
        ma = em.get('mean_abs_standardised_error', {})
        L.append(f"Error model e = (h/10)^beta (s(1-s) + eps)^b u, fitted on the history record: b = {em['b']:.3f}, "
                 f"beta = {em['beta']:.3f}. Mean |standardised error| by horizon: "
                 + ', '.join(f'{k} years {v:.3f}' for k, v in sorted(ma.items(), key=lambda kv: int(kv[0]))) +
                 f". Resampling blocks: {', '.join(em.get('blocks', []))}.\n")
    if cal is not None:
        g = cal.groupby(['method', 'horizon', 'nominal']).agg(coverage=('coverage', 'mean'),
                                                              coverage_popw=('coverage_population_weighted', 'mean'),
                                                              interval_score_pp=('interval_score_pp', 'mean'),
                                                              median_width_pp=('median_width_pp', 'mean')).reset_index()
        L.append('Leave-one-origin-out: coverage of held-out country x religion shares and interval score '
                 '(lower is better), parameter-only against error-calibrated intervals.\n')
        L.append(md(g, 3))
    calw = _read(V / 'predictive_calibration_world.csv')
    if calw is not None:
        gw = calw.groupby(['method', 'horizon', 'nominal']).inside.mean().unstack('nominal').reset_index()
        L.append('\nWorld shares of the observed countries (8 religions per held-out origin and horizon): share inside '
                 'the interval, by nominal level.\n')
        L.append(md(gw, 2))

    L.append('\n## 4. Religious switching\n')
    sf = rep.get('switching_fit', {})
    if sf:
        reps = sf.get('replicates', [])
        L.append(f"Empirical Bayes fit, mean of {len(reps)} replicate fits: delta = {sf.get('delta', float('nan')):.3f}, "
                 f"beta_d = {sf.get('beta_d', float('nan')):.3f}, tau_u = {sf.get('tau_u', float('nan')):.3f}; replicate "
                 f"standard deviations {', '.join(f'{k} {v:.3f}' for k, v in sf.get('replicate_sd', {}).items())}. "
                 f"Median posterior effective sample size {sf.get('median_posterior_ess', float('nan')):.0f} of "
                 f"{sf.get('latent_draws')} draws.\n")
    sc = _read(F / 'switching_check_vs_pew.csv')
    if sc is not None:
        L.append('Lifetime switching levels against Pew (2025), adults 18-54 in 117 countries, left per 100 raised. '
                 'Each run weights the history level and the survey level at random.\n')
        L.append(md(sc, 2))
    sr = _read(F / 'switching_rates_2020.csv')
    if sr is not None:
        d = sr[sr.rate.str.startswith('disaffiliation') & sr.religion.eq('Christianity')].sort_values('mean', ascending=False)
        L.append('\nHighest fitted lifetime disaffiliation of people raised Christian (2020 development):\n')
        L.append(md(d.head(10)[['country_id', 'mean', 'q05', 'q95', 'evidence']], 3))

    L.append('\n## 5. Migration\n')
    es = rep.get('emigration_selectivity')
    if es:
        L.append(f"Religion of migrants calibrated to Pew's published composition of migrants: destination affinity "
                 f"kappa = {es.get('kappa')}, minority effect lambda = {es['lam']:.2f}; error {es['rmse_pp']:.2f} pp "
                 f"against {es['rmse_if_mirror_origin_pp']:.2f} pp if migrants mirrored their origin.\n")
    fb = _read(V / 'migration_foreign_born_check.csv')
    if fb is not None:
        L.append('Foreign-born share of each country in 2020, simulated from the UN 1990 stocks (no switching), '
                 'against the UN 2020 stocks:\n')
        L.append(md(fb, 3))
    cc = _read(V / 'migration_corridor_check.csv')
    if cc is not None:
        L.append('\nCorridors 1990-2020: origin mix of simulated inflows into the 25 largest destinations against the '
                 'growth of UN bilateral stocks, by margin softness and corridor cap (none = the model as used).\n')
        L.append(md(cc, 3))
    conc = _read(F / 'migration_corridor_concentration.csv')
    if conc is not None:
        L.append('\nLargest single origin of each main destination\'s simulated arrivals, 2020-2050 (reference), '
                 'against that origin\'s share of the destination\'s 2020 migrant stock:\n')
        L.append(md(conc.head(15), 2))

    wt = _read(F / 'global_share_by_scenario.csv')
    if wt is not None:
        L.append('\n## 6. World shares\n')
        r = wt[wt.scenario.eq(ref) & wt.year.isin([2020, 2050, 2100])].copy()
        for c in ('mean', 'q05', 'q95', 'pi05', 'pi95'):
            if c in r:
                r[c] = 100 * r[c]
        L.append(f'Reference scenario `{ref}`: mean, 5-95% of runs (parameter uncertainty) and 90% predictive interval.\n')
        L.append(md(r[['year', 'religion', 'mean', 'q05', 'q95'] + [c for c in ('pi05', 'pi95') if c in r]], 1))
        for y in (2050, 2100):
            pv = wt[wt.year.eq(y)].pivot(index='scenario', columns='religion', values='mean')[CATS] * 100
            L.append(f'\n**{y}, every scenario (means)**\n')
            L.append(md(pv.reset_index(), 1))
        L.append('\n**Exploratory horizons (stated long-run assumptions; not forecasts), reference scenario**\n')
        lr = wt[wt.scenario.eq(ref) & wt.year.isin([2200, 2500, 3026])].pivot(index='year', columns='religion',
                                                                              values='mean')[CATS] * 100
        L.append(md(lr.reset_index(), 1))
    ps = _read(F / 'predictive_sensitivity_centring.csv')
    if ps is not None and len(ps):
        L.append('\n**Predictive medians, and the effect of centring the errors.** The intervals use the record\'s errors '
                 'as they were; centring them (subtracting the pooled mean standardised error) is shown for comparison.\n')
        t = ps.copy()
        for c in t.columns:
            if c not in ('scenario', 'year', 'religion'):
                t[c] = 100 * t[c]
        L.append(md(t.drop(columns='scenario'), 1))
    us = _read(F / 'uncertainty_model_vs_scenario.csv')
    if us is not None:
        L.append('\n### Three kinds of uncertainty (world shares, pp)\n')
        L.append('Run spread = mean 5-95% band inside a scenario; predictive = mean 90% predictive band (to 2100); '
                 'between = range of scenario means.\n')
        L.append(md(us[us.year.isin([2050, 2100])], 2))

    wc = _read(F / 'components_world_period.csv')
    if wc is not None:
        w = wc[wc.scenario.eq(ref) & wc.period.isin(['2020-2050', '2050-2100'])].groupby('religion').sum(numeric_only=True).reindex(CATS)
        cols = [c for c in w.columns if c.startswith('world_share_pp_')]
        L.append(f'\n## 7. What changes world shares, 2020-2100 (`{ref}`, pp)\n')
        L.append('The simulation\'s own sub-step accounting; the parts add up exactly to the total. Migration cancels '
                 'worldwide.\n')
        L.append(md(w[cols].rename(columns=lambda c: c.replace('world_share_pp_', '')).reset_index(), 2))
    ss = _read(F / 'world_share_shift_share.csv')
    if ss is not None:
        y = 2100 if 2100 in set(ss.year) else int(ss.year.max())
        L.append(f'\n## 8. Where world-share change comes from, 2020-{y}\n')
        L.append('An exact split of each religion\'s change in world share into countries\' own shares changing '
                 'and country populations growing at different rates.\n')
        L.append(md(ss[ss.year.eq(y)][['religion', 'change_pp', 'within_country_pp', 'population_weighting_pp',
                                       'interaction_pp']], 2))
    eff = _read(X / 'ablation_effects.csv')
    if eff is not None:
        L.append('\n## 9. What each mechanism contributes\n')
        L.append('The full model minus the same run with one mechanism switched off, paired run by run on identical '
                 'draws. Percentage points of world population (dominant_changed_countries is a count).\n')
        show = eff[eff.year.isin([2050, 2100]) & eff.outcome.isin(
            ['world_Christianity', 'world_Islam', 'world_Unaffiliated', 'world_Hinduism', 'dominant_changed_countries'])]
        piv = show.pivot_table(index=['outcome', 'year'], columns='mechanism', values='contribution_mean')
        piv.loc[[i for i in piv.index if not str(i[0]).startswith('dominant')]] *= 100
        L.append(md(piv.round(2).reset_index(), 2))
    sens = _read(X / 'sensitivity_coefficients.csv')
    if sens is not None:
        sens = sens[sens.basis.eq('rank')]
        L.append('\n## 10. Which assumptions move the results\n')
        L.append('Standardised rank regression coefficients (top five per outcome) from a separate Monte Carlo design.\n')
        for y in [v for v in (2050, 2100) if v in set(sens.year)]:
            top = (sens[sens.year.eq(y) & sens.outcome.isin(['world_Christianity', 'world_Islam', 'world_Unaffiliated',
                                                               'diversity_within_pop_weighted'])]
                   .sort_values('abs_coefficient', ascending=False).groupby('outcome').head(5))
            L.append(f'\n**{y}**\n')
            L.append(md(top[['outcome', 'parameter', 'coefficient', 'model_r2']], 3))
    dc = _read(F / 'dominant_change.csv')
    if dc is not None:
        L.append('\n## 11. Countries whose largest religion changes\n')
        g = dc.groupby('scenario').agg(**{f'most_runs_by_{y}': (f'prob_changed_by_{y}', lambda s_: int((s_ > 0.5).sum()))
                                          for y in (2050, 2100, 2200, 2500, 3026)}).reset_index()
        L.append('Countries where most runs change (parameter uncertainty only):\n')
        L.append(md(g, 0))
        pcol = 'prob_changed_by_2100_predictive'
        if pcol in dc:
            r = dc[dc.scenario.eq(ref)].sort_values(pcol, ascending=False)
            L.append(f'\nPredictive probability of a change by 2050 and 2100 (`{ref}`), the 25 highest at 2100. '
                     f'{int((r[pcol] > 0.5).sum())} countries exceed 50% by 2100.\n')
            L.append(md(r.head(25)[['country_id', 'dominant_2020', 'most_likely_2100', 'prob_changed_by_2050_predictive',
                                     pcol, 'prob_changed_by_2100']], 2))
    so = _read(X / 'migrant_sorting_effect.csv')
    if so is not None:
        L.append('\n## 12. Does more migration make countries more mixed?\n')
        L.append('Rising minus low migration, paired by run, under three assumptions about where migrants go.\n')
        L.append(md(so, 4))
    fe = _read(F / 'fertility_evidence.csv')
    if fe is not None:
        cov = fe.groupby('evidence_tier').population_2020.sum() / fe.population_2020.sum() * 100
        L.append('\n## 13. How much of the fertility input is measured\n')
        L.append(md(cov.round(1).rename('percent_of_world_population').reset_index(), 1))
    bm = _read(F / 'benchmark_vs_pew2015.csv')
    if bm is not None:
        L.append('\n## 14. Against Pew Research Center\'s 2015 projection\n')
        L.append('Change in world share 2020-2050 as each projects it, and the difference in 2020 levels.\n')
        L.append(md(bm[bm.level.eq('world')][['religion', 'this_model_change_pp', 'pew2015_change_pp',
                                               'change_difference_pp', 'level_difference_2020_pp']], 2))
    sk = _read(F / 'benchmark_pew2015_skill.csv')
    if sk is not None:
        L.append('\nPew\'s 2015 projection of 2020 scored against Pew\'s later measurement of 2020:\n')
        L.append(md(sk, 2))
    L.append('\n## 15. Read with care\n')
    L.extend(['- All history tests and predictive intervals are conditional on national demography (WPP 2024 estimates '
              'inside each historical window, the WPP 2024 medium variant in the projection).',
              '- The predictive intervals extrapolate the error growth measured at 10-40 years to 80 years.',
              '- Beyond 2100 every demographic input is a stated assumption; 2200, 2500 and 3026 are exploratory.',
              '- The religion of migrants is calibrated to aggregate Pew figures, not observed by corridor.',
              '- Folk/Traditional versus Other in Pew data is a World Religion Project proxy, and the two sources '
              'classify much of China differently.'])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(L) + '\n', encoding='utf8')
    print(f'Wrote {OUT}')
    if args.export:
        export_results()


if __name__ == '__main__':
    main()
