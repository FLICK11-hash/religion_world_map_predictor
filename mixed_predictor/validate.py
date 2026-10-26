"""Does it actually forecast? Forward-chaining backtest against two baselines.

The rule that makes this honest: to predict year T we may only use observations up to some cut
year c < T. The model is refitted from scratch at every cut, so nothing after the cut leaks in.
The damping half-life is a free parameter, so it gets the same treatment -- it is chosen on the
early cuts only, and the last cut is kept back to report a number that no fitting has seen.

Two baselines, because "my model has some error" means nothing without them:
  persistence  shares frozen at the last observed year. Hard to beat over short horizons.
  undamped     the same log trend with no decay. This is the manual predictor's strategy, and
               the research model measured it as worse than persistence on the same history.

Errors are in percentage points. The headline is total variation distance, which for a
composition is half the sum of the absolute share errors -- read it as "percent of the world's
population placed in the wrong group".
"""
from __future__ import annotations

import statistics

from model import fit, predict

MIN_TRAIN = 4          # observations needed before a cut is usable
STRATEGIES = ("persistence", "manual", "undamped", "damped")
HALF_LIFE_GRID = [0, 5, 10, 15, 20, 30, 40, 60, 80, 120, 200, 400, None]


def total_variation(predicted: dict, actual: dict, groups: list[str]) -> float:
    return 50.0 * sum(abs(predicted[g] - actual[g]) for g in groups)


def manual_algorithm(train_years, shares, groups, target_year) -> dict:
    """The manual predictor's arithmetic, reimplemented so it can be scored on the same data.

    Average the annual change in each share across consecutive intervals, extend it linearly,
    clip anything negative to zero, renormalise. Scoring this alongside the others separates two
    different improvements: better data, and a better method. Give the manual method good data and
    it still carries the clip, which is irreversible -- once a group reaches zero it stays there.
    """
    last = train_years[-1]
    per_year = {}
    for group in groups:
        steps = [(shares[b][group] - shares[a][group]) / (b - a)
                 for a, b in zip(train_years, train_years[1:])]
        per_year[group] = sum(steps) / len(steps)
    elapsed = target_year - last
    raw = {g: max(shares[last][g] + per_year[g] * elapsed, 0.0) for g in groups}
    total = sum(raw.values())
    return {g: v / total for g, v in raw.items()} if total else dict(shares[last])


def _forecast(years, shares, groups, cut_index, target_year, half_life, strategy):
    train_years = years[: cut_index + 1]
    if strategy == "persistence":
        return dict(shares[train_years[-1]])
    if strategy == "manual":
        return manual_algorithm(train_years, shares, groups, target_year)
    trends = fit(train_years, shares, groups)
    return predict(trends, train_years[-1], target_year,
                   None if strategy == "undamped" else half_life)


def backtest(years, shares, groups, half_life, strategy="damped", cut_indices=None) -> list[dict]:
    """One record per (cut, target year, group)."""
    cuts = cut_indices if cut_indices is not None else range(MIN_TRAIN - 1, len(years) - 1)
    records = []
    for cut_index in cuts:
        cut_year = years[cut_index]
        for target_year in years[cut_index + 1:]:
            predicted = _forecast(years, shares, groups, cut_index, target_year, half_life, strategy)
            for group in groups:
                records.append({
                    "cut_year": cut_year,
                    "target_year": target_year,
                    "horizon_years": target_year - cut_year,
                    "group": group,
                    "predicted_pct": 100.0 * predicted[group],
                    "actual_pct": 100.0 * shares[target_year][group],
                    "error_pp": 100.0 * (predicted[group] - shares[target_year][group]),
                })
    return records


def composition_errors(records: list[dict], groups: list[str]) -> list[dict]:
    """Collapse per-group records into one total-variation error per (cut, target)."""
    keyed: dict[tuple, dict] = {}
    for r in records:
        key = (r["cut_year"], r["target_year"])
        keyed.setdefault(key, {})[r["group"]] = (r["predicted_pct"], r["actual_pct"])
    out = []
    for (cut_year, target_year), pairs in sorted(keyed.items()):
        out.append({
            "cut_year": cut_year,
            "target_year": target_year,
            "horizon_years": target_year - cut_year,
            "total_variation_pp": 0.5 * sum(abs(p - a) for p, a in pairs.values()),
        })
    return out


def mean_total_variation(records, groups) -> float:
    rows = composition_errors(records, groups)
    return statistics.fmean(r["total_variation_pp"] for r in rows) if rows else float("nan")


