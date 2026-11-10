"""History tests: how well the model forecasts decades it was not fitted to.

    python run.py backtest            everything below (about ten minutes)
    python run.py backtest --quick    point forecasts and inference only

Writes data/validation/ (git-ignored) and prints a summary.

Point forecasts. Windows are ten-year periods with observed shares at both ends: World Religion
Project 1970-1980 ... 2000-2010 and, when data/processed/pew_harmonized.csv exists, Pew 2010-2020.
A window is forecast only with what was known before it: switching is estimated on windows that
END no later than the test window STARTS, and the switching strength of `switching_selected` is
chosen on earlier test windows only. National demography inside the window is WPP 2024's estimate
(retrospective, not the projection available at the time), so every model is scored conditional
on national fertility, mortality and net migration.

    persistence             shares unchanged
    trend                   the model's last-decade residual repeated: a naive trend baseline
    demography              births, deaths, ageing (group fertility, generations), no migration
    demography_migration    + origin-destination migration
    switching_<s>           + switching, posterior mean rates times strength s = 0, 0.5, 1
    switching_selected      + switching at the strength that scored best on earlier windows

Scores per window: population-weighted and unweighted total-variation (TV) error, mean absolute
error, accuracy of the largest religion and detection of changes in it.

Inference. A window-level comparison has as many observations as windows (four or five), so no
test on it can reach conventional significance. `inference` compares each model with persistence
country by country: the population-weighted mean difference in TV error over every country-window,
with a 95% interval from a bootstrap that resamples countries (all of a country's windows together).
Countries within a decade share common shocks, which this interval does not capture, so the exact
window-level sign-flip test is reported beside it as the conservative bound.

Forecast errors (religion_forecast.errors). Monte Carlo forecasts from every origin, scored at
horizons of 10 to 40 years; the fitted error model used for the projection's predictive intervals;
and leave-one-origin-out coverage and interval scores of those intervals.

Migration. foreign_born_check simulates 1990-2020 from the UN 1990 foreign-born stocks and compares
each country's 2020 foreign-born share with the UN 2020 stocks. corridor_check compares simulated
1990-2020 inflows into the 25 largest destinations with the growth of UN bilateral stocks.
"""
from __future__ import annotations

import argparse
import itertools
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from religion_forecast import calibration as ES
from religion_forecast import config
from religion_forecast import engine as E
from religion_forecast import errors as ER
from religion_forecast import model as SM

OUT = config.VALIDATION
CATS, K = E.CATS, E.K
STRENGTHS = [0.0, 0.5, 1.0]
MODELS = ['persistence', 'trend', 'demography', 'demography_migration', 'switching_0', 'switching_0.5',
          'switching_1', 'switching_selected']
LABELS = {'persistence': 'Persistence (no change)', 'trend': 'Trend (last decade repeated)',
          'demography': 'Births and deaths', 'demography_migration': '+ migration',
          'switching_0': '+ switching, strength 0', 'switching_0.5': '+ switching, strength 0.5',
          'switching_1': '+ switching, strength 1 (as projected)',
          'switching_selected': '+ switching, strength chosen on earlier decades'}


def to_simplex(x):
    """Clip at zero and renormalise each row to sum to one."""
    s = np.clip(x, 0.0, None)
    return s / np.maximum(s.sum(1, keepdims=True), 1e-300)


def tv_by_country(pred, obs, mask):
    """Total-variation distance per country [n] (NaN where not scored)."""
    m = mask & np.isfinite(obs).all(1)
    out = np.full(len(mask), np.nan)
    out[m] = 0.5 * np.abs(pred[m] - obs[m]).sum(1)
    return out


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


