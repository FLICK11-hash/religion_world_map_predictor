"""The output tables of one projection run.

Every number here comes from the simulation; nothing is re-estimated. The functions take the
per-scenario `Store` built by `projection.run_scenarios` and return tidy DataFrames.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from religion_forecast import datasets as D
from religion_forecast import engine as E
from religion_forecast import calibration as ES
from religion_forecast import model as SM

CATS, K = E.CATS, E.K
TARGET_YEARS = [2020, 2050, 2100, 2200, 2500, 3026]
YEARS = sorted(set(SM.KEEP_YEARS) | {3026})
STEPS = list(range(2020, 3031, 5))
PERIOD_LABEL = {pr: f'{pr[0]}-{pr[1]}' for pr in SM.PERIODS}


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
        add(f'input {k}', v['detail'], v['status'], 'religion_forecast/datasets.py')
    add('switching hyperparameters (delta, beta_d, tau_u)', str(hier.H), 'estimated', 'empirical Bayes, religion_forecast.switching')
    add('switching evidence windows', ', '.join(f"{w['source']} {w['start']}-{w['end']}" for w in wins), 'observed', 'WRP, Pew')
    if ctx.switch_obs is not None:
        add('survey switching cells', f'{len(ctx.switch_obs)} cells, {ctx.switch_obs.country_id.nunique()} countries',
            'observed', 'inputs/switching_lifetime_observed.csv')
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

# ------------------------------------------------------------------ additional research tables
def group_fertility(ctx, name, st):
    """Fertility of each religion in each country in 2020-25: the group TFR the simulation actually
    used, after the national normalisation that makes the country total match WPP. The evidence tier
    says whether the gap behind it came from a country, regional or world figure."""
    if st.group_tfr is None:
        return pd.DataFrame()
    tfr = st.group_tfr / max(st.R, 1)                       # mean over runs, [n, K, G]
    nat = ctx.wpp_mean('tfr', 2020, 2025)
    rows = []
    for i, c in enumerate(ctx.ids):
        for k, r in enumerate(CATS):
            if ctx.s2020[i, k] <= 0:
                continue
            rows.append({'scenario': name, 'country_id': c, 'religion': r,
                         'share_2020': float(ctx.s2020[i, k]), 'national_tfr': float(nat[i]),
                         'group_tfr_native': float(tfr[i, k, 0]),
                         'group_tfr_first_generation': float(tfr[i, k, 1]),
                         'ratio_to_national': float(tfr[i, k, 0] / max(nat[i], 1e-9)),
                         'evidence': str(st.fertility_evidence[i, k]) if st.fertility_evidence is not None else ''})
    return pd.DataFrame(rows)


def shift_share(ct, ref, years=(2050, 2100, 2200)):
    """Split each religion's change in WORLD share into
         within   countries' own shares changing, at the starting population weights
         between  the population weights changing, at the starting shares
                  (countries with above-average growth pulling their religions up)
         interact the cross term.
    The three parts add up exactly to the total change. This is a different question from the
    component accounting, which attributes change to births, switching and migration."""
    r = ct[ct.scenario.eq(ref)]
    base = r[r.year.eq(2020)].set_index('country_id')
    w0 = base.mean_population / base.mean_population.sum()
    rows = []
    for y in years:
        cur = r[r.year.eq(y)].set_index('country_id').reindex(base.index)
        w1 = cur.mean_population / cur.mean_population.sum()
        dw = (w1 - w0).to_numpy()
        for c in CATS:
            s0, s1 = base[f'mean_{c}'].to_numpy(), cur[f'mean_{c}'].to_numpy()
            within, between = float((w0.to_numpy() * (s1 - s0)).sum()), float((dw * s0).sum())
            interact = float((dw * (s1 - s0)).sum())
            rows.append({'scenario': ref, 'year': y, 'religion': c,
                         'world_share_2020_pp': 100 * float((w0.to_numpy() * s0).sum()),
                         'world_share_pp': 100 * float((w1.to_numpy() * s1).sum()),
                         'change_pp': 100 * (within + between + interact),
                         'within_country_pp': 100 * within, 'population_weighting_pp': 100 * between,
                         'interaction_pp': 100 * interact})
    return pd.DataFrame(rows)


def holders(ct, ref, years=(2020, 2100), top=10):
    """The countries that hold each religion's adherents: how concentrated is each group, and where.
    `cumulative_share` is the running share of the world's adherents down the ranking."""
    r = ct[ct.scenario.eq(ref)]
    rows = []
    for y in years:
        cur = r[r.year.eq(y)]
        for c in CATS:
            people = (cur[f'mean_{c}'] * cur.mean_population).to_numpy()
            tot = people.sum()
            if tot <= 0:
                continue
            order = np.argsort(people)[::-1][:top]
            run = 0.0
            for rank, j in enumerate(order, 1):
                run += people[j] / tot
                rows.append({'scenario': ref, 'year': y, 'religion': c, 'rank': rank,
                             'country_id': cur.country_id.iloc[j], 'adherents_millions': people[j] / 1e6,
                             'share_of_world_group': people[j] / tot, 'cumulative_share': run})
    return pd.DataFrame(rows)


