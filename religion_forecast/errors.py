"""Empirical forecast-error model: how far the model's past forecasts missed, by horizon, and the
predictive intervals that record implies.

The projection's Monte Carlo bands describe parameter uncertainty only. Out of sample they contain
the observed share far less often than their nominal level, because most forecast error comes from
country-level change the model has no mechanism for and from differences between rounds of
measurement. This module measures that error directly and adds it back.

1 Record. From each origin t0 = 1970, 1980, 1990, 2000 the model is run forward with everything as
  it would have been fitted at t0: switching is estimated on the World Religion Project decades
  that end by t0, and the survey cells, which postdate every origin, are not used. Each of `runs`
  Monte Carlo draws is scored against the World Religion Project at every later decade to 2010
  (horizons 10 to 40 years). When the Pew 2010 composition is available, 2010 -> 2020 adds a
  ten-year forecast scored against Pew 2020. Demography inside each window is WPP's estimate, so the
  record measures error conditional on national fertility, mortality and net migration.

2 Scale. With e the error of country c, religion k at horizon h,

      e = (h / 10)^beta * g(s) * u,      g(s) = (s (1 - s) + eps)^b,

  where s is the model's mean forecast share, u is a standardised error, and b and beta are
  estimated: b from the regression of log|e| on log(s(1 - s) + eps) at ten years over cells
  observed above zero (small shares move less), beta from the growth of the mean absolute
  standardised error with horizon.

3 Draw. A predictive draw takes one Monte Carlo run of the model and adds
  (h / 10)^beta * g(s) * u, with s the mean of the runs and u resampled from the ten-year record in two stages: one
  historical decade is drawn for the whole world, then each country takes the standardised error
  vector (all eight religions together) of one of its k = 15 nearest neighbours in that decade,
  nearest meaning the smallest total-variation distance between the two countries' forecast
  compositions (a k-nearest-neighbour bootstrap). Drawing the decade first keeps the common shock
  every country shared in it, which is what matters for world totals; drawing among neighbours
  gives each country many errors rather than the few its own history supplies, while an error
  measured on a religion that was a tiny minority is never transplanted onto a country where it
  is the majority. Shares are then clipped at zero and renormalised. On the history record this
  scored better than resampling any country, resampling within share-size classes, or aligning
  errors by rank, most of all for large shares and for world totals.

  The errors are used as recorded, not centred. Subtracting the pooled mean standardised error
  was tested: it calibrates slightly worse out of sample, and because that mean is dominated by
  the many small shares it pushes the errors of large countries in the wrong direction, moving
  world medians away from the model's central path. The record does have a consistent direction,
  the unaffiliated share observed below the forecast in every decade, which mostly reflects
  post-communist and Chinese religious revival as one source measured it, and it is carried into
  the intervals. The centred version is reported for comparison (`centred=True`).

4 Validate. For each forecast in the record, b, beta and the resampling pool are re-estimated
  from the entries that share no calendar years with it, and it is scored for coverage and for
  the interval score of Gneiting and Raftery (2007), against the parameter-only intervals
  (`validate`). A 'real-time' variant uses only entries that ended by the forecast's origin.

Out-of-sample calibration can be checked to 30 years (no 40-year forecast has a non-overlapping
entry left); the growth law is an extrapolation beyond that, and the predictive intervals are
reported to 2100 and no further.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from religion_forecast import calibration as ES
from religion_forecast import config
from religion_forecast import engine as E
from religion_forecast import model as SM

CATS, K = E.CATS, E.K
EPS = 1e-4                       # keeps the scale positive for shares of exactly 0 or 1
BASE_H = 10                      # the horizon the resampling pool is built at
MAX_REPORTED_HORIZON = 80        # 2020 -> 2100
LEVELS = (0.5, 0.8, 0.9, 0.95)
NEIGHBOURS = 15                  # k of the nearest-neighbour bootstrap


# ----------------------------------------------------------------------------- the record
def record(ctx, runs=40, seed=None, origins=(1970, 1980, 1990, 2000), last=2010, log=print):
    """Monte Carlo forecasts from each origin, scored at every later decade.

    Returns a list of dicts, one per (origin, horizon): source, origin, horizon, target (year),
    samples [runs, n, K] (the model's draws), obs [n, K] (NaN where unobserved), mask [n],
    pop [n] (WPP population at the target year)."""
    seed = ctx.a['random_seed'] if seed is None else seed
    p0 = ES.central_params(ctx)
    wins = ES.no_switching_hindcasts(ctx, p0, ES.windows(ctx, (1950, 1960, 1970, 1980, 1990, 2000)))
    out = []
    jobs = [('WRP', t0, list(range(10, last - t0 + 1, 10))) for t0 in origins]
    if ctx.s2010 is not None:
        jobs.append(('Pew', 2010, [10]))
    trains = {t0: [w for w in wins if w['source'] == 'WRP' and w['end'] <= t0] for _, t0, _ in jobs}
    ES.fit_many(ctx, [t if len(t) >= 2 else [] for t in trains.values()], use_survey=False)
    for source, t0, horizons in jobs:
        train = trains[t0]
        if len(train) < 2 or not horizons:
            continue
        hier = ES.fit_switching(ctx, train, use_survey=False)
        if source == 'WRP':
            s0_raw = ES.wrp_shares(ctx, t0)
            s0 = ES.fill_missing(ctx, s0_raw, t0)
            targets = {t0 + h: ES.wrp_shares(ctx, t0 + h) for h in horizons}
        else:
            s0_raw = ctx.s2010
            s0 = ES.fill_missing(ctx, ctx.s2010, 2010)
            targets = {2020: ctx.s2020.copy()}
        years = set(targets)
        samples = {y: np.empty((runs, ctx.n, K)) for y in years}
        for r in range(runs):
            rng = np.random.default_rng([seed, 4242, t0, r])
            p = SM.draw_run(ctx, rng, ctx.a['reference_scenario'])
            sd = ES.draw_switching(ctx, hier, r, rng)
            path = SM.hindcast(ctx, p, t0, s0, years=max(years) - t0, path=years, **sd.kwargs())
            for y in years:
                samples[y][r] = path[y]
        for y, obs in targets.items():
            mask = np.isfinite(s0_raw).all(1) & np.isfinite(obs).all(1)
            out.append(dict(source=source, origin=t0, horizon=y - t0, target=y, samples=samples[y],
                            obs=obs, mask=mask, pop=ctx.wpp_at('pop', y), train_windows=len(train)))
        log(f'  error record: {source} {t0} -> {sorted(years)} ({runs} runs, switching fitted on {len(train)} decades)')
    return out


# --------------------------------------------------------------------------- the error model
def _scale(s, b):
    return (np.clip(s, 0.0, 1.0) * (1.0 - np.clip(s, 0.0, 1.0)) + EPS) ** b


def overlaps(x, y):
    """True if forecasts x and y share any calendar years: (origin, target] intervals intersect."""
    return x['origin'] < y['target'] and y['origin'] < x['target']


def fit(rec, exclude=None, keep=None):
    """Estimate b, beta and the resampling pool from the record. `keep(entry)` selects the entries
    used; `exclude` = (source, origin) drops one origin (older interface). Returns a dict (the
    model). b is fitted on cells whose observed share is above zero: where a group is recorded at
    exactly zero the error equals the forecast by construction, which would pull b upwards. The
    resampling pool keeps every cell, zeros included, because a group recorded at zero next round
    is an outcome the intervals have to allow for."""
    use = [x for x in rec if (x['source'], x['origin']) != exclude and (keep is None or keep(x))]
    base = [x for x in use if x['horizon'] == BASE_H]
    if not base:
        raise ValueError('the error record has no ten-year forecasts')
    xs, ys = [], []
    for x in base:
        m = x['mask']
        centre = x['samples'][:, m].mean(0)
        e = np.abs(x['obs'][m] - centre)
        ok = (x['obs'][m] > 0) & (e > 1e-7)
        xs.append(np.log(centre * (1 - centre) + EPS)[ok])
        ys.append(np.log(e[ok]))
    X, Y = np.concatenate(xs), np.concatenate(ys)
    b = float(np.clip(np.polyfit(X, Y, 1)[0], 0.0, 1.0))
    # standardised errors and their size by horizon
    size = {}
    for x in use:
        m = x['mask']
        centre = x['samples'][:, m].mean(0)
        u = (x['obs'][m] - centre) / _scale(centre, b)
        size.setdefault(x['horizon'], []).append((float(np.abs(u).mean()), int(m.sum())))
    mean_abs = {h: float(np.average([a for a, _ in v], weights=[n for _, n in v])) for h, v in size.items()}
    cells = {h: int(sum(n for _, n in v)) for h, v in size.items()}
    hs = sorted(h for h in mean_abs if h > BASE_H)
    if hs:
        lx = np.log(np.array(hs, float) / BASE_H)
        ly = np.log(np.array([mean_abs[h] for h in hs]) / mean_abs[BASE_H])
        wts = np.array([cells[h] for h in hs], float)
        beta = float((wts * lx * ly).sum() / (wts * lx * lx).sum())
        beta_source = 'estimated'
    else:
        beta, beta_source = 0.5, 'no longer horizons in the data used: random-walk growth assumed'
    beta = float(np.clip(beta, 0.0, 1.0))
    # resampling pool: one block per ten-year forecast, each country's standardised error vector,
    # and the pool's mean vector (subtracted when the errors are centred)
    blocks = []
    for x in base:
        m = x['mask']
        centre = x['samples'].mean(0)
        u = np.full((len(m), K), np.nan)
        u[m] = (x['obs'][m] - centre[m]) / _scale(centre[m], b)
        blocks.append(dict(label=f"{x['source']} {x['origin']}-{x['target']}", u=u, mask=m.copy(), s=centre.copy()))
    mean_u = np.nanmean(np.concatenate([blk['u'][blk['mask']] for blk in blocks]), axis=0)
    return dict(b=b, beta=beta, beta_source=beta_source, eps=EPS, base_horizon=BASE_H, neighbours=NEIGHBOURS,
                mean_u=mean_u.tolist(), mean_abs_standardised_error=mean_abs, cells=cells, blocks=blocks,
                entries_used=len(use), excluded=None if exclude is None else f'{exclude[0]} {exclude[1]}')


def growth(model, h):
    return (max(float(h), 1e-9) / model['base_horizon']) ** model['beta']


def neighbours(centre, model, k=NEIGHBOURS):
    """For every block, each target country's k nearest observed countries [n, k] (indices into the
    block), by total-variation distance between the target's forecast composition `centre` [n, K]
    and the block's forecast compositions."""
    out = []
    for blk in model['blocks']:
        rows = np.flatnonzero(blk['mask'])
        D = 0.5 * np.abs(centre[:, None, :] - blk['s'][rows][None, :, :]).sum(2)
        kk = min(k, len(rows))
        out.append(rows[np.argsort(D, axis=1)[:, :kk]])
    return out


