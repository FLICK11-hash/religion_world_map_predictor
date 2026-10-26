"""A damped log-share trend: one growth rate per religion, fading with a fitted half-life.

Why this shape, in one paragraph. The manual predictor averages the annual change in each share,
extrapolates it linearly, clips anything negative to zero and renormalises. Two things go wrong:
the clip is irreversible, so whichever group hits zero first stays there (it drives "Other" to
exactly 0.0 at every horizon), and an undamped straight line is the worst-performing strategy in
the research model's own backtest. This module fixes both structurally rather than by adding
machinery:

  * Fit the trend to log(share), not share, and turn predictions back into shares with a softmax.
    Shares are then strictly between 0 and 1 and sum to 1 by construction. No clipping, ever.
  * Multiply the trend by a decay with half-life H, so the cumulative drift converges instead of
    running away. H is not assumed: validate.py picks it out of sample.

H also makes the model a dial between the two baselines it has to beat. H -> infinity is plain
log-linear extrapolation; H -> 0 is "nothing changes". Choosing H on held-out history is therefore
choosing where between those two the data says to sit.
"""
from __future__ import annotations

import math

FLOOR = 1e-9  # guards log(0); the smallest real share here is Judaism at 0.0022


def fit(years: list[int], shares: dict, groups: list[str]) -> dict:
    """Least-squares trend in log-share space, anchored on the last observed year.

    Returns {group: (level, slope)}: level is the *observed* log-share at the last year and slope
    is the change in log-share per year -- a relative growth rate.

    Anchoring on the observation rather than on the regression intercept matters more than it
    looks. With the intercept, a zero half-life gives "persistence at the smoothed level", which
    is a few tenths of a point away from where the world actually was, and that offset is paid at
    every horizon; the first version of this model lost to persistence in all five
    cross-validation folds partly because of it. Anchored this way, a zero half-life reproduces
    the last observation exactly, so the family contains the persistence baseline as a special
    case and cannot do systematically worse than it.
    """
    reference = years[-1]
    offsets = [y - reference for y in years]
    mean_t = sum(offsets) / len(offsets)
    spread = sum((t - mean_t) ** 2 for t in offsets)

    trends = {}
    for group in groups:
        logs = [math.log(max(shares[y][group], FLOOR)) for y in years]
        mean_y = sum(logs) / len(logs)
        covariance = sum((t - mean_t) * (v - mean_y) for t, v in zip(offsets, logs))
        slope = covariance / spread
        anchor = math.log(max(shares[reference][group], FLOOR))
        trends[group] = (anchor, slope)
    return trends


def trend_quality(years: list[int], shares: dict, groups: list[str]) -> dict:
    """R-squared of each group's log-share trend: how straight the line actually is.

    This is what lets one parameter do the work of eight. A group whose log-share really does move
    in a straight line (Islam, 0.88 over 1970-2010) should keep its trend; one that wanders or
    reverses ("Other", 0.28) should be damped hard. Scaling the half-life by R-squared does exactly
    that, and R-squared is computed only from the years the model is allowed to see, so it carries
    no information from the future.
    """
    reference = years[-1]
    offsets = [y - reference for y in years]
    mean_t = sum(offsets) / len(offsets)
    spread = sum((t - mean_t) ** 2 for t in offsets)

    quality = {}
    for group in groups:
        logs = [math.log(max(shares[y][group], FLOOR)) for y in years]
        mean_y = sum(logs) / len(logs)
        slope = sum((t - mean_t) * (v - mean_y) for t, v in zip(offsets, logs)) / spread
        residual = sum((v - (mean_y + slope * (t - mean_t))) ** 2 for t, v in zip(offsets, logs))
        total = sum((v - mean_y) ** 2 for v in logs)
        quality[group] = max(0.0, 1.0 - residual / total) if total else 0.0
    return quality


def damped_years(horizon: float, half_life: float | None) -> float:
    """Effective elapsed time once the trend decays with the given half-life.

    The integral of 2^(-u/H) from 0 to the horizon. With no half-life this is just the horizon
    (undamped); as H shrinks it tends to 0 (frozen). It converges to H/ln2, which is the most
    drift the model will ever allow -- see long_run_limit.
    """
    if half_life is None:
        return horizon
    if half_life <= 0:
        return 0.0
    scale = half_life / math.log(2)
    return scale * (1.0 - 2.0 ** (-horizon / half_life))


def predict(trends: dict, reference_year: int, year: int, half_life) -> dict:
    """Shares for one future year. Strictly positive, sums to exactly 1.

    half_life may be a single number (or None for no damping) applied to every group, or a dict
    giving each group its own -- see trend_quality.
    """
    horizon = year - reference_year
    if isinstance(half_life, dict):
        elapsed = {g: damped_years(horizon, half_life[g]) for g in trends}
    else:
        shared = damped_years(horizon, half_life)
        elapsed = {g: shared for g in trends}
    logs = {g: level + slope * elapsed[g] for g, (level, slope) in trends.items()}
    biggest = max(logs.values())  # subtract the max before exp: standard softmax guard
    weights = {g: math.exp(v - biggest) for g, v in logs.items()}
    total = sum(weights.values())
    return {g: w / total for g, w in weights.items()}


def fitted(trends: dict, reference_year: int, year: int) -> dict:
    """The trend evaluated inside the observed window, undamped -- for history-vs-fit tables."""
    return predict(trends, reference_year, year, half_life=None)


def long_run_limit(trends: dict, half_life: float | None) -> dict:
    """Where the damped model settles. Infinite horizon, so the answer is finite unless H is None."""
    if half_life is None:
        return {g: float("inf") if slope > 0 else 0.0 for g, (_, slope) in trends.items()}
    scale = half_life / math.log(2)
    logs = {g: level + slope * scale for g, (level, slope) in trends.items()}
    biggest = max(logs.values())
    weights = {g: math.exp(v - biggest) for g, v in logs.items()}
    total = sum(weights.values())
    return {g: w / total for g, w in weights.items()}


def relative_change_per_decade(trends: dict) -> dict:
    """The slope as a readable number: percent change in the share per decade, relative."""
    return {g: 100.0 * (math.exp(10.0 * slope) - 1.0) for g, (_, slope) in trends.items()}
