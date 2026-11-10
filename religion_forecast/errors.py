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
  estimated: b from the regression of log|e| on log(s(1 - s) + eps) at ten years (small shares
  move less), beta from the growth of the mean absolute standardised error with horizon.

3 Draw. A predictive draw takes one Monte Carlo run of the model and adds
  (h / 10)^beta * g(s) * u, with u resampled from the ten-year record in two stages: one
  historical decade is drawn for the whole world, then each country takes the standardised error
  vector (all eight religions together) of a country drawn at random from that decade. Drawing
  the decade first keeps the common shock every country shared in it, which is what matters for
  world totals; drawing the country within it gives each cell the whole pooled distribution rather
  than the few errors its own history supplies. Shares are then clipped at zero and renormalised.

4 Validate. Leave one origin out: b, beta and the resampling pool are re-estimated without it,
  and its forecasts are scored for coverage and for the interval score of Gneiting and Raftery
  (2007), against the parameter-only intervals.

The record's longest horizon is 40 years, so the growth law is an extrapolation beyond 2060, and
the predictive intervals are reported to 2100 and no further.
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
    jobs = [('WRP', t0, [h for h in range(10, last - t0 + 1, 10)]) for t0 in origins]
    if ctx.s2010 is not None:
        jobs.append(('Pew', 2010, [10]))
    for source, t0, horizons in jobs:
        train = [w for w in wins if w['source'] == 'WRP' and w['end'] <= t0]
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
            idx = hier.sample_indices(rng, 1)[:, 0]
            path = SM.hindcast(ctx, p, t0, s0, years=max(years) - t0, hier=hier, draw_idx=idx, path=years)
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


def fit(rec, exclude=None):
    """Estimate b, beta and the resampling pool from the record, leaving out the entries whose
    (source, origin) is `exclude`. Returns a dict (the model)."""
    use = [x for x in rec if (x['source'], x['origin']) != exclude]
    base = [x for x in use if x['horizon'] == BASE_H]
    if not base:
        raise ValueError('the error record has no ten-year forecasts')
    # b: log|e| on log(s(1 - s) + eps) over every observed ten-year cell
    xs, ys = [], []
    for x in base:
        m = x['mask']
        centre = x['samples'][:, m].mean(0)
        e = np.abs(x['obs'][m] - centre)
        keep = e > 1e-7
        xs.append(np.log(centre * (1 - centre) + EPS)[keep])
        ys.append(np.log(e[keep]))
    X, Y = np.concatenate(xs), np.concatenate(ys)
    b = float(np.polyfit(X, Y, 1)[0])
    b = float(np.clip(b, 0.0, 1.0))
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
    else:
        beta = 0.5                                     # random-walk growth when there is no record
    beta = float(np.clip(beta, 0.0, 1.0))
    # resampling pool: one block per ten-year forecast, each country's standardised error vector
    blocks = []
    for x in base:
        m = x['mask']
        centre = x['samples'].mean(0)
        u = np.full((len(m), K), np.nan)
        u[m] = (x['obs'][m] - centre[m]) / _scale(centre[m], b)
        blocks.append(dict(label=f"{x['source']} {x['origin']}-{x['target']}", u=u, mask=m.copy()))
    return dict(b=b, beta=beta, eps=EPS, base_horizon=BASE_H, mean_abs_standardised_error=mean_abs,
                cells=cells, blocks=blocks, excluded=None if exclude is None else f'{exclude[0]} {exclude[1]}')


def growth(model, h):
    return (max(float(h), 1e-9) / model['base_horizon']) ** model['beta']


