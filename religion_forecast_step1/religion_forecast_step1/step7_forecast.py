"""Step 7 forecast: religious composition of every country, 2020-3030, under eight scenarios.

Run (from this folder, Windows PowerShell):
    .\\.venv\\Scripts\\python.exe step7_fetch_data.py         # optional data (once)
    .\\.venv\\Scripts\\python.exe step7_validate.py           # history tests (writes data/validation_step7)
    .\\.venv\\Scripts\\python.exe step7_forecast.py           # this script (runs from step7_assumptions.json)
    .\\.venv\\Scripts\\python.exe verify_step7.py
    .\\.venv\\Scripts\\python.exe step7_make_maps.py
Options: --runs N (per scenario), --scenarios a,b, --seed S, --quick (8 runs, for a fast check).
Writes data/forecasts_step7/ (git-ignored). Earlier steps' outputs are not touched.

What is fitted before the runs
  religion of migrants    minority effect and destination affinity calibrated to Pew's published
                          religious composition of migrants (needs UN bilateral stocks; otherwise
                          migrants mirror their origin)
  switching               empirical Bayes on (a) what demographic hindcasts of WRP 1950-2010 and, when
                          available, Pew 2010-2020 leave unexplained and (b) verified survey cells in
                          step7_inputs/switching_lifetime_observed.csv
Each run draws every uncertain parameter (ranges in step7_assumptions.json), one posterior switching
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

import step7_data as D
import step7_engine as E
import step7_estimate as ES
import step7_model as SM
import step7_switching as SW

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'forecasts_step7'
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


# --------------------------------------------------------------------------- summaries
def q(x, a, axis=0):
    return np.quantile(x, a, axis=axis)


def country_table(ctx, name, st):
    rows = []
    R = st.R
    div = E.gini_simpson(st.sh[:R].astype(float))                  # [R, Y, n]
    eff = E.effective_number(st.sh[:R].astype(float))
    dom = st.sh[:R].argmax(-1)                                     # [R, Y, n]
    mean_sh = st.sh[:R].mean(0)
    for j, y in enumerate(YEARS):
        modal = np.array([np.bincount(dom[:, j, i], minlength=K).argmax() for i in range(ctx.n)])
        agree = (dom[:, j, :] == modal[None, :]).mean(0)
        for i, c in enumerate(ctx.ids):
            row = {'scenario': name, 'country_id': c, 'year': y, 'mean_population': float(st.pop[:R, j, i].mean()),
                   'most_likely_dominant': CATS[modal[i]], 'dominant_agreement_fraction': float(agree[i]),
                   'mean_dominant': CATS[int(mean_sh[j, i].argmax())],
                   'diversity_gini_simpson_mean': float(div[:, j, i].mean()),
                   'diversity_gini_simpson_q05': float(q(div[:, j, i], .05)),
                   'diversity_gini_simpson_q95': float(q(div[:, j, i], .95)),
                   'effective_number_mean': float(eff[:, j, i].mean()),
                   'foreign_born_share_mean': float(st.fb[:R, j, i].mean()),
                   'second_generation_share_mean': float(st.g2[:R, j, i].mean())}
            for k, g in enumerate(CATS):
                v = st.sh[:R, j, i, k].astype(float)
                row[f'mean_{g}'] = float(v.mean())
                row[f'q05_{g}'] = float(q(v, .05))
                row[f'q95_{g}'] = float(q(v, .95))
            rows.append(row)
    df = pd.DataFrame(rows)
    m = df[[f'mean_{g}' for g in CATS]].to_numpy()
    df[[f'mean_{g}' for g in CATS]] = m / m.sum(1, keepdims=True)
    return df


def world_table(name, st):
    rows = []
    for j, y in enumerate(STEPS):
        for k, g in enumerate(CATS):
            v = st.world[:st.R, j, k]
            rows.append({'scenario': name, 'year': y, 'religion': g, 'mean': float(v.mean()),
                         'q05': float(q(v, .05)), 'q95': float(q(v, .95))})
    df = pd.DataFrame(rows)
    i3025, i3030 = STEPS.index(3025), STEPS.index(3030)
    for k, g in enumerate(CATS):
        v = 0.8 * st.world[:st.R, i3025, k] + 0.2 * st.world[:st.R, i3030, k]
        df = pd.concat([df, pd.DataFrame([{'scenario': name, 'year': 3026, 'religion': g, 'mean': float(v.mean()),
                                           'q05': float(q(v, .05)), 'q95': float(q(v, .95))}])], ignore_index=True)
    return df.sort_values(['year', 'religion']).reset_index(drop=True)


def components_table(ctx, name, st):
    R = st.R
    rows = []
    for pi, pr in enumerate(SM.PERIODS):
        for i, c in enumerate(ctx.ids):
            for k, g in enumerate(CATS):
                row = {'scenario': name, 'country_id': c, 'period': PERIOD_LABEL[pr], 'religion': g}
                for ci, comp in enumerate(E.COMPONENTS):
                    row[f'persons_{comp}'] = st.cp[pi, i, k, ci] / R
                for si, sub in enumerate(E.SHARE_STEPS):
                    row[f'share_pp_{sub}'] = 100 * st.cs[pi, i, k, si] / R
                row['share_pp_total'] = 100 * st.cs[pi, i, k].sum() / R
                rows.append(row)
    return pd.DataFrame(rows)


def world_components(name, st):
    rows = []
    for pi, pr in enumerate(SM.PERIODS):
        for k, g in enumerate(CATS):
            row = {'scenario': name, 'period': PERIOD_LABEL[pr], 'religion': g}
            for ci, comp in enumerate(E.COMPONENTS):
                row[f'persons_{comp}'] = st.cp[pi, :, k, ci].sum() / st.R
            for si, sub in enumerate(E.SHARE_STEPS):
                row[f'world_share_pp_{sub}'] = 100 * st.ws[pi, k, si] / st.R
            row['world_share_pp_total'] = 100 * st.ws[pi, k].sum() / st.R
            rows.append(row)
    return pd.DataFrame(rows)


def migration_table(ctx, name, st):
    rows = []
    for pi, pr in enumerate(SM.PERIODS):
        for i, c in enumerate(ctx.ids):
            for k, g in enumerate(CATS):
                a, b = st.mig_in[pi, i, k] / st.R, st.mig_out[pi, i, k] / st.R
                if a == 0 and b == 0:
                    continue
                rows.append({'scenario': name, 'period': PERIOD_LABEL[pr], 'country_id': c, 'religion': g,
                             'immigrants': a, 'emigrants': b, 'net': a - b})
    return pd.DataFrame(rows)


def corridors(ctx, name, st, top=400):
    rows = []
    for oi, pr in enumerate(SM.PERIODS[:2]):
        F = st.od[oi] / st.R
        flat = np.argsort(F, axis=None)[::-1][:top]
        for f in flat:
            o, d = np.unravel_index(f, F.shape)
            rows.append({'scenario': name, 'period': PERIOD_LABEL[pr], 'origin': ctx.ids[o], 'destination': ctx.ids[d],
                         'persons': float(F[o, d])})
    return pd.DataFrame(rows)


def dominant_change(ctx, name, st):
    R = st.R
    dom = st.sh[:R].argmax(-1)
    base = dom[:, 0, :]
    rows = []
    for i, c in enumerate(ctx.ids):
        row = {'scenario': name, 'country_id': c, 'dominant_2020': CATS[int(np.bincount(base[:, i], minlength=K).argmax())]}
        first = None
        for y in TARGET_YEARS[1:]:
            j = YEARS.index(y)
            pchg = float((dom[:, j, i] != base[:, i]).mean())
            row[f'prob_changed_by_{y}'] = pchg
            row[f'most_likely_{y}'] = CATS[int(np.bincount(dom[:, j, i], minlength=K).argmax())]
            if first is None and pchg > 0.5:
                first = y
        row['first_target_year_majority_of_runs_changed'] = first
        rows.append(row)
    return pd.DataFrame(rows)


def uncertainty_split(world):
    """Model (within-scenario) versus scenario (between-scenario) uncertainty of world shares."""
    rows = []
    for (y, g), sub in world[world.year.isin(TARGET_YEARS)].groupby(['year', 'religion']):
        rows.append({'year': y, 'religion': g,
                     'within_scenario_band_pp_mean': 100 * float((sub.q95 - sub.q05).mean()),
                     'between_scenario_range_pp': 100 * float(sub['mean'].max() - sub['mean'].min()),
                     'lowest_scenario': sub.loc[sub['mean'].idxmin(), 'scenario'],
                     'highest_scenario': sub.loc[sub['mean'].idxmax(), 'scenario']})
    return pd.DataFrame(rows)


def switching_check(ctx, hier):
    """Fitted lifetime rates (2020 development) turned into Pew's measure for adults 18-54
    ('left per 100 raised'), population-weighted across countries, against Pew's published
    117-country figures. Adults 18-54 have completed only part of their lifetime switching; the share
    completed is taken from the model's age weights and each country's 2020 age structure."""
    z = SW.development_index(ctx.wpp_mean('e0', 2015, 2020), ctx.wpp_mean('tfr', 2015, 2020), ctx.a)
    d, v, a = hier.rates(z, hier.H)
    w = hier.posterior_weights()
    d = np.einsum('nm,nmj->nj', w, d)
    v = np.einsum('nm,nmj->nj', w, v)
    a = (w * a).sum(1)
    age = ctx.age_dist(2020)
    cumw = np.cumsum(np.concatenate([np.zeros(SW.SWITCH_AGES[0]), SW.SWITCH_AGE_WEIGHTS,
                                     np.zeros(E.A - SW.SWITCH_AGES[-1] - 1)]))
    # ages 18-54: age groups 15-19 (2/5 of it) ... 50-54
    wt = age[:, 3:11].copy()
    wt[:, 0] *= 0.4
    frac = (wt * cumw[None, 3:11]).sum(1) / np.maximum(wt.sum(1), 1e-300)
    pop1854 = ctx.wpp_at('pop', 2020) * wt.sum(1)
    rows = []
    tgt = pd.read_csv(D.TRACKED / 'switching_global_targets.csv', comment='#') \
        if (D.TRACKED / 'switching_global_targets.csv').exists() else pd.DataFrame()
    for r in SW.REL + [E.U]:
        g = CATS[r]
        base = pop1854 * ctx.s2020[:, r]
        out = (d[:, SW.REL.index(r)] + v[:, SW.REL.index(r)]) if r != E.U else a
        model_left = 100 * float((base * frac * out).sum() / max(base.sum(), 1e-300))
        pew = tgt[(tgt.religion == g) & (tgt.measure == 'left_per_100_raised')] if len(tgt) else []
        rows.append({'religion': g, 'model_left_per_100_raised_18_54': model_left,
                     'pew_left_per_100_raised_18_54': float(pew.value.iloc[0]) if len(pew) else np.nan,
                     'model_lifetime_outflow_popweighted': 100 * float((base * out).sum() / max(base.sum(), 1e-300)),
                     'share_of_lifetime_switching_completed_by_18_54': float((base * frac).sum() / max(base.sum(), 1e-300))})
    return pd.DataFrame(rows)


def provenance(ctx, hier, wins):
    a = ctx.a
    rows = []

    def add(name, value, status, source):
        rows.append({'parameter': name, 'value': value, 'status': status, 'source_or_reason': source})
    add('start shares 2020', ctx.start_source, 'observed', 'Pew 2020 (Folk/Other split by WRP proxy)')
    add('national fertility, mortality, net migration to 2100', 'WPP 2024 medium', 'observed/projected', 'UN WPP 2024')
    for k, v in D.catalogue().items():
        add(f'input {k}', v['detail'], v['status'], 'step7_data.py')
    add('switching hyperparameters (delta, beta_d, tau_u)', str(hier.H), 'estimated', 'empirical Bayes, step7_switching')
    add('switching evidence windows', ', '.join(f"{w['source']} {w['start']}-{w['end']}" for w in wins), 'observed', 'WRP, Pew')
    if ctx.switch_obs is not None:
        add('survey switching cells', f'{len(ctx.switch_obs)} cells, {ctx.switch_obs.country_id.nunique()} countries',
            'observed', 'step7_inputs/switching_lifetime_observed.csv')
    if ctx.selectivity is not None:
        add('religion of migrants: destination affinity kappa, minority effect lambda',
            f"kappa={ctx.selectivity.get('kappa', 0):.2f}; lambda={ctx.selectivity['lam']:.2f}",
            'estimated', f"grid fit to Pew's published religious composition of migrants (19 targets), rmse "
                         f"{ctx.selectivity['rmse_pp']:.2f} pp (migrants mirroring origin: {ctx.selectivity['rmse_mirror_pp']:.2f})")

    def walk(prefix, obj):
        if isinstance(obj, dict):
            st = obj.get('status')
            if st is not None and ('range' in obj or 'value' in obj or 'by_group' in obj):
                val = obj.get('range', obj.get('value', obj.get('by_group')))
                add(prefix, json.dumps(val), st, obj.get('note', obj.get('source', '')))
            for kk, vv in obj.items():
                if isinstance(vv, dict) and kk not in ('scenarios',):
                    walk(f'{prefix}.{kk}' if prefix else kk, vv)
    walk('', {k: v for k, v in a.items() if k != 'scenarios'})
    for name, cfg in a['scenarios'].items():
        add(f'scenario {name}', json.dumps({k: cfg[k] for k in ('switching', 'migration', 'fertility')}), 'scenario assumption',
            cfg['label'])
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--runs', type=int, default=None)
    ap.add_argument('--scenarios', default='all')
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--quick', action='store_true', help='8 runs per scenario (a fast check, not for results)')
    args = ap.parse_args()
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
    ct = pd.concat([country_table(ctx, s, st) for s, st in stores.items()], ignore_index=True)
    wt = pd.concat([world_table(s, st) for s, st in stores.items()], ignore_index=True)
    ct.to_csv(OUT / 'country_year_by_scenario.csv', index=False)
    ct[ct.scenario.eq(ref)].drop(columns='scenario').to_csv(OUT / 'country_year_uncertainty.csv', index=False)
    wt.to_csv(OUT / 'global_share_by_scenario.csv', index=False)
    wt[wt.scenario.eq(ref)].drop(columns='scenario').to_csv(OUT / 'global_share_uncertainty.csv', index=False)
    pd.concat([components_table(ctx, s, st) for s, st in stores.items()], ignore_index=True).to_csv(
        OUT / 'components_country_period.csv', index=False)
    wc = pd.concat([world_components(s, st) for s, st in stores.items()], ignore_index=True)
    wc.to_csv(OUT / 'components_world_period.csv', index=False)
    pd.concat([migration_table(ctx, s, st) for s, st in stores.items()], ignore_index=True).to_csv(
        OUT / 'migration_country_period.csv', index=False)
    corridors(ctx, ref, stores[ref]).to_csv(OUT / 'migration_corridors_reference.csv', index=False)
    dc = pd.concat([dominant_change(ctx, s, st) for s, st in stores.items()], ignore_index=True)
    dc.to_csv(OUT / 'dominant_change.csv', index=False)
    us = uncertainty_split(wt)
    us.to_csv(OUT / 'uncertainty_model_vs_scenario.csv', index=False)
    sc = hier.survey_level['table'] if hier.survey_level is not None else switching_check(ctx, hier)
    sc.to_csv(OUT / 'switching_check_vs_pew.csv', index=False)
    ES.switching_table(ctx, hier).to_csv(OUT / 'switching_rates_2020.csv', index=False)
    prov = provenance(ctx, hier, wins)
    prov.to_csv(OUT / 'parameter_provenance.csv', index=False)
    params = pd.concat([pd.DataFrame(st.params).assign(scenario=s) for s, st in stores.items()], ignore_index=True)
    params.to_csv(OUT / 'run_parameters.csv', index=False)
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
                         'Group fertility gaps are damped Pew global ratios unless religion_fertility_observed.csv supplies a country.',
                         'The religion of migrants comes from a two-parameter model (minority effect, destination affinity) calibrated to '
                         'Pew aggregates; corridor-level religion of migrants is not observed.'])
    (OUT / 'step7_report.json').write_text(json.dumps(rep, indent=2, default=float), encoding='utf8')
    print('\nWorld shares (reference scenario: %s), %%:' % ref)
    piv = wt[wt.scenario.eq(ref) & wt.year.isin(TARGET_YEARS)].pivot(index='year', columns='religion', values='mean') * 100
    print(piv[CATS].round(1).to_string())
    print('\nModel vs scenario uncertainty (world shares, pp):')
    print(us[us.religion.isin(['Christianity', 'Islam', 'Unaffiliated', 'Hinduism'])].round(2).to_string(index=False))
    print('\nSwitching levels against Pew (adults 18-54, left per 100 raised); runs mix the two levels:')
    print(sc.round(1).to_string(index=False))
    print(f'\nWrote {OUT} in {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
