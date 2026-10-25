"""Experiments that ask what the model says, rather than what it predicts.

    ablation    turn one mechanism off at a time and measure what it was contributing
    sensitivity which uncertain parameters actually move the results
    sorting     does more migration make countries more religiously mixed, and under what
                assumption about where migrants go

Every experiment reuses the random draws of the main projection, run by run, so a difference
between two variants comes from the change being tested and not from sampling noise.

    python run.py experiments                 all three
    python run.py experiments --only ablation
    python run.py experiments --runs 40       more runs (slower, tighter intervals)

Writes data/experiments/ (git-ignored).
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from religion_forecast import config
from religion_forecast import engine as E
from religion_forecast import model as SM
from religion_forecast import projection as FC

OUT = config.EXPERIMENTS
CATS = E.CATS
YEARS = [2050, 2100, 2200, 2500, 3026]
SORTING_SCENARIOS = ['low_migration', 'stabilising', 'rising_migration']

# Mechanism ablations. Each is the reference scenario with one mechanism switched off.
ABLATIONS = {
    'full model': {},
    'no religious switching': {'switching': False},
    'no migration': {'migration': False},
    'no fertility differences': {'fertility_gaps': False},
    'demography only': {'switching': False, 'migration': False, 'fertility_gaps': False},
}


def _world(res, year):
    pop = res['pop'][year]
    w = pop / max(pop.sum(), 1e-9)
    return (res['shares'][year] * w[:, None]).sum(0), w


# What `_summary` reports. Keeping this explicit matters for the sensitivity analysis, which has to
# tell outcomes apart from drawn parameters: `foreign_born_share_world`, for instance, is an
# outcome of the migration settings, and regressing on it alongside them would be circular.
OUTCOMES = ['diversity_within_pop_weighted', 'diversity_world', 'dominant_changed_countries',
            'foreign_born_share_world', 'world_population'] + [f'world_{c}' for c in CATS]


def _summary(ctx, res, dom0, **extra):
    rows = []
    for y in YEARS:
        world, w = _world(res, y)
        sh = res['shares'][y]
        rows.append(dict(year=y,
                         diversity_within_pop_weighted=float((E.gini_simpson(sh) * w).sum()),
                         diversity_world=float(E.gini_simpson(world)),
                         dominant_changed_countries=int((sh.argmax(1) != dom0).sum()),
                         foreign_born_share_world=float((res['foreign_born'][y] * w).sum()),
                         world_population=float(res['pop'][y].sum()),
                         **{f'world_{c}': float(world[k]) for k, c in enumerate(CATS)}, **extra))
    return rows


# --------------------------------------------------------------------------------- ablations
def ablation(ctx, hier, runs, seed, log=print):
    """The reference scenario with one mechanism switched off at a time, on identical draws."""
    cfg = ctx.a['scenarios'][ctx.a['reference_scenario']]
    dom0 = ctx.s2020.argmax(1)
    rows, t0 = [], time.time()
    for name, off in ABLATIONS.items():
        for r in range(runs):
            rng = np.random.default_rng([seed, r])
            p = SM.draw_run(ctx, rng, ctx.a['reference_scenario'])
            idx = hier.sample_indices(rng, 1)[:, 0]
            res = SM.simulate(ctx, p, cfg, hier, idx, **off)
            rows += _summary(ctx, res, dom0, variant=name, run=r)
        log(f'  ablation {name}: {runs} runs ({time.time() - t0:.0f}s)')
    return pd.DataFrame(rows)


def ablation_effects(df):
    """Each mechanism's contribution: full model minus the run without it, paired by run."""
    keys = ['year', 'run']
    full = df[df.variant.eq('full model')].set_index(keys)
    cols = [c for c in df.columns if c.startswith('world_') or c.startswith('diversity_')
            or c == 'dominant_changed_countries']
    out = []
    for name in ABLATIONS:
        if name == 'full model':
            continue
        sub = df[df.variant.eq(name)].set_index(keys)
        diff = (full[cols] - sub[cols]).reset_index()
        g = diff.groupby('year')[cols].agg(['mean', lambda x: x.quantile(.05), lambda x: x.quantile(.95)])
        for year in sorted(diff.year.unique()):
            for c in cols:
                m, lo, hi = g.loc[year, (c, 'mean')], g.loc[year, (c, '<lambda_0>')], g.loc[year, (c, '<lambda_1>')]
                out.append(dict(mechanism=name.replace('no ', ''), year=year, outcome=c,
                                contribution_mean=float(m), contribution_q05=float(lo), contribution_q95=float(hi)))
    return pd.DataFrame(out)