# ------------------------------------------------------------------------- point forecasts
def run(include_pew=True, ctx=None):
    """Point forecasts of every test window. Returns (ctx, by-window scores, per-country errors,
    switching fits by fold, out-of-sample choices, summary of strength choices)."""
    ctx = ctx or make_context()
    p = ES.central_params(ctx)
    starts = (1950, 1960, 1970, 1980, 1990, 2000)
    wins = ES.no_switching_hindcasts(ctx, p, ES.windows(ctx, starts, include_pew), migration=True)
    wins_nomig = ES.no_switching_hindcasts(ctx, p, ES.windows(ctx, starts, include_pew), migration=False)
    tests = [w for w in wins if w['start'] >= 1970]
    rows, per_country, fits, sel_rows, hist = [], [], [], [], []
    for w in tests:
        t = w['start']
        label = f"{w['source']} {t}-{w['end']}"
        pop = ctx.wpp_at('pop', t)
        train = [x for x in wins if x['source'] == 'WRP' and x['end'] <= t]
        hier = ES.fit_switching(ctx, train, use_survey=False) if len(train) >= 2 else None
        b = ctx.a['switching'].get('bounds', {})
        at_bound = [] if hier is None else [k for k, v in zip(('delta', 'beta_d', 'tau_u'), hier.H)
                                            if k in b and min(abs(v - b[k][0]), abs(v - b[k][1])) < 1e-6]
        fits.append({'test_window': label, 'train_windows': len(train),
                     'delta': None if hier is None else hier.H[0], 'beta_d': None if hier is None else hier.H[1],
                     'tau_u': None if hier is None else hier.H[2], 'at_bound': ','.join(at_bound)})
        nm = next(x for x in wins_nomig if x['start'] == t and x['source'] == w['source'])
        base = w['pred']
        eff = ES.expected_switch_effect(hier, w) if hier is not None else np.zeros_like(base)
        previous = next((x for x in wins if x['source'] == 'WRP' and x['end'] == t), None) if w['source'] == 'WRP' \
            else next((x for x in wins if x['source'] == 'WRP' and x['end'] == 2010), None)
        preds = {'persistence': w['s0'], 'demography': nm['pred'], 'demography_migration': base,
                 'trend': base if previous is None else to_simplex(base + previous['resid'])}
        opt = {s: to_simplex(base + s * eff) for s in STRENGTHS}
        for s in STRENGTHS:
            preds[f'switching_{s:g}'] = opt[s]
        s_star = min(STRENGTHS, key=lambda s: np.mean([h[s] for h in hist])) if hist else 1.0
        preds['switching_selected'] = opt[s_star]
        for name in MODELS:
            pr = preds[name]
            rows.append({'window': label, 'source': w['source'], 'start': t, 'model': name,
                         **score(pr, w['s1'], w['s0'], w['mask'], pop)})
            tv = tv_by_country(pr, w['s1'], w['mask'])
            for i in np.flatnonzero(np.isfinite(tv)):
                per_country.append({'window': label, 'source': w['source'], 'country_id': ctx.ids[i],
                                    'population': float(pop[i]), 'model': name, 'tv': float(tv[i])})
        sel_rows.append({'window': label, 'switch_strength_used': s_star})
        hist.append({s: score(opt[s], w['s1'], w['s0'], w['mask'], pop)['popw_tv_pp'] for s in STRENGTHS})
    by = pd.DataFrame(rows)
    choice = {'switching_strength_scores_popw_tv_pp': {str(s): float(np.mean([h[s] for h in hist])) for s in STRENGTHS}}
    return ctx, by, pd.DataFrame(per_country), pd.DataFrame(fits), pd.DataFrame(sel_rows), choice


