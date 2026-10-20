"""Step 7 sensitivity: does migration raise or lower religious diversity, and why?

Runs the migration scenarios with three assumptions about who migrates where, using the same random
draws for each (common random numbers), so the differences come from the assumption alone:
  calibrated     destination affinity kappa and minority effect lambda fitted to Pew's migrant figures
  no_affinity    kappa = 0 (migrants do not favour destinations where their religion is common), same lambda
  mirror         kappa = 0, lambda = 0 (migrants have their origin country's religious mix)

Run (from this folder, Windows PowerShell):
    .\\.venv\\Scripts\\python.exe step7_sensitivity.py            # 6 runs per cell, about 15 minutes
    .\\.venv\\Scripts\\python.exe step7_sensitivity.py --runs 12
Writes data/forecasts_step7/sensitivity_migrant_sorting.csv (git-ignored). Nothing else is touched.
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

import step7_engine as E
import step7_forecast as FC
import step7_model as SM

YEARS = [2050, 2100, 2200, 2500, 3026]
SCENARIOS = ['low_migration', 'stabilising', 'rising_migration']


def summarise(ctx, res, s2020_dom):
    rows = []
    for y in YEARS:
        sh, pop = res['shares'][y], res['pop'][y]
        w = pop / pop.sum()
        world = (sh * w[:, None]).sum(0)
        rows.append(dict(
            year=y,
            diversity_within_pop_weighted=float((E.gini_simpson(sh) * w).sum()),
            diversity_within_country_mean=float(E.gini_simpson(sh).mean()),
            diversity_world=float(E.gini_simpson(world)),
            dominant_changed_countries=int((sh.argmax(1) != s2020_dom).sum()),
            foreign_born_share_world=float((res['foreign_born'][y] * w).sum()),
            **{f'world_{c}': float(world[k]) for k, c in enumerate(E.CATS)}))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=6)
    ap.add_argument('--seed', type=int, default=None)
    args = ap.parse_args()
    t0 = time.time()
    ctx = SM.Context()
    hier, _ = FC.prepare(ctx)
    seed = args.seed if args.seed is not None else ctx.a['random_seed']
    cal = dict(ctx.selectivity)
    variants = {'calibrated': cal,
                'no_affinity': dict(cal, kappa=0.0),
                'mirror': dict(cal, kappa=0.0, lam=0.0)}
    dom0 = ctx.s2020.argmax(1)
    rows = []
    for name in SCENARIOS:
        cfg = ctx.a['scenarios'][name]
        for r in range(args.runs):
            for vname, sel in variants.items():
                ctx.selectivity = sel
                rng = np.random.default_rng([seed, r])      # the same draws as run r of step7_forecast
                p = SM.draw_run(ctx, rng, name)
                idx = hier.sample_indices(rng, 1)[:, 0]
                res = SM.simulate(ctx, p, cfg, hier, idx)
                for row in summarise(ctx, res, dom0):
                    rows.append(dict(scenario=name, variant=vname, run=r, kappa=sel['kappa'], lam=sel['lam'], **row))
        print(f'  {name}: {args.runs} runs x {len(variants)} variants ({time.time() - t0:.0f}s)')
    ctx.selectivity = cal
    df = pd.DataFrame(rows)
    out = FC.OUT / 'sensitivity_migrant_sorting.csv'
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    cols = ['diversity_within_pop_weighted', 'diversity_world', 'dominant_changed_countries', 'world_Islam',
            'world_Christianity', 'world_Unaffiliated']
    tab = df.groupby(['year', 'scenario', 'variant'])[cols].median().round(3)
    with pd.option_context('display.width', 200, 'display.max_rows', 200):
        print(tab)
    print(f'Wrote {out} in {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