# ------------------------------------------------------------------------------- sensitivity
def _standardise(x):
    sd = x.std(ddof=1)
    return (x - x.mean()) / sd if sd > 1e-12 else x * 0.0


def sensitivity(outcomes, params, outcome_cols):
    """Which drawn parameters move which outcomes.

    For each outcome, both the raw values and their ranks are standardised and the outcome is
    regressed on all parameters at once. The coefficients (SRC on values, SRRC on ranks) say how
    many standard deviations the outcome moves when one parameter moves by one standard deviation
    with the others held at their mean. Ranks are the headline because they survive a monotone
    non-linearity; R2 says how much of the spread this linear reading explains, so a low R2 is a
    warning that the parameters interact.
    """
    rows = []
    X = outcomes[params].to_numpy(float)
    keep = [j for j in range(X.shape[1]) if X[:, j].std(ddof=1) > 1e-12]
    params = [params[j] for j in keep]
    X = X[:, keep]
    Xs = np.column_stack([_standardise(X[:, j]) for j in range(X.shape[1])])
    Xr = np.column_stack([_standardise(pd.Series(X[:, j]).rank().to_numpy(float)) for j in range(X.shape[1])])
    # Parameters are drawn independently, so they should be near-orthogonal; if any pair is not,
    # its coefficients cannot be read one at a time, and this column says so.
    R = np.corrcoef(Xs, rowvar=False)
    np.fill_diagonal(R, 0.0)
    corr = np.nan_to_num(np.abs(R)).max(1).round(3)
    for col in outcome_cols:
        y = outcomes[col].to_numpy(float)
        if not np.isfinite(y).all() or y.std(ddof=1) <= 1e-12:
            continue
        for label, design, target in (('value', Xs, _standardise(y)),
                                      ('rank', Xr, _standardise(pd.Series(y).rank().to_numpy(float)))):
            beta, *_ = np.linalg.lstsq(design, target, rcond=None)
            r2 = 1.0 - ((target - design @ beta) ** 2).sum() / max((target ** 2).sum(), 1e-12)
            for j, pname in enumerate(params):
                rows.append(dict(outcome=col, basis=label, parameter=pname,
                                 coefficient=float(beta[j]), abs_coefficient=abs(float(beta[j])),
                                 model_r2=float(r2), runs=len(y), max_abs_corr_with_other=corr[j]))
    return pd.DataFrame(rows)


def sensitivity_runs(ctx, hier, runs, seed, log=print):
    """Extra runs of the reference scenario used only for the sensitivity design: one row per run
    with its drawn parameters and its outcomes."""
    cfg = ctx.a['scenarios'][ctx.a['reference_scenario']]
    dom0 = ctx.s2020.argmax(1)
    rows, t0 = [], time.time()
    for r in range(runs):
        rng = np.random.default_rng([seed, 10_000 + r])          # a design separate from the projection runs
        p = SM.draw_run(ctx, rng, ctx.a['reference_scenario'])
        idx = hier.sample_indices(rng, 1)[:, 0]
        res = SM.simulate(ctx, p, cfg, hier, idx)
        scalars = {k: float(v) for k, v in p.items() if np.ndim(v) == 0 and k != 'scenario'}
        for row in _summary(ctx, res, dom0, run=r):
            rows.append({**scalars, **row})
        if (r + 1) % 20 == 0:
            log(f'  sensitivity {r + 1}/{runs} runs ({time.time() - t0:.0f}s)')
    return pd.DataFrame(rows)


# -------------------------------------------------------------------------- migrant sorting
SORTING_VARIANTS = {
    'calibrated': {},                                    # kappa and lambda fitted to Pew
    'no destination affinity': {'kappa': 0.0},           # migrants do not favour co-religionists
    'migrants mirror origin': {'kappa': 0.0, 'lam': 0.0},
}