def summarize(by):
    out = []
    scopes = [('WRP 1970-2010', by.source.eq('WRP')), ('WRP 1990-2010', by.source.eq('WRP') & by.start.ge(1990)),
              ('Pew 2010-2020', by.source.eq('Pew')), ('all windows', by.source.isin(['WRP', 'Pew']))]
    for scope, filt in scopes:
        sub = by[filt]
        if sub.empty or (scope == 'all windows' and sub.source.nunique() < 2):
            continue
        g = sub.groupby('model').agg(windows=('window', 'nunique'), popw_tv_pp=('popw_tv_pp', 'mean'),
                                     mean_tv_pp=('mean_tv_pp', 'mean'), mae_pp=('mae_pp', 'mean'),
                                     dominant_accuracy=('dominant_accuracy', 'mean'),
                                     changed_true=('changed_true', 'sum'), changed_hit=('changed_hit', 'sum'),
                                     false_alarm=('false_alarm', 'sum')).reset_index()
        pers = float(g.loc[g.model.eq('persistence'), 'popw_tv_pp'].iloc[0])
        g['change_vs_persistence_pp'] = g.popw_tv_pp - pers
        g['change_vs_persistence_percent'] = 100 * g.change_vs_persistence_pp / pers
        g.insert(0, 'scope', scope)
        g['model'] = pd.Categorical(g.model, MODELS, ordered=True)
        out.append(g.sort_values('model'))
    return pd.concat(out, ignore_index=True)


# ------------------------------------------------------------------------------- inference
def sign_flip_p(diffs):
    """Exact two-sided p-value of the paired sign-flip (randomisation) test that the mean
    difference is zero. With n differences the smallest attainable value is 2 / 2^n."""
    d = np.asarray(diffs, float)
    obs = abs(d.mean())
    flips = np.array(list(itertools.product((1.0, -1.0), repeat=len(d))))
    return float((np.abs((flips * d).mean(1)) >= obs - 1e-12).mean())


def inference(per_country, reference='persistence', B=4000, seed=2026):
    """Each model against `reference`, country by country, in percentage points of TV error.

    mean_difference_pp   population-weighted mean of (model - reference) over all country-windows
    ci95_low/high        percentile interval from B bootstrap resamples of countries
    p_bootstrap          two-sided bootstrap p-value: 2 x the share of resamples on the far side of 0
    unweighted_*         the same with every country weighted equally
    share_better         fraction of country-windows where the model's error is lower
    windows, p_window    number of windows and the exact window-level sign-flip p-value"""
    rows = []
    rng = np.random.default_rng(seed)
    pc = per_country.copy()
    pc['scope'] = np.where(pc.source.eq('Pew'), 'Pew 2010-2020', 'WRP 1970-2010')
    scopes = [('WRP 1970-2010', pc[pc.scope.eq('WRP 1970-2010')])]
    if pc.source.eq('Pew').any():
        scopes += [('Pew 2010-2020', pc[pc.source.eq('Pew')]), ('all windows', pc)]
    for scope, sub in scopes:
        ref = sub[sub.model.eq(reference)].set_index(['window', 'country_id'])
        countries = sorted(sub.country_id.unique())
        cidx = {c: i for i, c in enumerate(countries)}
        draws = rng.integers(len(countries), size=(B, len(countries)))
        for name in [m for m in MODELS if m != reference]:
            cur = sub[sub.model.eq(name)].set_index(['window', 'country_id'])
            j = cur.join(ref[['tv']], rsuffix='_ref', how='inner').reset_index()
            d = 100 * (j.tv - j.tv_ref).to_numpy()
            w = j.population.to_numpy()
            ci = j.country_id.map(cidx).to_numpy()
            S, W = np.bincount(ci, w * d, len(countries)), np.bincount(ci, w, len(countries))
            Su, Nu = np.bincount(ci, d, len(countries)), np.bincount(ci, None, len(countries))
            boot = S[draws].sum(1) / W[draws].sum(1)
            boot_u = Su[draws].sum(1) / Nu[draws].sum(1)
            per_window = j.groupby('window').apply(lambda g: np.average(100 * (g.tv - g.tv_ref), weights=g.population),
                                                   include_groups=False)
            mean = float(S.sum() / W.sum())
            rows.append(dict(scope=scope, model=name, reference=reference, country_windows=len(d),
                             countries=int((Nu > 0).sum()), mean_difference_pp=mean,
                             ci95_low_pp=float(np.quantile(boot, 0.025)), ci95_high_pp=float(np.quantile(boot, 0.975)),
                             p_bootstrap=float(min(1.0, 2 * min((boot <= 0).mean(), (boot >= 0).mean()))),
                             unweighted_mean_difference_pp=float(Su.sum() / Nu.sum()),
                             unweighted_ci95_low_pp=float(np.quantile(boot_u, 0.025)),
                             unweighted_ci95_high_pp=float(np.quantile(boot_u, 0.975)),
                             share_better=float((d < -1e-9).mean()), windows=int(len(per_window)),
                             windows_better=int((per_window < 0).sum()),
                             p_window=sign_flip_p(per_window.to_numpy()) if len(per_window) > 1 else np.nan))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- migration
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


