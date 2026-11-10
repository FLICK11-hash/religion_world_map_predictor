"""Projection: religious composition of every country, 2020-3030, under eight scenarios.

    python run.py project                  40 runs per scenario (config/assumptions.json)
    python run.py project --runs 12        fewer runs
    python run.py project --scenarios stabilising,high_retention
    python run.py project --quick          8 runs, to check the plumbing, not for results

Writes data/projections/ (git-ignored).

Fitted once, before the runs
  religion of migrants   minority effect and destination affinity calibrated to Pew's published
                         religious composition of migrants (needs UN bilateral stocks)
  switching              empirical Bayes on (a) what demographic hindcasts of World Religion Project
                         decades 1950-2010 (and Pew 2010-2020 when available) leave unexplained and
                         (b) the verified survey rows in inputs/switching_lifetime_observed.csv
  forecast errors        the error model fitted by run.py backtest (religion_forecast.errors);
                         built here if the backtest has not been run

Each run draws every uncertain parameter (ranges in config/assumptions.json), one posterior
switching draw per country, and the weight given to the survey level of switching. Run r uses the
same draws in every scenario (common random numbers), so differences between scenarios come from
the scenario assumptions alone. Three kinds of uncertainty are reported separately:
  q05/q95    the spread of the runs: parameter uncertainty inside one scenario
  pi05/pi95  predictive quantiles to 2100: the runs plus the forecast errors of the past
  scenarios  the spread of scenario means: assumption uncertainty
Years after 2100 rest on stated long-run assumptions and are exploratory, with no predictive
intervals; 2500 and 3026 show what those assumptions imply, not what will happen.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from religion_forecast import calibration as ES
from religion_forecast import config
from religion_forecast import datasets as D
from religion_forecast import engine as E
from religion_forecast import errors as ER
from religion_forecast import model as SM
from religion_forecast import switching as SW
from religion_forecast import tables as T

OUT = config.PROJECTIONS
CATS, K = E.CATS, E.K
TARGET_YEARS = [2020, 2050, 2100, 2200, 2500, 3026]
YEARS = sorted(set(SM.KEEP_YEARS) | {3026})
STEPS = list(range(2020, 3031, 5))
PERIOD_LABEL = {pr: f'{pr[0]}-{pr[1]}' for pr in SM.PERIODS}


def prepare(ctx, log=print):
    """Calibrations shared by every run: the religion of migrants, and the switching fit as an
    ensemble of replicate fits (switching.Ensemble). The fit is cached in data/projections so that
    run.py experiments reuses exactly the fit the projection used."""
    import hashlib
    import pickle
    ctx.selectivity = ES.calibrate_affinity(ctx)
    p0 = ES.central_params(ctx)
    wins = ES.no_switching_hindcasts(ctx, p0, ES.windows(ctx))
    sw = ctx.a['switching']
    replicates = int(sw.get('replicate_fits', {}).get('value', 3))
    key = hashlib.sha256(json.dumps([sw, ctx.start_source, ctx.ids, replicates], sort_keys=True, default=str)
                         .encode()).hexdigest()[:16]
    cache = OUT / 'switching_fit.pkl'
    if cache.exists():
        try:
            saved = pickle.loads(cache.read_bytes())
            if saved.get('key') == key:
                log(f'Switching fit: reusing {cache.relative_to(config.PROJECT)}')
                return saved['ensemble'], wins
        except Exception:                                    # a stale or unreadable cache is refitted
            pass
    members = []
    for i in range(replicates):
        t0 = time.time()
        h = ES.fit_switching(ctx, wins, use_survey=True, seed=7 + i)
        h.survey_level = ES.calibrate_survey_level(ctx, h)
        members.append(h)
        log(f'  switching fit {i + 1}/{replicates}: delta={h.H[0]:.3f}, beta_d={h.H[1]:.3f}, tau_u={h.H[2]:.3f} '
            f'({time.time() - t0:.0f}s)')
    ens = SW.Ensemble(members)
    OUT.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(pickle.dumps({'key': key, 'ensemble': ens}))
    return ens, wins


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
            h = hier.member(r)
            idx = h.sample_indices(rng, 1)[:, 0]
            res = SM.simulate(ctx, p, cfg, h, idx)
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
    print(f'Projection: {ctx.n} countries, start state {ctx.start_source}')
    print('Inputs:', json.dumps({k: v['status'] for k, v in D.catalogue().items()}))
    hier, wins = prepare(ctx)
    sd = hier.H_spread()
    print(f'Switching fit ({len(hier.members)} replicates): delta={hier.H[0]:.3f} (sd {sd[0]:.3f}), '
          f'beta_d={hier.H[1]:.3f} (sd {sd[1]:.3f}), tau_u={hier.H[2]:.3f} (sd {sd[2]:.3f}); evidence windows '
          f"{len(wins)}; survey cells {0 if ctx.switch_obs is None else len(ctx.switch_obs)}")
    if ctx.selectivity is not None:
        print(f"Religion of migrants: affinity kappa={ctx.selectivity.get('kappa', 0):.2f}, minority lambda="
              f"{ctx.selectivity['lam']:.2f}, rmse {ctx.selectivity['rmse_pp']:.2f} pp "
              f"(migrants mirror origin: {ctx.selectivity['rmse_mirror_pp']:.2f} pp)")
    print(f'Running {len(scenarios)} scenarios x {runs} runs (seed {seed}) ...')
    stores = run_scenarios(ctx, hier, scenarios, runs, seed)
    error_model = ER.load_or_build(ctx)
    T.attach_predictive(stores, error_model, seed)
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
    T.corridor_concentration(ctx, ref, stores[ref]).to_csv(OUT / 'migration_corridor_concentration.csv', index=False)
    dc = pd.concat([T.dominant_change(ctx, s, st) for s, st in stores.items()], ignore_index=True)
    dc.to_csv(OUT / 'dominant_change.csv', index=False)
    us = T.uncertainty_split(wt)
    us.to_csv(OUT / 'uncertainty_model_vs_scenario.csv', index=False)
    sc = hier.survey_level['table'] if hier.survey_level is not None else T.switching_check(ctx, hier.members[0])
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
               forecast_error_model=dict(b=error_model['b'], beta=error_model['beta'],
                                         blocks=[blk['label'] for blk in error_model['blocks']],
                                         note='predictive intervals (pi*) to 2100 add resampled past forecast errors '
                                              'to every run; see religion_forecast/errors.py'),
               switching_fit=dict(delta=hier.H[0], beta_d=hier.H[1], tau_u=hier.H[2],
                                  replicates=[dict(delta=m.H[0], beta_d=m.H[1], tau_u=m.H[2],
                                                   log_marginal=m.log_marginal_value) for m in hier.members],
                                  replicate_sd=dict(zip(('delta', 'beta_d', 'tau_u'), hier.H_spread())),
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
               cautions=['Shares after 2100 rest on stated long-run assumptions; 2500 and 3026 are exploratory scenarios without predictive intervals.',
                         'q05/q95 are parameter uncertainty only; use pi05/pi95 (to 2100) for predictive intervals.',
                         'The Folk/Traditional vs Other split of Pew data is a WRP-based proxy; WRP and Pew classify China differently.',
                         'Fertility gaps come from published world, regional or country figures (fertility_evidence.csv); the world and regional tiers are damped because a ratio measured across countries is not a within-country ratio.',
                         'The religion of migrants comes from a two-parameter model (minority effect, destination affinity) calibrated to '
                         'Pew aggregates; corridor-level religion of migrants is not observed.'])
    (OUT / 'projection_report.json').write_text(json.dumps(rep, indent=2, default=float), encoding='utf8')
    print('\nWorld shares (reference scenario: %s), %%:' % ref)
    piv = wt[wt.scenario.eq(ref) & wt.year.isin(TARGET_YEARS)].pivot(index='year', columns='religion', values='mean') * 100
    print(piv[CATS].round(1).to_string())
    show = wt[wt.scenario.eq(ref) & wt.year.isin([2050, 2100])].copy()
    show[['mean', 'pi05', 'pi95']] *= 100
    print('\nPredictive 90% intervals of world shares (%):')
    print(show.pivot(index='religion', columns='year', values=['mean', 'pi05', 'pi95']).round(1).to_string())
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