def select_half_life(years, shares, groups, grid=None, holdout_cuts=1):
    """Pick the half-life on early cuts only; keep the last cut(s) back for reporting.

    Returns (chosen_half_life, [{half_life, selection_error_pp}], holdout_cut_indices).
    """
    grid = grid or HALF_LIFE_GRID
    usable = list(range(MIN_TRAIN - 1, len(years) - 1))
    if len(usable) <= holdout_cuts:
        raise ValueError(f"{len(usable)} usable cuts is too few to hold {holdout_cuts} back")
    selection_cuts, holdout = usable[:-holdout_cuts], usable[-holdout_cuts:]

    scored = []
    for half_life in grid:
        records = backtest(years, shares, groups, half_life, "damped", selection_cuts)
        scored.append({"half_life": half_life,
                       "selection_error_pp": mean_total_variation(records, groups)})
    best = min(scored, key=lambda row: row["selection_error_pp"])
    return best["half_life"], scored, holdout


def compare_strategies(years, shares, groups, half_life, cut_indices=None) -> list[dict]:
    """Mean total-variation error for the model and both baselines, on the same cuts."""
    out = []
    for strategy in STRATEGIES:
        records = backtest(years, shares, groups, half_life, strategy, cut_indices)
        rows = composition_errors(records, groups)
        errors = [r["total_variation_pp"] for r in rows]
        out.append({
            "strategy": strategy,
            "half_life": half_life if strategy == "damped" else (None if strategy == "undamped" else 0),
            "forecasts": len(errors),
            "mean_error_pp": statistics.fmean(errors),
            "worst_error_pp": max(errors),
        })
    return out


def error_by_group(records: list[dict], groups: list[str]) -> list[dict]:
    """Per-group accuracy. Small groups are measured worst and predicted worst; showing one
    average hides that, so the per-group table is reported alongside it."""
    out = []
    for group in groups:
        mine = [r for r in records if r["group"] == group]
        out.append({
            "group": group,
            "mean_abs_error_pp": statistics.fmean(abs(r["error_pp"]) for r in mine),
            "mean_share_pct": statistics.fmean(r["actual_pct"] for r in mine),
        })
    for row in out:
        row["error_relative_to_share"] = (row["mean_abs_error_pp"] / row["mean_share_pct"]
                                          if row["mean_share_pct"] else float("nan"))
    return sorted(out, key=lambda r: -r["mean_abs_error_pp"])


def error_by_horizon(records: list[dict], groups: list[str]) -> list[dict]:
    """What the model's error actually was at each horizon -- the basis for any uncertainty claim."""
    rows = composition_errors(records, groups)
    out = []
    for horizon in sorted({r["horizon_years"] for r in rows}):
        errors = sorted(r["total_variation_pp"] for r in rows if r["horizon_years"] == horizon)
        per_group = sorted(abs(r["error_pp"]) for r in records if r["horizon_years"] == horizon)
        out.append({
            "horizon_years": horizon,
            "forecasts": len(errors),
            "mean_error_pp": statistics.fmean(errors),
            "worst_error_pp": errors[-1],
            "group_error_p90_pp": per_group[min(int(0.9 * len(per_group)), len(per_group) - 1)],
        })
    return out


def cross_validated_comparison(years, shares, groups, grid=None) -> list[dict]:
    """Leave-one-cut-out: the fairest comparison available on nine observations.

    select_half_life keeps back the last cut only, which leaves a single-digit number of scored
    forecasts and an answer that moves if you shift the split. This instead holds out each cut in
    turn, re-chooses the half-life on the remaining cuts, and scores the held-out one. Every cut
    gets evaluated, and the half-life never sees the cut it is judged on.

    The baselines have no parameters to tune, so their numbers are identical either way -- which
    is the point: this puts the damped model on the same footing rather than giving it the
    advantage of picking its half-life on the data it is scored against.
    """
    grid = grid or HALF_LIFE_GRID
    usable = list(range(MIN_TRAIN - 1, len(years) - 1))
    per_fold = []
    for held_out in usable:
        others = [c for c in usable if c != held_out]
        scored = [(half_life,
                   mean_total_variation(backtest(years, shares, groups, half_life, "damped", others),
                                        groups))
                  for half_life in grid]
        chosen = min(scored, key=lambda row: row[1])[0]
        fold = {"held_out_cut": years[held_out], "chosen_half_life": chosen}
        for strategy in STRATEGIES:
            records = backtest(years, shares, groups, chosen, strategy, [held_out])
            fold[strategy] = mean_total_variation(records, groups)
        per_fold.append(fold)

    summary = []
    for strategy in STRATEGIES:
        values = [f[strategy] for f in per_fold]
        summary.append({
            "strategy": strategy,
            "folds": len(values),
            "cv_mean_error_pp": statistics.fmean(values),
            "cv_worst_error_pp": max(values),
            "beats_persistence": sum(1 for f in per_fold if f[strategy] < f["persistence"]),
        })
    return summary, per_fold