def predictive(samples, horizon, model, rng, draws=10, nn=None, centred=False, central=False):
    """Predictive draws [R * draws, n, K] from model draws `samples` [R, n, K] at `horizon` years:
    each model draw plus (h / 10)^beta g(s) u, with s the mean of the model draws (as when the
    errors were measured) and u from the two-stage bootstrap. `nn` (from `neighbours`) is computed
    from that mean when not given. central=True adds the errors to the mean path only, dropping the
    model's own spread (a comparison: the recorded errors were measured from the mean, so adding
    them to every draw counts the record's own parameter spread twice; that spread is 5-10% of the
    predictive width). centred=True subtracts the pooled mean standardised error (a comparison,
    not the projection's choice)."""
    R, n, _ = samples.shape
    blocks = model['blocks']
    centre = samples.mean(0)
    nn = neighbours(centre, model) if nn is None else nn
    scale = growth(model, horizon) * _scale(centre, model['b'])
    shift = np.asarray(model.get('mean_u', np.zeros(K)), float) if centred else np.zeros(K)
    out = np.empty((R * draws, n, K))
    for j in range(R * draws):
        bi = rng.integers(len(blocks))
        cand = nn[bi]
        u = blocks[bi]['u'][cand[np.arange(n), rng.integers(cand.shape[1], size=n)]] - shift
        s = centre if central else samples[j // draws]
        x = np.clip(s + scale * u, 0.0, None)
        out[j] = x / np.maximum(x.sum(1, keepdims=True), 1e-300)
    return out


# --------------------------------------------------------------------------------- scoring
def interval_score(lo, hi, obs, alpha):
    """Gneiting and Raftery's interval score for a central (1 - alpha) interval (lower is better):
    width plus 2/alpha times the distance by which the observation falls outside."""
    return (hi - lo) + (2.0 / alpha) * np.maximum(lo - obs, 0.0) + (2.0 / alpha) * np.maximum(obs - hi, 0.0)


SHARE_CLASSES = ((0.0, 0.01, 'under 1%'), (0.01, 0.05, '1-5%'), (0.05, 0.2, '5-20%'), (0.2, 1.01, '20% or more'))


def _score_draws(draws, x, levels=LEVELS):
    """Coverage and interval score of the central intervals of `draws` for the observed cells of
    record entry x: over all cells; over cells observed above zero (a group recorded at exactly
    zero is inside any interval reaching zero, which the clipping at zero makes common, so the
    all-cells figure flatters small shares); and by the forecast share (known in advance). Also
    the same for the world shares of the observed countries."""
    m = x['mask']
    obs = x['obs'][m]
    d = draws[:, m]
    w = np.repeat(x['pop'][m][:, None], K, axis=1)
    centre = d.mean(0)
    pos = obs > 0
    rows = []
    for lev in levels:
        a = 1.0 - lev
        lo, hi = np.quantile(d, a / 2, axis=0), np.quantile(d, 1 - a / 2, axis=0)
        inside = (obs >= lo) & (obs <= hi)
        isc = interval_score(lo, hi, obs, a)
        row = dict(nominal=lev, coverage=float(inside.mean()),
                   coverage_population_weighted=float(np.average(inside, weights=w)),
                   coverage_observed_above_zero=float(inside[pos].mean()),
                   interval_score_pp=100 * float(isc.mean()),
                   interval_score_above_zero_pp=100 * float(isc[pos].mean()),
                   median_width_pp=100 * float(np.median(hi - lo)), cells=int(inside.size),
                   cells_observed_zero=int((~pos).sum()))
        for lo_s, hi_s, name in SHARE_CLASSES:
            c = (centre >= lo_s) & (centre < hi_s)
            row[f'coverage_forecast_{name}'] = float(inside[c].mean()) if c.any() else np.nan
        rows.append(row)
    pw = x['pop'][m] / x['pop'][m].sum()
    wobs = (obs * pw[:, None]).sum(0)
    wd = (d * pw[None, :, None]).sum(1)
    world = []
    for lev in levels:
        a = 1.0 - lev
        lo, hi = np.quantile(wd, a / 2, axis=0), np.quantile(wd, 1 - a / 2, axis=0)
        world.append(dict(nominal=lev, inside=[bool(v) for v in (wobs >= lo) & (wobs <= hi)],
                          interval_score_pp=100 * float(interval_score(lo, hi, wobs, a).mean())))
    return rows, world


MAIN_SCHEME = 'non-overlapping'
SCHEMES = {
    # the forecast being scored shares no calendar years with any entry the error model is fitted on
    'non-overlapping': lambda x, y: not overlaps(x, y),
    # only what was known at the forecast's origin: entries that ended by then
    'real-time': lambda x, y: y['target'] <= x['origin'],
    # the earlier, optimistic design: every other origin, including decades inside the scored window
    'leave-one-origin-out (overlapping)': lambda x, y: y['origin'] != x['origin'] or y['source'] != x['source'],
}


def validate(rec, seed=None, draws=25, log=print, schemes=None):
    """Out-of-sample coverage and interval score of the predictive intervals.

    For every forecast in the record, the error model is refitted on the entries a scheme allows
    (SCHEMES) and the forecast is scored. The main scheme is 'non-overlapping': no entry the error
    model uses shares calendar years with the forecast being scored, so a decade's shock is never
    in the pool used to score it. A forecast is skipped when no ten-year entry is left (every
    40-year forecast, and the earliest origins in real time). Under the main scheme four methods
    are scored: the model's own draws (parameter uncertainty), the error-calibrated intervals as
    projected, the same with errors added to the central path only, and with centred errors.
    'real-time' and the older 'leave-one-origin-out (overlapping)' are scored for the projected
    method only."""
    seed = 2026 if seed is None else seed
    schemes = schemes or list(SCHEMES)
    rows, world_rows = [], []
    for scheme in schemes:
        allowed = SCHEMES[scheme]
        for x in rec:
            if not any(y['horizon'] == BASE_H and allowed(x, y) for y in rec):
                continue
            model = fit(rec, keep=lambda y, x=x, allowed=allowed: allowed(x, y))
            nn = neighbours(x['samples'].mean(0), model)

            def pred(x=x, model=model, nn=nn, **kw):
                rng = np.random.default_rng([seed, x['origin'], x['horizon']])
                return predictive(x['samples'], x['horizon'], model, rng, draws, nn, **kw)

            variants = [('error-calibrated', pred())]
            if scheme == schemes[0]:
                variants = [('model draws (parameter uncertainty)', x['samples'])] + variants + [
                    ('error-calibrated, central path', pred(central=True)),
                    ('error-calibrated, centred', pred(centred=True))]
            for method, d in variants:
                cells, world = _score_draws(d, x)
                base = dict(scheme=scheme, window=f"{x['source']} {x['origin']}-{x['target']}", source=x['source'],
                            origin=x['origin'], horizon=x['horizon'], method=method, countries=int(x['mask'].sum()),
                            b=model['b'], beta=model['beta'], beta_source=model['beta_source'],
                            pool_blocks=len(model['blocks']), entries_used=model['entries_used'])
                rows += [dict(base, **c) for c in cells]
                for wr in world:
                    for k, inside in enumerate(wr['inside']):
                        world_rows.append(dict(base, nominal=wr['nominal'], religion=CATS[k], inside=inside,
                                               interval_score_pp=wr['interval_score_pp']))
        log(f'  validated the predictive intervals: {scheme}')
    return pd.DataFrame(rows), pd.DataFrame(world_rows)


def record_table(rec):
    """The error record as a tidy table: one row per (origin, horizon, country, religion)."""
    rows = []
    for x in rec:
        m = x['mask']
        centre = x['samples'].mean(0)
        lo, hi = np.quantile(x['samples'], 0.05, axis=0), np.quantile(x['samples'], 0.95, axis=0)
        for i in np.flatnonzero(m):
            for k, c in enumerate(CATS):
                rows.append(dict(source=x['source'], origin=x['origin'], horizon=x['horizon'], country_index=int(i),
                                 religion=c, forecast=float(centre[i, k]), observed=float(x['obs'][i, k]),
                                 error=float(x['obs'][i, k] - centre[i, k]), model_q05=float(lo[i, k]),
                                 model_q95=float(hi[i, k]), population=float(x['pop'][i])))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------ persistence
def save(model, path=None):
    """Write the fitted model: scalars to JSON, the resampling pool to a compressed .npz."""
    path = path or config.VALIDATION
    path.mkdir(parents=True, exist_ok=True)
    meta = {k: v for k, v in model.items() if k != 'blocks'}
    meta['blocks'] = [blk['label'] for blk in model['blocks']]
    meta['mean_abs_standardised_error'] = {str(k): v for k, v in model['mean_abs_standardised_error'].items()}
    meta['cells'] = {str(k): v for k, v in model['cells'].items()}
    (path / 'forecast_error_model.json').write_text(json.dumps(meta, indent=2), encoding='utf8')
    np.savez_compressed(path / 'forecast_error_pool.npz',
                        **{f'u{i}': blk['u'] for i, blk in enumerate(model['blocks'])},
                        **{f'm{i}': blk['mask'] for i, blk in enumerate(model['blocks'])},
                        **{f's{i}': blk['s'] for i, blk in enumerate(model['blocks'])})


def load(path=None):
    """The fitted model saved by `save`, or None if the backtest has not been run."""
    path = path or config.VALIDATION
    jp, npz = path / 'forecast_error_model.json', path / 'forecast_error_pool.npz'
    if not (jp.exists() and npz.exists()):
        return None
    meta = json.loads(jp.read_text(encoding='utf8'))
    z = np.load(npz)
    if any(f's{i}' not in z for i in range(len(meta['blocks']))):
        return None                                          # saved by an older version: rebuild
    meta['blocks'] = [dict(label=lab, u=z[f'u{i}'], mask=z[f'm{i}'], s=z[f's{i}'])
                      for i, lab in enumerate(meta['blocks'])]
    return meta


def load_or_build(ctx, runs=40, log=print):
    model = load()
    if model is not None and all(len(b['mask']) == ctx.n for b in model['blocks']):
        return model
    log('No forecast-error model in data/validation; building it from the history record ...')
    model = fit(record(ctx, runs=runs, log=log))
    save(model)
    return model