def corridor_check(ctx, rhos=(1.0, 0.75, 0.5), start=1990, end=2020, top=25, corridor_caps=(None,)):
    """Simulated 1990-2020 corridor flows vs positive growth of UN bilateral stocks, by margin
    softness and (optionally) corridor cap."""
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
        for cap in corridor_caps:
            acc = []

            def realise(self, year, dem, P, _acc=acc):
                out = orig(self, year, dem, P)
                _acc.append(self.last_F)
                return out
            SM.MigrationPlan.realise = realise
            try:
                SM.hindcast(ctx, dict(p, margin_rho=rho, corridor_cap=cap), start, ctx.s2020, years=end - start)
            finally:
                SM.MigrationPlan.realise = orig
            F = np.sum(acc, axis=0)
            mix = lambda M, d: M[:, d] / max(M[:, d].sum(), 1e-300)
            top_share = lambda M, d: float(mix(M, d).max())
            rows.append(dict(margin_rho=rho, corridor_cap='none' if cap is None else cap,
                             destination_origin_mix_corr=float(np.mean([np.corrcoef(mix(F, d), mix(dS, d))[0, 1] for d in dests])),
                             destination_origin_mix_tv=float(np.mean([0.5 * np.abs(mix(F, d) - mix(dS, d)).sum() for d in dests])),
                             largest_origin_share_simulated=float(np.mean([top_share(F, d) for d in dests])),
                             largest_origin_share_observed=float(np.mean([top_share(dS, d) for d in dests])),
                             simulated_moves_millions=float(F.sum() / 1e6), stock_growth_millions=float(dS.sum() / 1e6)))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------ data ablations