def fertility_evidence(ctx):
    """Which evidence tier supplies each country's fertility gap for each religion, with the 2020
    population share so a reader can see how much of the world the country tier covers."""
    f = ctx.fertility
    rows = []
    for i, c in enumerate(ctx.ids):
        for k, r in enumerate(CATS):
            tier = 'country' if np.isfinite(f['country'][i, k]) else (
                'region' if f['region_of'][i] in f['region'] and np.isfinite(f['region'][f['region_of'][i]][k])
                else 'world')
            rows.append({'country_id': c, 'pew_region': f['region_of'][i], 'religion': r, 'evidence_tier': tier,
                         'published_ratio': float(f['country'][i, k]) if tier == 'country' else np.nan,
                         'measure': str(f['measure'][i, k]), 'share_2020': float(ctx.s2020[i, k]),
                         'population_2020': float(ctx.wpp_at('pop', 2020)[i] * ctx.s2020[i, k])})
    return pd.DataFrame(rows)


def run_outcomes(ctx, stores, years=(2050, 2100, 2200, 3026)):
    """One row per (scenario, run): the drawn parameters and the outcomes of that run. This is the
    input to the global sensitivity analysis, which asks which parameters move which outcomes."""
    rows = []
    for name, st in stores.items():
        for r in range(st.R):
            row = {'scenario': name, 'run': r}
            row.update({k: v for k, v in st.params[r].items() if np.ndim(v) == 0 and k != 'scenario'})
            for y in years:
                j = YEARS.index(y)
                pop = st.pop[r, j]
                w = pop / max(pop.sum(), 1e-9)
                world = (st.sh[r, j] * w[:, None]).sum(0)
                for k, c in enumerate(CATS):
                    row[f'{c}_{y}'] = float(world[k])
                row[f'diversity_{y}'] = float((E.gini_simpson(st.sh[r, j]) * w).sum())
                row[f'world_population_{y}'] = float(pop.sum())
                row[f'dominant_changed_{y}'] = int((st.sh[r, j].argmax(1) != ctx.s2020.argmax(1)).sum())
            rows.append(row)
    return pd.DataFrame(rows)


