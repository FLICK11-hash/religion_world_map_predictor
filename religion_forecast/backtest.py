"""Step 7 validation: forward-chaining history tests of every mechanism against persistence.

Run:  .\\.venv\\Scripts\\python.exe run.py backtest
Writes data/validation/ (git-ignored) and prints a summary.

Windows are 10-year periods with observed religious shares at both ends: WRP 1950-1960 ... 2000-2010
(WRP categories) and, when data/processed/pew_harmonized.csv exists, Pew 2010-2020. A window is
predicted only with what was known before it: switching rates and the residual learner are fitted on
windows that END no later than the test window STARTS, and their weights (switching strength,
residual weight) are chosen on earlier test windows only. WPP demography for the window itself is
used (retrospective: WPP 2024 estimates, not the projections available at the time).

Models
  persistence              shares unchanged
  demography               births, deaths, ageing (religion-specific fertility, generations), no migration
  demography_migration     + conserving origin-destination migration
  + switching              + hierarchical switching (posterior mean), strength chosen out of sample
  + switching + residual   + ridge residual learner, weight chosen out of sample
  + momentum               demography_migration + last window's residual carried forward (as in 5E)
Scores: population-weighted total-variation error (pp), country-mean TV, MAE, dominant-religion
accuracy, and detection of dominant-religion changes.

Migration volumes (foreign_born_check): starting from the UN 1990 foreign-born stocks, simulate
1990-2020 with WPP demography and the migration model (no switching) at the low, middle and high end
of the circulation range, and compare each country's 2020 foreign-born share with the UN 2020 stocks.
Baseline: the 1990 foreign-born share unchanged. Writes migration_foreign_born_check.csv.
Interval calibration (interval_calibration): the full Monte Carlo on each history window, measuring
what fraction of observed shares fall inside the model's 50/80/90% predictive intervals.
Corridors (corridor_check): the same 1990-2020 run at several margin softness values (margin_rho);
simulated flows into each of the 25 largest destinations are compared with the growth of the UN
bilateral stocks 1990-2020 (origin mix: correlation and total-variation distance). Writes
migration_corridor_check.csv. Run only the two migration checks with --foreign-born-only.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from religion_forecast import engine as E
from religion_forecast import calibration as ES
from religion_forecast import model as SM
from religion_forecast import residual as RL
from religion_forecast import config

OUT = config.VALIDATION
CATS, K = E.CATS, E.K
STRENGTHS = [0.0, 0.5, 1.0]
RESID_WEIGHTS = [0.0, 0.25, 0.5, 1.0]
RESID_ALPHAS = [1.0, 10.0, 100.0]


def score(pred, obs, s0, mask, pop):
    m = mask & np.isfinite(obs).all(1)
    p, o, s = pred[m], obs[m], s0[m]
    tv = 0.5 * np.abs(p - o).sum(1)
    w = pop[m]
    dp, do, ds = p.argmax(1), o.argmax(1), s.argmax(1)
    changed = do != ds
    return dict(n=int(m.sum()), popw_tv_pp=100 * float(np.average(tv, weights=w)), mean_tv_pp=100 * float(tv.mean()),
                mae_pp=100 * float(np.abs(p - o).mean()), dominant_accuracy=float((dp == do).mean()),
                changed_true=int(changed.sum()), changed_hit=int((changed & (dp == do)).sum()),
                false_alarm=int((~changed & (dp != ds)).sum()),
                **{f'err_pp_{c}': 100 * float(np.average(p[:, k] - o[:, k], weights=w)) for k, c in enumerate(CATS)})


def make_context(bilateral=True, age_data=True, selectivity=True):
    ctx = SM.Context(bilateral=bilateral, age_data=age_data)
    if selectivity:
        ctx.selectivity = ES.calibrate_affinity(ctx)
    return ctx


def ablations(include_pew=True):
    """Does each added dataset improve the history tests? Demography and demography+migration
    errors for data variants (switching is not involved, so no refitting is needed)."""
    variants = [('WPP indicators only (as Step 5D/5E)', dict(bilateral=False, age_data=False, selectivity=False)),
                ('+ WPP age structure by sex', dict(bilateral=False, age_data=True, selectivity=False)),
                ('+ UN bilateral migrant stocks', dict(bilateral=True, age_data=True, selectivity=False)),
                ('+ religion of migrants calibrated to Pew', dict(bilateral=True, age_data=True, selectivity=True))]
    rows = []
    for label, opt in variants:
        ctx = make_context(**opt)
        p = ES.central_params(ctx)
        for mig in (False, True):
            wins = ES.no_switching_hindcasts(ctx, p, ES.windows(ctx, (1970, 1980, 1990, 2000), include_pew), migration=mig)
            for w in wins:
                pop = ctx.wpp_at('pop', w['start'])
                sc = score(w['pred'], w['s1'], w['s0'], w['mask'], pop)
                ps = score(w['s0'], w['s1'], w['s0'], w['mask'], pop)
                rows.append({'data_variant': label, 'model': 'demography_migration' if mig else 'demography',
                             'window': f"{w['source']} {w['start']}-{w['end']}", 'source': w['source'], 'start': w['start'],
                             'popw_tv_pp': sc['popw_tv_pp'], 'persistence_popw_tv_pp': ps['popw_tv_pp'],
                             'mean_tv_pp': sc['mean_tv_pp']})
    return pd.DataFrame(rows)


def run(include_pew=True, quick=False, ctx=None):
    ctx = ctx or make_context()
    p = ES.central_params(ctx)
    starts = (1950, 1960, 1970, 1980, 1990, 2000)
    wins = ES.no_switching_hindcasts(ctx, p, ES.windows(ctx, starts, include_pew), migration=True)
    wins_nomig = ES.no_switching_hindcasts(ctx, p, ES.windows(ctx, starts, include_pew), migration=False)
    tests = [w for w in wins if w['start'] >= 1970]
    rows, fits, sel_rows = [], [], []
    prev_resid = {}
    hist = {'switch': [], 'resid': [], 'start': []}   # per earlier test window: error by option
    for wi, w in enumerate(wins):
        if wi > 0:
            prev_resid[w['start']] = wins[wi - 1]['resid'] if wins[wi - 1]['end'] <= w['start'] else None
    for w in tests:
        t = w['start']
        pop = ctx.wpp_at('pop', t)
        train = [x for x in wins if x['end'] <= t]
        hier = ES.fit_switching(ctx, train, use_survey=False) if len(train) >= 2 else None
        fits.append({'test_window': f"{w['source']} {t}-{w['end']}", 'train_windows': len(train),
                     'delta': None if hier is None else hier.H[0], 'beta_d': None if hier is None else hier.H[1],
                     'tau_u': None if hier is None else hier.H[2]})
        nm = next(x for x in wins_nomig if x['start'] == t and x['source'] == w['source'])
        base = w['pred']
        eff = ES.expected_switch_effect(hier, w) if hier is not None else np.zeros_like(base)
        preds = {'persistence': w['s0'], 'demography': nm['pred'], 'demography_migration': base}
        # switching strength: chosen on earlier test windows (1.0 before any history exists)
        opt_s = {s: RL.apply(base, s * eff) for s in STRENGTHS}
        if hist['switch']:
            tot = {s: np.mean([h[s] for h in hist['switch']]) for s in STRENGTHS}
            s_star = min(STRENGTHS, key=lambda s: tot[s])
        else:
            s_star = 1.0
        for s in STRENGTHS:
            preds[f'switching_strength_{s:g}'] = opt_s[s]
        preds['demography_migration_switching'] = opt_s[s_star]
        # residual learner trained on earlier windows' residuals after switching (same strength)
        best_r = {}
        Xtr, Ytr = [], []
        for x in train:
            hx = hier
            ex = ES.expected_switch_effect(hx, x) if hx is not None else 0.0
            after = RL.apply(x['pred'], s_star * ex)
            m = x['mask']
            Xtr.append(RL.features(ctx, x, prev_resid.get(x['start']))[m])
            Ytr.append((np.nan_to_num(x['s1']) - after)[m])
        Xte = RL.features(ctx, w, prev_resid.get(t))
        resid_opts = {}
        if Xtr and sum(len(a) for a in Xtr) > 30:
            X, Y = np.vstack(Xtr), np.vstack(Ytr)
            for al in RESID_ALPHAS:
                model = RL.Ridge(al).fit(X, Y)
                d = model.predict(Xte)
                for lw in RESID_WEIGHTS:
                    resid_opts[(al, lw)] = RL.apply(opt_s[s_star], lw * d)
        else:
            resid_opts[(10.0, 0.0)] = opt_s[s_star]
        if hist['resid']:
            keys = set.intersection(*[set(h) for h in hist['resid']]) & set(resid_opts)
            r_star = min(keys, key=lambda k: np.mean([h[k] for h in hist['resid']])) if keys else (10.0, 0.0)
        else:
            r_star = (10.0, 0.0)
        preds['demography_migration_switching_residual'] = resid_opts.get(r_star, opt_s[s_star])
        last = prev_resid.get(t)
        preds['demography_migration_momentum'] = RL.apply(base, 0.0 if last is None else last) if last is not None else base
        for name, pr in preds.items():
            rows.append({'window': f"{w['source']} {t}-{w['end']}", 'source': w['source'], 'start': t, 'model': name,
                         **score(pr, w['s1'], w['s0'], w['mask'], pop)})
        sel_rows.append({'window': f"{w['source']} {t}-{w['end']}", 'switch_strength_used': s_star,
                         'residual_alpha_used': r_star[0], 'residual_weight_used': r_star[1]})
        hist['switch'].append({s: score(opt_s[s], w['s1'], w['s0'], w['mask'], pop)['popw_tv_pp'] for s in STRENGTHS})
        hist['start'].append(t)
        hist['resid'].append({k: score(v, w['s1'], w['s0'], w['mask'], pop)['popw_tv_pp'] for k, v in resid_opts.items()})
    by = pd.DataFrame(rows)
    # best option on all test windows, and on the windows whose switching fit had 4+ decades of training
    sw_tot = {s: np.mean([h[s] for h in hist['switch']]) for s in STRENGTHS}
    recent = [h for h, t0 in zip(hist['switch'], hist['start']) if t0 >= 1990]
    sw_rec = {s: np.mean([h[s] for h in recent]) for s in STRENGTHS} if recent else {}
    keys = set.intersection(*[set(h) for h in hist['resid']])
    rs_tot = {k: np.mean([h[k] for h in hist['resid']]) for k in keys}
    choice = {'switching_strength_best_all_windows': min(STRENGTHS, key=lambda s: sw_tot[s]),
              'switching_strength_scores_popw_tv_pp': {str(k): v for k, v in sw_tot.items()},
              'switching_strength_best_1990_2010': min(sw_rec, key=lambda s: sw_rec[s]) if sw_rec else None,
              'switching_strength_scores_1990_2010_popw_tv_pp': {str(k): v for k, v in sw_rec.items()},
              'residual': dict(zip(('alpha', 'weight'), min(rs_tot, key=lambda k: rs_tot[k]))),
              'residual_scores_popw_tv_pp': {f'alpha={k[0]:g},weight={k[1]:g}': v for k, v in rs_tot.items()}}
    return ctx, by, pd.DataFrame(fits), pd.DataFrame(sel_rows), choice


def foreign_born_check(ctx, start=1990, end=2020):
    """Simulated vs UN foreign-born share of each country in `end`, from the UN stocks of `start`."""
    from religion_forecast import datasets as D
    if ctx.stock_df is None:
        return None
    S0, y0 = D.stock_matrix(ctx.stock_df, ctx.ids, start)
    S1, y1 = D.stock_matrix(ctx.stock_df, ctx.ids, end)
    if S0 is None or y0 != start or y1 != end:
        return None
    pop = ctx.wpp_at('pop', end)
    fb_un = np.minimum(S1.sum(0), 0.85 * pop) / pop
    w = pop / pop.sum()
    p = ES.central_params(ctx)
    lo, hi = ctx.a['migration']['turnover_per_year']['range']
    rows, per_country = [], {'country_id': ctx.ids, 'un_2020': fb_un}

    def add(name, fb, pop_sim):
        err = fb - fb_un
        rows.append(dict(model=name, popw_mae_pp=float(100 * (np.abs(err) * w).sum()),
                         country_mae_pp=float(100 * np.abs(err).mean()),
                         corr_with_un=float(np.corrcoef(fb, fb_un)[0, 1]),
                         world_foreign_born_millions=float((fb * pop_sim).sum() / 1e6),
                         un_world_foreign_born_millions=float((fb_un * pop).sum() / 1e6)))
        per_country[name] = fb

    for t in (lo, 0.5 * (lo + hi), hi):
        _, P0, P = SM.hindcast(ctx, dict(p, turnover=t), start, ctx.s2020, years=end - start, return_state=True)
        pop_sim = P.sum((1, 2, 3))
        add(f'migration model, circulation {t:.4f}/year', P[:, :, 1].sum((1, 2)) / pop_sim, pop_sim)
    fb0 = P0[:, :, 1].sum((1, 2)) / P0.sum((1, 2, 3))
    add('persistence (1990 foreign-born share)', fb0, pop)
    return pd.DataFrame(rows), pd.DataFrame(per_country)


def interval_calibration(ctx, runs=40, seed=None, starts=(1980, 1990, 2000), levels=(0.5, 0.8, 0.9)):
    """Are the model's predictive intervals the right width?

    Point errors say whether the centre of a forecast is right; they say nothing about whether the
    stated uncertainty is honest. For each history window this draws `runs` full parameter sets,
    runs the 10-year hindcast with each, and asks what fraction of the observed country x religion
    shares fell inside the model's central 50%, 80% and 90% intervals. A well-calibrated model
    covers about the nominal fraction.

    The intervals here are PARAMETER uncertainty only: the model does not claim to know how much
    the WRP measurements themselves move between rounds. `coverage_with_measurement_error` widens
    each interval by the per-religion residual scale the switching fit estimates for that noise,
    which is the comparison that shows whether the shortfall is the model being overconfident or
    the data being noisy.

    Switching is fitted on windows that END no later than the test window STARTS, as elsewhere.
    """
    seed = ctx.a['random_seed'] if seed is None else seed
    wins = ES.no_switching_hindcasts(ctx, ES.central_params(ctx), ES.windows(ctx, (1950, 1960, 1970, 1980, 1990, 2000)))
    rows, per_window = [], []
    for w in [x for x in wins if x['start'] in starts]:
        train = [x for x in wins if x['end'] <= w['start']]
        if len(train) < 2:
            continue
        hier = ES.fit_switching(ctx, train, use_survey=False)
        noise = np.zeros(K) if hier.net_scale is None else np.asarray(hier.net_scale, float)
        preds = np.empty((runs, ctx.n, K))
        for r in range(runs):
            rng = np.random.default_rng([seed, 777, w['start'], r])
            p = SM.draw_run(ctx, rng, ctx.a['reference_scenario'])
            idx = hier.sample_indices(rng, 1)[:, 0]
            preds[r] = SM.hindcast(ctx, p, w['start'], w['s0'], years=w['end'] - w['start'],
                                   hier=hier, draw_idx=idx)[0]
        m = w['mask'] & np.isfinite(w['s1']).all(1)
        obs = w['s1'][m]
        pr = preds[:, m, :]
        pop = ctx.wpp_at('pop', w['start'])[m]
        weights = np.repeat(pop[:, None], K, axis=1)
        for lev in levels:
            lo, hi = np.quantile(pr, (1 - lev) / 2, axis=0), np.quantile(pr, 1 - (1 - lev) / 2, axis=0)
            inside = (obs >= lo) & (obs <= hi)
            wide = (obs >= lo - noise[None, :]) & (obs <= hi + noise[None, :])
            rows.append(dict(window=f"{w['source']} {w['start']}-{w['end']}", nominal=lev, cells=int(inside.size),
                             coverage=float(inside.mean()),
                             coverage_population_weighted=float(np.average(inside, weights=weights)),
                             coverage_with_measurement_error=float(wide.mean()),
                             mean_interval_width_pp=100 * float((hi - lo).mean()),
                             median_interval_width_pp=100 * float(np.median(hi - lo))))
        centre = preds.mean(0)
        # How wide would the intervals have to be? Compare the model's own half-width with the
        # absolute error actually made, per religion.
        err = np.abs(pr.mean(0) - obs)
        half = 0.5 * (np.quantile(pr, 0.95, axis=0) - np.quantile(pr, 0.05, axis=0))
        for k, c in enumerate(CATS):
            per_window.append(dict(window=f"{w['source']} {w['start']}-{w['end']}", religion=c, runs=runs,
                                   train_windows=len(train), cells=int(len(obs)),
                                   abs_error_median_pp=100 * float(np.median(err[:, k])),
                                   abs_error_q90_pp=100 * float(np.quantile(err[:, k], 0.9)),
                                   model_half_width_q90_pp=100 * float(np.quantile(half[:, k], 0.9)),
                                   widening_needed=float(np.quantile(err[:, k], 0.9) /
                                                         max(np.quantile(half[:, k], 0.9), 1e-9))))
    return pd.DataFrame(rows), pd.DataFrame(per_window)


def corridor_check(ctx, rhos=(1.0, 0.75, 0.5), start=1990, end=2020, top=25):
    """Simulated 1990-2020 corridor flows vs positive growth of UN bilateral stocks, by margin softness."""
    from religion_forecast import datasets as D
    if ctx.stock_df is None:
        return None
    S0, y0 = D.stock_matrix(ctx.stock_df, ctx.ids, start)
    S1, y1 = D.stock_matrix(ctx.stock_df, ctx.ids, end)
    if S0 is None or y0 != start or y1 != end:
        return None
    dS = np.maximum(S1 - S0, 0.0)
    np.fill_diagonal(dS, 0.0)
    dests = np.argsort(dS.sum(0))[::-1][:top]
    p = ES.central_params(ctx)
    rows = []
    orig = SM.MigrationPlan.realise
    for rho in rhos:
        acc = []

        def realise(self, year, dem, P, _acc=acc):
            out = orig(self, year, dem, P)
            _acc.append(self.last_F)
            return out
        SM.MigrationPlan.realise = realise
        try:
            SM.hindcast(ctx, dict(p, margin_rho=rho), start, ctx.s2020, years=end - start)
        finally:
            SM.MigrationPlan.realise = orig
        F = np.sum(acc, axis=0)
        mix = lambda M, d: M[:, d] / max(M[:, d].sum(), 1e-300)
        rows.append(dict(margin_rho=rho,
                         destination_origin_mix_corr=float(np.mean([np.corrcoef(mix(F, d), mix(dS, d))[0, 1] for d in dests])),
                         destination_origin_mix_tv=float(np.mean([0.5 * np.abs(mix(F, d) - mix(dS, d)).sum() for d in dests])),
                         simulated_moves_millions=float(F.sum() / 1e6), stock_growth_millions=float(dS.sum() / 1e6)))
    return pd.DataFrame(rows)


def summarize(by):
    out = []
    for scope, filt in (('test windows 1990-2010 (WRP)', by.source.eq('WRP') & by.start.ge(1990)),
                        ('all WRP windows 1970-2010', by.source.eq('WRP')),
                        ('Pew 2010-2020', by.source.eq('Pew'))):
        sub = by[filt]
        if sub.empty:
            continue
        g = sub.groupby('model').agg(windows=('window', 'nunique'), popw_tv_pp=('popw_tv_pp', 'mean'),
                                     mean_tv_pp=('mean_tv_pp', 'mean'), mae_pp=('mae_pp', 'mean'),
                                     dominant_accuracy=('dominant_accuracy', 'mean'),
                                     changed_true=('changed_true', 'sum'), changed_hit=('changed_hit', 'sum'),
                                     false_alarm=('false_alarm', 'sum')).reset_index()
        pers = float(g.loc[g.model.eq('persistence'), 'popw_tv_pp'].iloc[0])
        g['beats_persistence'] = g.popw_tv_pp < pers - 1e-9
        g['change_vs_persistence_pp'] = g.popw_tv_pp - pers
        g.insert(0, 'scope', scope)
        out.append(g)
    return pd.concat(out, ignore_index=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--no-pew', action='store_true', help='skip the Pew 2010-2020 window even if available')
    ap.add_argument('--skip-ablations', action='store_true', help='skip the data-ablation table')
    ap.add_argument('--foreign-born-only', action='store_true', help='run only the migration-volume check')
    ap.add_argument('--quick', action='store_true', help='skip the data ablations and the interval calibration')
    ap.add_argument('--calibration-runs', type=int, default=40, help='Monte Carlo runs per window for the interval calibration')
    args = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    fb = foreign_born_check(make_context())
    if fb is not None:
        fb[0].to_csv(OUT / 'migration_foreign_born_check.csv', index=False)
        fb[1].to_csv(OUT / 'migration_foreign_born_by_country.csv', index=False)
        print('Foreign-born share 2020, simulated from UN 1990 stocks vs UN 2020 (pp):')
        print(fb[0].round(3).to_string(index=False))
    if not (args.foreign_born_only or args.quick):
        cal, cw = interval_calibration(make_context(), runs=args.calibration_runs)
        if len(cal):
            cal.to_csv(OUT / 'interval_calibration.csv', index=False)
            cw.to_csv(OUT / 'interval_calibration_windows.csv', index=False)
            print('\nPredictive interval calibration (share of observed country x religion shares inside):')
            print(cal.round(3).to_string(index=False))
            print('\nOut-of-sample error at a 10-year horizon against the width the model claims:')
            g = cw.groupby('religion').agg(abs_error_median_pp=('abs_error_median_pp', 'mean'),
                                           abs_error_q90_pp=('abs_error_q90_pp', 'mean'),
                                           model_half_width_q90_pp=('model_half_width_q90_pp', 'mean'),
                                           widening_needed=('widening_needed', 'mean')).reset_index()
            print(g.round(3).to_string(index=False))
    cc = corridor_check(make_context())
    if cc is not None:
        cc.to_csv(OUT / 'migration_corridor_check.csv', index=False)
        print('Corridors 1990-2020: simulated inflows vs growth of UN bilateral stocks (25 largest destinations):')
        print(cc.round(3).to_string(index=False))
    if args.foreign_born_only:
        return
    if not (args.skip_ablations or args.quick):
        ab = ablations(include_pew=not args.no_pew)
        ab.to_csv(OUT / 'data_ablations_by_window.csv', index=False)
        abs_ = (ab.assign(scope=np.where(ab.source.eq('Pew'), 'Pew 2010-2020',
                                         np.where(ab.start.ge(1990), 'WRP 1990-2010', 'WRP 1970-1990')))
                .groupby(['scope', 'data_variant', 'model'], sort=False)
                .agg(popw_tv_pp=('popw_tv_pp', 'mean'), persistence=('persistence_popw_tv_pp', 'mean')).reset_index())
        abs_['change_vs_persistence_pp'] = abs_.popw_tv_pp - abs_.persistence
        abs_.to_csv(OUT / 'data_ablations_summary.csv', index=False)
        print('Data ablations (population-weighted TV error, pp):')
        print(abs_.round(3).to_string(index=False))
    ctx, by, fits, sel, choice = run(include_pew=not args.no_pew)
    summ = summarize(by)
    by.to_csv(OUT / 'validation_by_window.csv', index=False)
    summ.to_csv(OUT / 'validation_summary.csv', index=False)
    fits.to_csv(OUT / 'switching_fit_by_fold.csv', index=False)
    sel.to_csv(OUT / 'out_of_sample_choices.csv', index=False)
    from religion_forecast import datasets as D
    rep = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), start_state=ctx.start_source,
               inputs=D.catalogue(), history_test_choices=choice,
               used_by_forecast=dict(
                   switching_strength=('fixed at 1 (config/assumptions.json, switching.strength_range), not taken from '
                                       'the history tests. Over all four windows no switching scores best, because the '
                                       'two earliest folds were fitted on only two or three noisy WRP decades (see '
                                       'switching_fit_by_fold.csv); on 1990-2010, where the fit had four or five decades, '
                                       'full strength scores best; and surveys observe switching directly. The level of '
                                       'switching is uncertain and enters each run through survey_level_weight.'),
                   residual_weight=ctx.a['residual']['default_weight'],
                   residual_note='The forecast runs without the residual learner. If history_test_choices.residual.weight '
                                 'is above 0 (for example with the Pew 2010-2020 window), that is reported, not applied.'),
               emigration_selectivity=None if ctx.selectivity is None else {
                   'model': ctx.selectivity.get('kind', 'propensity'), 'kappa': ctx.selectivity.get('kappa'),
                   'lambda': ctx.selectivity['lam'], 'rmse_pp': ctx.selectivity['rmse_pp'],
                   'rmse_if_migrants_mirror_origin_pp': ctx.selectivity['rmse_mirror_pp']},
               notes=['history_test_choices are the options with the lowest mean population-weighted error over the '
                      'test windows; the per-window choices in out_of_sample_choices.csv use earlier windows only.',
                      'WPP 2024 estimates are used for each historical window (retrospective, not real-time).',
                      'WRP and Pew classify some populations differently (notably folk religion vs unaffiliated in '
                      'China); windows never mix sources.'])
    (OUT / 'validation_report.json').write_text(json.dumps(rep, indent=2, default=float), encoding='utf8')
    pd.set_option('display.width', 200)
    cols = ['scope', 'model', 'windows', 'popw_tv_pp', 'mean_tv_pp', 'dominant_accuracy', 'changed_true',
            'changed_hit', 'false_alarm', 'change_vs_persistence_pp']
    print(summ[cols].round(3).to_string(index=False))
    print('\nSwitching fit by fold:\n' + fits.to_string(index=False))
    print('\nOut-of-sample choices per window:\n' + sel.to_string(index=False))
    print('\nBest options in the history tests:', json.dumps(choice, indent=1, default=float))
    print('Used by the forecast: switching strength 1 (assumption; see validation_report.json), residual weight',
          ctx.a['residual']['default_weight'])
    print(f'\nWrote {OUT}')


if __name__ == '__main__':
    main()
