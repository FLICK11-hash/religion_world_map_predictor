"""Step 7 forecast: religious composition of every country, 2020-3030, under eight scenarios.

Run (from this folder, Windows PowerShell):
    .\\.venv\\Scripts\\python.exe run.py fetch         # optional data (once)
    .\\.venv\\Scripts\\python.exe run.py backtest           # history tests (writes data/validation)
    .\\.venv\\Scripts\\python.exe run.py project           # this script (runs from config/assumptions.json)
    .\\.venv\\Scripts\\python.exe run.py checks
    .\\.venv\\Scripts\\python.exe run.py figures --png
Options: --runs N (per scenario), --scenarios a,b, --seed S, --quick (8 runs, for a fast check).
Writes data/projections/ (git-ignored). Earlier steps' outputs are not touched.

What is fitted before the runs
  religion of migrants    minority effect and destination affinity calibrated to Pew's published
                          religious composition of migrants (needs UN bilateral stocks; otherwise
                          migrants mirror their origin)
  switching               empirical Bayes on (a) what demographic hindcasts of WRP 1950-2010 and, when
                          available, Pew 2010-2020 leave unexplained and (b) verified survey cells in
                          inputs/switching_lifetime_observed.csv
Each run draws every uncertain parameter (ranges in config/assumptions.json), one posterior switching
draw per country, and the switching strength. Run r uses the same draws in every scenario (common
random numbers), so differences between scenarios come from the scenario assumptions alone.
Within-scenario spread = model and parameter uncertainty; differences between scenarios = scenario
uncertainty. Both are reported separately.
Years after 2100 rest on stated long-run assumptions; 2500 and 3026 are speculative scenarios.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from religion_forecast import datasets as D
from religion_forecast import engine as E
from religion_forecast import calibration as ES
from religion_forecast import model as SM
from religion_forecast import switching as SW
from religion_forecast import tables as T
from religion_forecast import config

OUT = config.PROJECTIONS
CATS, K = E.CATS, E.K
TARGET_YEARS = [2020, 2050, 2100, 2200, 2500, 3026]
YEARS = sorted(set(SM.KEEP_YEARS) | {3026})
STEPS = list(range(2020, 3031, 5))
PERIOD_LABEL = {pr: f'{pr[0]}-{pr[1]}' for pr in SM.PERIODS}


def prepare(ctx):
    """Calibrations shared by every run."""
    ctx.selectivity = ES.calibrate_affinity(ctx)
    p0 = ES.central_params(ctx)
    wins = ES.no_switching_hindcasts(ctx, p0, ES.windows(ctx))
    hier = ES.fit_switching(ctx, wins, use_survey=True)
    hier.survey_level = ES.calibrate_survey_level(ctx, hier)
    return hier, wins


class Store:
    """Per-scenario accumulators (all runs kept for kept years; components summed)."""

    def __init__(self, n, R):
        Y, S, P = len(YEARS), len(STEPS), len(SM.PERIODS)
        self.sh = np.zeros((R, Y, n, K), np.float32)
        self.pop = np.zeros((R, Y, n))
        self.fb = np.zeros((R, Y, n), np.float32)
        self.g2 = np.zeros((R, Y, n), np.float32)
        self.world = np.zeros((R, S, K))
        self.cp = np.zeros((P, n, K, len(E.COMPONENTS)))
        self.cs = np.zeros((P, n, K, len(E.SHARE_STEPS)))
        self.ws = np.zeros((P, K, len(E.SHARE_STEPS)))
        self.mig_in = np.zeros((P, n, K))
        self.mig_out = np.zeros((P, n, K))
        self.od = np.zeros((2, n, n))
        self.params, self.diag, self.rates = [], [], []
        self.group_tfr = None                 # summed over runs; divided by R when tabulated
        self.fertility_evidence = None
        self.R = 0

    def add(self, r, res, p):
        for j, y in enumerate(YEARS):
            self.sh[r, j] = res['shares'][y]
            self.pop[r, j] = res['pop'][y]
            self.fb[r, j] = res['foreign_born'][y]
            self.g2[r, j] = res['second_gen'][y]
        for j, y in enumerate(STEPS):
            self.world[r, j] = res['world'][y]
        for pi, pr in enumerate(SM.PERIODS):
            if pr in res['components']:
                rec = res['components'][pr]
                self.cp[pi] += rec.persons
                self.cs[pi] += rec.share
                self.ws[pi] += rec.world_share
                self.mig_in[pi] += res['mig_in'][pr]
                self.mig_out[pi] += res['mig_out'][pr]
        for oi, pr in enumerate(SM.PERIODS[:2]):
            if pr in res['od']:
                self.od[oi] += res['od'][pr]
        self.params.append({k: v for k, v in p.items() if np.ndim(v) == 0})
        self.diag.append(dict(rescale_mean_abs_log=float(np.mean(res['rescale'])) if res['rescale'] else 0.0,
                              migration_shortfall_persons=res['migration_shortfall']))
        if 2025 in res['lifetime_rates']:
            self.rates.append(res['lifetime_rates'])
        if res.get('group_tfr_2025') is not None:
            self.group_tfr = res['group_tfr_2025'] if self.group_tfr is None else self.group_tfr + res['group_tfr_2025']
        if res.get('fertility_evidence') is not None:
            self.fertility_evidence = res['fertility_evidence']
        self.R += 1


def run_scenarios(ctx, hier, scenarios, runs, seed, log=print):
    stores = {}
    for si, name in enumerate(scenarios):
        cfg = ctx.a['scenarios'][name]
        st = Store(ctx.n, runs)
        t0 = time.time()
        for r in range(runs):
            rng = np.random.default_rng([seed, r])          # same draws in every scenario (common random numbers)
            p = SM.draw_run(ctx, rng, name)
            idx = hier.sample_indices(rng, 1)[:, 0]
            res = SM.simulate(ctx, p, cfg, hier, idx)
            st.add(r, res, p)
        log(f'  {name}: {runs} runs in {time.time() - t0:.0f}s')
        stores[name] = st
    return stores


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--runs', type=int, default=None)
    ap.add_argument('--scenarios', default='all')
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--quick', action='store_true', help='8 runs per scenario (a fast check, not for results)')
    args = ap.parse_args(argv)
    t0 = time.time()
    ctx = SM.Context()
    a = ctx.a
    runs = 8 if args.quick else (args.runs or a['runs_per_scenario'])
    seed = a['random_seed'] if args.seed is None else args.seed
    scenarios = list(a['scenarios']) if args.scenarios == 'all' else args.scenarios.split(',')
    print(f'Step 7 forecast: {ctx.n} countries, start state {ctx.start_source}')
    print('Inputs:', json.dumps({k: v['status'] for k, v in D.catalogue().items()}))
    hier, wins = prepare(ctx)
    print(f'Switching fit: delta={hier.H[0]}, beta_d={hier.H[1]}, tau_u={hier.H[2]}; evidence windows {len(wins)}; '
          f"survey cells {0 if ctx.switch_obs is None else len(ctx.switch_obs)}")
    if ctx.selectivity is not None:
        print(f"Religion of migrants: affinity kappa={ctx.selectivity.get('kappa', 0):.2f}, minority lambda="
              f"{ctx.selectivity['lam']:.2f}, rmse {ctx.selectivity['rmse_pp']:.2f} pp "
              f"(migrants mirror origin: {ctx.selectivity['rmse_mirror_pp']:.2f} pp)")
    print(f'Running {len(scenarios)} scenarios x {runs} runs (seed {seed}) ...')
    stores = run_scenarios(ctx, hier, scenarios, runs, seed)
    OUT.mkdir(parents=True, exist_ok=True)
    ref = a['reference_scenario'] if a['reference_scenario'] in stores else scenarios[0]
    ct = pd.concat([T.country_table(ctx, s, st) for s, st in stores.items()], ignore_index=True)
    wt = pd.concat([T.world_table(s, st) for s, st in stores.items()], ignore_index=True)
    ct.to_csv(OUT / 'country_year_by_scenario.csv', index=False)
    ct[ct.scenario.eq(ref)].drop(columns='scenario').to_csv(OUT / 'country_year_uncertainty.csv', index=False)
    wt.to_csv(OUT / 'global_share_by_scenario.csv', index=False)
    wt[wt.scenario.eq(ref)].drop(columns='scenario').to_csv(OUT / 'global_share_uncertainty.csv', index=False)
    pd.concat([T.components_table(ctx, s, st) for s, st in stores.items()], ignore_index=True).to_csv(
        OUT / 'components_country_period.csv', index=False)
    wc = pd.concat([T.world_components(s, st) for s, st in stores.items()], ignore_index=True)
    wc.to_csv(OUT / 'components_world_period.csv', index=False)
    pd.concat([T.migration_table(ctx, s, st) for s, st in stores.items()], ignore_index=True).to_csv(
        OUT / 'migration_country_period.csv', index=False)
    T.corridors(ctx, ref, stores[ref]).to_csv(OUT / 'migration_corridors_reference.csv', index=False)
    dc = pd.concat([T.dominant_change(ctx, s, st) for s, st in stores.items()], ignore_index=True)
    dc.to_csv(OUT / 'dominant_change.csv', index=False)
    us = T.uncertainty_split(wt)
    us.to_csv(OUT / 'uncertainty_model_vs_scenario.csv', index=False)
    sc = hier.survey_level['table'] if hier.survey_level is not None else T.switching_check(ctx, hier)
    sc.to_csv(OUT / 'switching_check_vs_pew.csv', index=False)
    ES.switching_table(ctx, hier).to_csv(OUT / 'switching_rates_2020.csv', index=False)
    prov = T.provenance(ctx, hier, wins)
    prov.to_csv(OUT / 'parameter_provenance.csv', index=False)
    params = pd.concat([pd.DataFrame(st.params).assign(scenario=s) for s, st in stores.items()], ignore_index=True)
    params.to_csv(OUT / 'run_parameters.csv', index=False)
    T.run_outcomes(ctx, stores).to_csv(OUT / 'run_outcomes.csv', index=False)
    T.group_fertility(ctx, ref, stores[ref]).to_csv(OUT / 'group_fertility_2020_2025.csv', index=False)
    T.fertility_evidence(ctx).to_csv(OUT / 'fertility_evidence.csv', index=False)
    T.shift_share(ct, ref).to_csv(OUT / 'world_share_shift_share.csv', index=False)
    T.holders(ct, ref).to_csv(OUT / 'adherents_by_country.csv', index=False)
    bench = T.pew_2015_benchmark(ctx, ct, ref)
    if len(bench):
        bench.to_csv(OUT / 'benchmark_vs_pew2015.csv', index=False)
    skill = T.pew_2015_forecast_skill(ctx)
    if len(skill):
        skill.to_csv(OUT / 'benchmark_pew2015_skill.csv', index=False)
    diag = pd.concat([pd.DataFrame(st.diag).assign(scenario=s) for s, st in stores.items()], ignore_index=True)
    wpop = pd.DataFrame([{'scenario': s, 'year': y, 'mean_world_population': float(st.pop[:st.R, j].sum(1).mean())}
                         for s, st in stores.items() for j, y in enumerate(YEARS)])
    wpop.to_csv(OUT / 'world_population_by_scenario.csv', index=False)
    rep = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), runtime_seconds=round(time.time() - t0, 1),
               countries=ctx.n, dropped_countries=ctx.dropped, start_state=ctx.start_source, inputs=D.catalogue(),
               runs_per_scenario=runs, seed=seed, scenarios={s: a['scenarios'][s]['label'] for s in scenarios},
               reference_scenario=ref,
               switching_fit=dict(delta=hier.H[0], beta_d=hier.H[1], tau_u=hier.H[2],
                                  net_noise_scale_pp=None if hier.net_scale is None else [round(100 * float(x), 3) for x in hier.net_scale],
                                  median_posterior_ess=float(np.median(hier.effective_sample_size())),
                                  latent_draws=hier.M),
               switching_survey_level=None if hier.survey_level is None else dict(
                   logit_shift_by_religion={r.religion: float(r.logit_shift) for r in hier.survey_level['table'].itertuples()},
                   note='survey level = fitted rates shifted so adults 18-54 match Pew 2025 (117 countries); runs mix the two levels'),
               emigration_selectivity=None if ctx.selectivity is None else dict(
                   model=ctx.selectivity.get('kind', 'propensity'), kappa=ctx.selectivity.get('kappa'),
                   lam=ctx.selectivity['lam'], rmse_pp=ctx.selectivity['rmse_pp'],
                   rmse_if_mirror_origin_pp=ctx.selectivity['rmse_mirror_pp'],
                   residuals_pp=ctx.selectivity['residuals']),
               diagnostics=dict(mean_abs_log_rescale_to_2100=float(diag.rescale_mean_abs_log.mean()),
                                migration_shortfall_persons_mean=float(diag.migration_shortfall_persons.mean())),
               cautions=['Shares after 2100 rest on stated long-run assumptions; 2500 and 3026 are speculative scenarios.',
                         'Within-scenario bands are parameter and model uncertainty under that scenario, not calibrated probabilities.',
                         'The Folk/Traditional vs Other split of Pew data is a WRP-based proxy; WRP and Pew classify China differently.',
                         'Fertility gaps come from published world, regional or country figures (fertility_evidence.csv); the world and regional tiers are damped because a ratio measured across countries is not a within-country ratio.',
                         'The religion of migrants comes from a two-parameter model (minority effect, destination affinity) calibrated to '
                         'Pew aggregates; corridor-level religion of migrants is not observed.'])
    (OUT / 'projection_report.json').write_text(json.dumps(rep, indent=2, default=float), encoding='utf8')
    print('\nWorld shares (reference scenario: %s), %%:' % ref)
    piv = wt[wt.scenario.eq(ref) & wt.year.isin(TARGET_YEARS)].pivot(index='year', columns='religion', values='mean') * 100
    print(piv[CATS].round(1).to_string())
    print('\nModel vs scenario uncertainty (world shares, pp):')
    print(us[us.religion.isin(['Christianity', 'Islam', 'Unaffiliated', 'Hinduism'])].round(2).to_string(index=False))
    ss = T.shift_share(ct, ref)
    print('\nWhere world-share change comes from, 2020-2100 (percentage points):')
    print(ss[ss.year.eq(2100)][['religion', 'change_pp', 'within_country_pp', 'population_weighting_pp']]
          .round(2).to_string(index=False))
    print('\nSwitching levels against Pew (adults 18-54, left per 100 raised); runs mix the two levels:')
    print(sc.round(1).to_string(index=False))
    print(f'\nWrote {OUT} in {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