def pew_2015_benchmark(ctx, ct, ref):
    """This model against Pew Research Center's own 2010-2050 projection.

    The two disagree about 2020 itself, because Pew's 2015 report and its 2025 measurement
    classify some populations differently (for the world Christian share the gap is over two
    percentage points, larger than most of the change either projects over thirty years). Levels
    are therefore not comparable and the table compares the CHANGE from 2020 to 2050 in each
    source separately, which is the quantity both are projecting.
    """
    pew = D.pew_2015_projection()
    if pew is None:
        return pd.DataFrame()
    r = ct[ct.scenario.eq(ref)]
    region_of = dict(zip(ctx.ids, ctx.fertility['region_of']))
    rows = []
    for level, areas in (('world', ['WORLD']), ('region', sorted(set(region_of.values()) - {'Unknown'}))):
        for area in areas:
            sel = r if area == 'WORLD' else r[r.country_id.map(region_of).eq(area)]
            if sel.empty:
                continue
            ours = {}
            for y in (2020, 2050):
                cur = sel[sel.year.eq(y)]
                pop = cur.mean_population.to_numpy()
                ours[y] = {c: float((cur[f'mean_{c}'].to_numpy() * pop).sum() / pop.sum()) for c in CATS}
            pw = pew[pew.level.eq(level) & pew.area.eq(area)]
            if pw.empty:
                continue
            pews = {}
            for y in (2020, 2050):
                g = pw[pw.year.eq(y)].set_index('religion').people
                tot = g.sum()
                pews[y] = {c: float(g.get(c, 0.0) / tot) for c in CATS}
            for c in CATS:
                rows.append({'level': level, 'area': area, 'religion': c,
                             'this_model_2020_pp': 100 * ours[2020][c], 'this_model_2050_pp': 100 * ours[2050][c],
                             'this_model_change_pp': 100 * (ours[2050][c] - ours[2020][c]),
                             'pew2015_2020_pp': 100 * pews[2020][c], 'pew2015_2050_pp': 100 * pews[2050][c],
                             'pew2015_change_pp': 100 * (pews[2050][c] - pews[2020][c]),
                             'change_difference_pp': 100 * ((ours[2050][c] - ours[2020][c]) - (pews[2050][c] - pews[2020][c])),
                             'level_difference_2020_pp': 100 * (ours[2020][c] - pews[2020][c])})
    return pd.DataFrame(rows)


def pew_2015_forecast_skill(ctx):
    """How well did Pew's own ten-year-ahead projection do? Pew's 2015 report projected 2020; the
    start state is Pew's 2025 measurement of 2020. Scoring one against the other gives an outside
    yardstick for what a careful published projection achieves at a ten-year horizon, next to this
    model's own backtest errors. Part of the gap is genuine forecast error and part is the two
    vintages classifying people differently, so this is an upper bound on Pew's error."""
    pew = D.pew_2015_projection()
    if pew is None:
        return pd.DataFrame()
    cty = pew[pew.level.eq('country') & pew.year.isin([2010, 2020])]
    wide = cty.pivot_table(index=['area', 'year'], columns='religion', values='people').reset_index()
    name_to_iso = _pew_country_codes(ctx, sorted(wide.area.unique()))
    wide['country_id'] = wide.area.map(name_to_iso)
    wide = wide.dropna(subset=['country_id'])
    rows = []
    idx = {c: i for i, c in enumerate(ctx.ids)}
    pop2020 = ctx.wpp_at('pop', 2020)
    for year, label in ((2020, 'projected 2020'), (2010, 'no change from 2010')):
        sub = wide[wide.year.eq(year)]
        errs, weights, codes = [], [], []
        for _, r in sub.iterrows():
            i = idx.get(r.country_id)
            if i is None:
                continue
            tot = sum(float(r[c]) for c in CATS)
            if tot <= 0:
                continue
            pred = np.array([float(r[c]) / tot for c in CATS])
            errs.append(0.5 * np.abs(pred - ctx.s2020[i]).sum())
            weights.append(pop2020[i])
            codes.append(r.country_id)
        if errs:
            e, w = np.array(errs), np.array(weights)
            contrib = e * w / (e * w).sum()
            top = np.argsort(contrib)[::-1][:5]
            rows.append({'source': f'Pew 2015 report, {label}', 'countries': len(e),
                         'popw_tv_pp': 100 * float(np.average(e, weights=w)), 'mean_tv_pp': 100 * float(e.mean()),
                         'median_tv_pp': 100 * float(np.median(e)),
                         'largest_contributors': ', '.join(
                             f'{codes[j]} {100 * contrib[j]:.0f}%' for j in top)})
    return pd.DataFrame(rows)


def _pew_country_codes(ctx, names):
    """Match Pew's country names to ISO3 codes through the Natural Earth names already loaded."""
    import difflib
    known = {}
    for c in ctx.ids:
        known[c] = c
    ne = getattr(ctx, 'country_name', None)
    if ne is not None:
        for c, nm in zip(ctx.ids, ne):
            known[str(nm).lower()] = c
    out = {}
    lowered = {k.lower(): v for k, v in known.items()}
    for nm in names:
        key = nm.lower().strip()
        if key in lowered:
            out[nm] = lowered[key]
            continue
        hit = difflib.get_close_matches(key, list(lowered), n=1, cutoff=0.92)
        if hit:
            out[nm] = lowered[hit[0]]
    return out