def predictive(samples, horizon, model, rng, draws=10):
    """Predictive draws [R * draws, n, K] from model draws `samples` [R, n, K] at `horizon` years."""
    R, n, _ = samples.shape
    blocks = model['blocks']
    g = growth(model, horizon)
    out = np.empty((R * draws, n, K))
    for j in range(R * draws):
        blk = blocks[rng.integers(len(blocks))]
        obs_rows = np.flatnonzero(blk['mask'])
        u = blk['u'][obs_rows[rng.integers(len(obs_rows), size=n)]]
        s = samples[j // draws]
        x = np.clip(s + g * _scale(s, model['b']) * u, 0.0, None)
        out[j] = x / np.maximum(x.sum(1, keepdims=True), 1e-300)
    return out


# --------------------------------------------------------------------------------- scoring
def interval_score(lo, hi, obs, alpha):
    """Gneiting and Raftery's interval score for a central (1 - alpha) interval (lower is better):
    width plus 2/alpha times the distance by which the observation falls outside."""
    return (hi - lo) + (2.0 / alpha) * np.maximum(lo - obs, 0.0) + (2.0 / alpha) * np.maximum(obs - hi, 0.0)


def _score_draws(draws, x, levels=LEVELS):
    m = x['mask']
    obs = x['obs'][m]
    d = draws[:, m]
    w = np.repeat(x['pop'][m][:, None], K, axis=1)
    rows = []
    for lev in levels:
        a = 1.0 - lev
        lo, hi = np.quantile(d, a / 2, axis=0), np.quantile(d, 1 - a / 2, axis=0)
        inside = (obs >= lo) & (obs <= hi)
        rows.append(dict(nominal=lev, coverage=float(inside.mean()),
                         coverage_population_weighted=float(np.average(inside, weights=w)),
                         interval_score_pp=100 * float(interval_score(lo, hi, obs, a).mean()),
                         median_width_pp=100 * float(np.median(hi - lo))))
    # the same for world shares (the population-weighted total of the observed countries)
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


def validate(rec, seed=None, draws=25, log=print):
    """Leave-one-origin-out coverage and interval score of the parameter-only and the
    error-calibrated intervals, at every horizon the held-out origin has."""
    seed = 2026 if seed is None else seed
    rows, world_rows = [], []
    for source, origin in sorted({(x['source'], x['origin']) for x in rec}):
        model = fit(rec, exclude=(source, origin))
        for x in [y for y in rec if (y['source'], y['origin']) == (source, origin)]:
            rng = np.random.default_rng([seed, origin, x['horizon']])
            for method, d in (('model draws (parameter uncertainty)', x['samples']),
                              ('error-calibrated', predictive(x['samples'], x['horizon'], model, rng, draws))):
                cells, world = _score_draws(d, x)
                base = dict(window=f"{source} {origin}-{x['target']}", source=source, origin=origin,
                            horizon=x['horizon'], method=method, countries=int(x['mask'].sum()),
                            b=model['b'], beta=model['beta'])
                rows += [dict(base, **c) for c in cells]
                for wr in world:
                    for k, inside in enumerate(wr['inside']):
                        world_rows.append(dict(base, nominal=wr['nominal'], religion=CATS[k], inside=inside,
                                               interval_score_pp=wr['interval_score_pp']))
        log(f'  validated held-out origin {source} {origin}')
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
                        **{f'm{i}': blk['mask'] for i, blk in enumerate(model['blocks'])})


def load(path=None):
    """The fitted model saved by `save`, or None if the backtest has not been run."""
    path = path or config.VALIDATION
    jp, npz = path / 'forecast_error_model.json', path / 'forecast_error_pool.npz'
    if not (jp.exists() and npz.exists()):
        return None
    meta = json.loads(jp.read_text(encoding='utf8'))
    z = np.load(npz)
    meta['blocks'] = [dict(label=lab, u=z[f'u{i}'], mask=z[f'm{i}']) for i, lab in enumerate(meta['blocks'])]
    return meta


def load_or_build(ctx, runs=40, log=print):
    model = load()
    if model is not None and all(len(b['mask']) == ctx.n for b in model['blocks']):
        return model
    log('No forecast-error model in data/validation; building it from the history record ...')
    model = fit(record(ctx, runs=runs, log=log))
    save(model)
    return model