def ablations(include_pew=True):
    """Does each added dataset improve the history tests? Demography and demography + migration
    errors for data variants (switching is not involved, so nothing is refitted)."""
    variants = [('WPP indicators only', dict(bilateral=False, age_data=False, selectivity=False)),
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


# ------------------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--no-pew', action='store_true', help='skip the Pew 2010-2020 window even if available')
    ap.add_argument('--quick', action='store_true', help='point forecasts and inference only')
    ap.add_argument('--error-runs', type=int, default=40, help='Monte Carlo runs per origin for the forecast-error record')
    args = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.set_option('display.width', 220)
    ctx, by, per_country, fits, sel, choice = run(include_pew=not args.no_pew)
    summ = summarize(by)
    inf = inference(per_country)
    by.to_csv(OUT / 'validation_by_window.csv', index=False)
    per_country.to_csv(OUT / 'validation_by_country.csv', index=False)
    summ.to_csv(OUT / 'validation_summary.csv', index=False)
    inf.to_csv(OUT / 'inference.csv', index=False)
    fits.to_csv(OUT / 'switching_fit_by_fold.csv', index=False)
    sel.to_csv(OUT / 'out_of_sample_choices.csv', index=False)
    print(summ[['scope', 'model', 'windows', 'popw_tv_pp', 'change_vs_persistence_pp', 'change_vs_persistence_percent',
                'dominant_accuracy']].round(3).to_string(index=False))
    print('\nEach model against persistence, country by country (TV error, pp; negative = better):')
    print(inf[['scope', 'model', 'mean_difference_pp', 'ci95_low_pp', 'ci95_high_pp', 'p_bootstrap', 'share_better',
               'windows_better', 'windows', 'p_window']].round(3).to_string(index=False))
    calib = None
    if not args.quick:
        print('\nForecast-error record (Monte Carlo forecasts from every origin):')
        rec = ER.record(ctx, runs=args.error_runs)
        model = ER.fit(rec)
        ER.save(model)
        ER.record_table(rec).assign(country_id=lambda d: d.country_index.map(dict(enumerate(ctx.ids)))) \
            .drop(columns='country_index').to_csv(OUT / 'forecast_error_record.csv', index=False)
        calib, calib_world = ER.validate(rec)
        calib.to_csv(OUT / 'predictive_calibration.csv', index=False)
        calib_world.to_csv(OUT / 'predictive_calibration_world.csv', index=False)
        print(f"Error model: b = {model['b']:.3f} (scale (s(1-s))^b), beta = {model['beta']:.3f} "
              f"(error grows as (h/10)^beta); mean |standardised error| by horizon "
              f"{ {int(k): round(v, 3) for k, v in model['mean_abs_standardised_error'].items()} }")
        g = calib.groupby(['method', 'horizon', 'nominal'])[['coverage', 'interval_score_pp']].mean().unstack('nominal')
        print('Leave-one-origin-out coverage and interval score:')
        print(g.round(3).to_string())
        fb = foreign_born_check(make_context())
        if fb is not None:
            fb[0].to_csv(OUT / 'migration_foreign_born_check.csv', index=False)
            fb[1].to_csv(OUT / 'migration_foreign_born_by_country.csv', index=False)
            print('\nForeign-born share 2020, simulated from UN 1990 stocks vs UN 2020 (pp):')
            print(fb[0].round(3).to_string(index=False))
        cc = corridor_check(make_context(), corridor_caps=(None, 3.0, 2.0))
        if cc is not None:
            cc.to_csv(OUT / 'migration_corridor_check.csv', index=False)
            print('\nCorridors 1990-2020, simulated inflows vs growth of UN bilateral stocks (25 largest destinations):')
            print(cc.round(3).to_string(index=False))
        ab = ablations(include_pew=not args.no_pew)
        ab.to_csv(OUT / 'data_ablations_by_window.csv', index=False)
        abs_ = (ab.assign(scope=np.where(ab.source.eq('Pew'), 'Pew 2010-2020', 'WRP 1970-2010'))
                .groupby(['scope', 'data_variant', 'model'], sort=False)
                .agg(popw_tv_pp=('popw_tv_pp', 'mean'), persistence=('persistence_popw_tv_pp', 'mean')).reset_index())
        abs_['change_vs_persistence_pp'] = abs_.popw_tv_pp - abs_.persistence
        abs_.to_csv(OUT / 'data_ablations_summary.csv', index=False)
    from religion_forecast import datasets as D
    rep = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), start_state=ctx.start_source,
               inputs=D.catalogue(), switching_strength_choice=choice,
               projection_uses=dict(
                   switching_strength='1, with the level of switching varied through survey_level_weight; see '
                                      'docs/METHODS.md. The strength chosen on earlier windows is reported in '
                                      'out_of_sample_choices.csv, and the projection setting is scored as switching_1.'),
               emigration_selectivity=None if ctx.selectivity is None else {
                   'model': ctx.selectivity.get('kind', 'propensity'), 'kappa': ctx.selectivity.get('kappa'),
                   'lambda': ctx.selectivity['lam'], 'rmse_pp': ctx.selectivity['rmse_pp'],
                   'rmse_if_migrants_mirror_origin_pp': ctx.selectivity['rmse_mirror_pp']},
               forecast_error_model=None if calib is None else {k: v for k, v in json.loads(
                   (OUT / 'forecast_error_model.json').read_text()).items() if k != 'mean_u'},
               notes=['WPP 2024 estimates are used inside each historical window (retrospective, not real-time).',
                      'The World Religion Project and Pew classify some populations differently (notably folk '
                      'religion and the unaffiliated in China); windows never mix sources.'])
    (OUT / 'validation_report.json').write_text(json.dumps(rep, indent=2, default=float), encoding='utf8')
    print(f'\nWrote {OUT}')


if __name__ == '__main__':
    main()