def migrant_sorting(ctx, hier, runs, seed, log=print):
    """Does more migration make countries more religiously mixed? The answer depends on where
    migrants go, so each migration scenario is rerun under three assumptions about that."""
    calibrated = dict(ctx.selectivity)
    dom0 = ctx.s2020.argmax(1)
    rows, t0 = [], time.time()
    try:
        for name in SORTING_SCENARIOS:
            cfg = ctx.a['scenarios'][name]
            for r in range(runs):
                for vname, override in SORTING_VARIANTS.items():
                    ctx.selectivity = dict(calibrated, **override)
                    rng = np.random.default_rng([seed, r])
                    p = SM.draw_run(ctx, rng, name)
                    idx = hier.sample_indices(rng, 1)[:, 0]
                    res = SM.simulate(ctx, p, cfg, hier, idx)
                    rows += _summary(ctx, res, dom0, scenario=name, variant=vname, run=r,
                                     kappa=ctx.selectivity['kappa'], lam=ctx.selectivity['lam'])
            log(f'  sorting {name}: {runs} runs x {len(SORTING_VARIANTS)} variants ({time.time() - t0:.0f}s)')
    finally:
        ctx.selectivity = calibrated
    return pd.DataFrame(rows)


def sorting_effect(df):
    """Rising minus low migration, paired by run, under each assumption about where migrants go."""
    pv = df.pivot_table(index=['year', 'variant', 'run'], columns='scenario',
                        values='diversity_within_pop_weighted').reset_index()
    if not {'rising_migration', 'low_migration'} <= set(pv.columns):
        return pd.DataFrame()
    pv['d'] = pv.rising_migration - pv.low_migration
    return (pv.groupby(['year', 'variant']).d
            .agg(median='median', q05=lambda x: x.quantile(.05), q95=lambda x: x.quantile(.95),
                 runs_more_diverse=lambda x: int((x > 0).sum()), runs='size').reset_index()
            .rename(columns={'d': 'diversity_difference'}))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--runs', type=int, default=12, help='runs per variant for the ablation and sorting experiments')
    ap.add_argument('--sensitivity-runs', type=int, default=120, help='runs in the sensitivity design')
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--only', choices=['ablation', 'sensitivity', 'sorting'], default=None)
    args = ap.parse_args(argv)
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    ctx = SM.Context()
    hier, _ = FC.prepare(ctx)
    seed = args.seed if args.seed is not None else ctx.a['random_seed']
    want = {args.only} if args.only else {'ablation', 'sensitivity', 'sorting'}
    pd.set_option('display.width', 200)

    if 'ablation' in want:
        df = ablation(ctx, hier, args.runs, seed)
        df.to_csv(OUT / 'ablation_runs.csv', index=False)
        eff = ablation_effects(df)
        eff.to_csv(OUT / 'ablation_effects.csv', index=False)
        show = eff[eff.year.isin([2050, 2100]) & eff.outcome.isin(
            ['world_Christianity', 'world_Islam', 'world_Unaffiliated', 'dominant_changed_countries'])]
        print('\nWhat each mechanism contributes (full model minus the run without it):')
        print(show.pivot_table(index=['outcome', 'year'], columns='mechanism', values='contribution_mean').round(4).to_string())

    if 'sensitivity' in want:
        runs = sensitivity_runs(ctx, hier, args.sensitivity_runs, seed)
        runs.to_csv(OUT / 'sensitivity_runs.csv', index=False)
        outcome_cols = [c for c in OUTCOMES if c in runs.columns and c != 'world_population']
        params = [c for c in runs.columns if c not in OUTCOMES and c not in ('year', 'run')]
        out = pd.concat([sensitivity(runs[runs.year.eq(y)], params, outcome_cols).assign(year=y)
                         for y in sorted(runs.year.unique())], ignore_index=True)
        out.to_csv(OUT / 'sensitivity_coefficients.csv', index=False)
        top = (out[out.basis.eq('rank') & out.year.isin([2100, 3026])]
               .sort_values('abs_coefficient', ascending=False)
               .groupby(['year', 'outcome']).head(3))
        print('\nStrongest parameters (standardised rank regression, top 3 per outcome):')
        print(top[top.outcome.isin(['world_Christianity', 'world_Islam', 'world_Unaffiliated',
                                    'diversity_within_pop_weighted'])]
              [['year', 'outcome', 'parameter', 'coefficient', 'model_r2']].round(3).to_string(index=False))

    if 'sorting' in want:
        df = migrant_sorting(ctx, hier, args.runs, seed)
        df.to_csv(OUT / 'migrant_sorting_runs.csv', index=False)
        eff = sorting_effect(df)
        eff.to_csv(OUT / 'migrant_sorting_effect.csv', index=False)
        print('\nRising minus low migration, within-country diversity (positive = more diverse):')
        print(eff.round(4).to_string(index=False))

    print(f'\nWrote {OUT} in {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
