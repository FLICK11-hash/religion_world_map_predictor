"""World religious composition: a small, validated forecast.

    python main.py                 the forecast, with the evidence for it
    python main.py validate        the full backtest tables
    python main.py selftest        assertions that the constraints hold
    python main.py methodology     audit of the validation itself, with the corrected result
    python main.py rebuild-data    regenerate world_shares_wrp.csv from the raw WRP file

Standard library only. Reads one committed CSV. Writes results/.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import data
import model
import validate

RESULTS = Path(__file__).resolve().parent / "results"
HORIZONS = [2030, 2050, 2100]
BEYOND_VALIDATION = [2500, 3026]   # the other two implementations report these; see README


def _write_csv(name: str, rows: list[dict]) -> Path:
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / name
    if rows:
        with path.open("w", newline="", encoding="utf8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return path


def _rule(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def _share_row(label: str, shares: dict, groups: list[str], extra: str = "") -> str:
    return f"{label:<10}" + "".join(f"{100 * shares[g]:>9.2f}" for g in groups) + extra


def report(args) -> int:
    years, shares, provenance = data.load()
    groups = data.GROUPS

    print("WORLD RELIGIOUS COMPOSITION - mixed predictor")
    print(f"Data: {provenance.get('source')}, {provenance.get('start_year')}-{provenance.get('end_year')}, "
          f"{provenance.get('observations')} observations")
    print(f"Panel: {provenance.get('countries')} countries present in every year, covering "
          f"{float(provenance.get('coverage_2010_pct', 'nan')):.1f}% of 2010 world population")

    header = f"{'':<10}" + "".join(f"{g[:8]:>9}" for g in groups)

    _rule("OBSERVED HISTORY (percent of the panel's population)")
    print(header)
    for year in years:
        print(_share_row(str(year), shares[year], groups))

    trends = model.fit(years, shares, groups)
    _rule("FITTED TREND (percent change in each share per decade, relative)")
    per_decade = model.relative_change_per_decade(trends)
    print(f"{'':<10}" + "".join(f"{per_decade[g]:>+9.1f}" for g in groups))

    summary, folds = validate.cross_validated_comparison(years, shares, groups)
    _rule(f"MODEL SELECTION (leave-one-cut-out cross-validation, {len(folds)} folds)")
    print(f"{'strategy':<14}{'mean err pp':>12}{'worst pp':>10}{'beats persistence':>20}")
    for row in summary:
        beats = "-" if row["strategy"] == "persistence" else f"{row['beats_persistence']}/{row['folds']}"
        print(f"{row['strategy']:<14}{row['cv_mean_error_pp']:>12.3f}"
              f"{row['cv_worst_error_pp']:>10.3f}{beats:>20}")
    best = min(summary, key=lambda r: r["cv_mean_error_pp"])
    print(f"\nLowest cross-validated error: {best['strategy']} "
          f"({best['cv_mean_error_pp']:.3f} pp). Half-life chosen per fold: "
          f"{[f['chosen_half_life'] for f in folds]}")

    half_life, scored, _ = validate.select_half_life(years, shares, groups, holdout_cuts=1)
    print(f"Half-life refitted on every usable cut for the published forecast: {half_life} years")

    records = validate.backtest(years, shares, groups, half_life)
    _rule("MEASURED ERROR BY HORIZON (this model, all cuts)")
    print(f"{'horizon':>8}{'forecasts':>11}{'mean pp':>9}{'worst pp':>10}{'group p90 pp':>14}")
    horizon_rows = validate.error_by_horizon(records, groups)
    for row in horizon_rows:
        print(f"{row['horizon_years']:>8}{row['forecasts']:>11}{row['mean_error_pp']:>9.2f}"
              f"{row['worst_error_pp']:>10.2f}{row['group_error_p90_pp']:>14.2f}")

    _rule("ACCURACY BY GROUP (mean absolute error, all cuts)")
    print(f"{'group':<18}{'mean share %':>13}{'error pp':>10}{'error/share':>13}")
    group_rows = validate.error_by_group(records, groups)
    for row in group_rows:
        print(f"{row['group']:<18}{row['mean_share_pct']:>13.2f}{row['mean_abs_error_pp']:>10.2f}"
              f"{row['error_relative_to_share']:>13.2f}")
    worst, best_group = group_rows[0], group_rows[-1]
    print(f"\nAbsolute error is largest for {worst['group']} ({worst['mean_abs_error_pp']:.2f} pp). "
          f"Relative to its own size it is largest for "
          f"{max(group_rows, key=lambda r: r['error_relative_to_share'])['group']}.")

    _rule("FORECAST (percent of population)")
    print(header)
    print(_share_row(f"{years[-1]}*", shares[years[-1]], groups, "   observed"))
    forecast_rows = []
    for year in HORIZONS + BEYOND_VALIDATION:
        predicted = model.predict(trends, years[-1], year, half_life)
        note = "   beyond validated range" if year in BEYOND_VALIDATION else ""
        print(_share_row(str(year), predicted, groups, note))
        forecast_rows.append({"year": year,
                              "within_validated_range": year not in BEYOND_VALIDATION,
                              **{g: round(100 * predicted[g], 4) for g in groups}})
    limit = model.long_run_limit(trends, half_life)
    print(_share_row("limit", limit, groups, "   where the damped trend settles"))

    # The three strategies scored 3.003 / 3.043 / 3.299 pp in cross-validation -- close enough
    # that publishing one of them as "the" answer would claim a precision the nine observations
    # do not support. The spread between them is the honest statement of model uncertainty.
    _rule("THE SAME YEARS UNDER EACH VALIDATED STRATEGY")
    print(header)
    spread_rows = []
    for year in (2050, 2100):
        options = {
            "damped": model.predict(trends, years[-1], year, half_life),
            "undamped": model.predict(trends, years[-1], year, None),
            "persistence": dict(shares[years[-1]]),
            "manual": validate.manual_algorithm(years, shares, groups, year),
        }
        for name, predicted in options.items():
            print(_share_row(f"{year} {name[:4]}", predicted, groups))
            spread_rows.append({"year": year, "strategy": name,
                                **{g: round(100 * predicted[g], 4) for g in groups}})
        widest = max(groups, key=lambda g: max(o[g] for o in options.values())
                     - min(o[g] for o in options.values()))
        span = 100 * (max(o[widest] for o in options.values())
                      - min(o[widest] for o in options.values()))
        print(f"{'':<10}strategies disagree most about {widest}: {span:.1f} pp at {year}")
    _write_csv("forecast_by_strategy.csv", spread_rows)

    longest = max(r["horizon_years"] for r in horizon_rows)
    print(f"\nThe longest horizon ever tested here is {longest} years, scored by "
          f"{horizon_rows[-1]['forecasts']} forecast(s), mean error "
          f"{horizon_rows[-1]['mean_error_pp']:.2f} pp.")
    print(f"Every figure past {years[-1] + longest} is extrapolation beyond anything measured.")
    spread = max(100 * abs(model.predict(trends, years[-1], 2100, None)[g]
                           - model.predict(trends, years[-1], 2100, half_life)[g])
                 for g in groups)
    print(f"\nREAD THE FLAT ROWS AS 'NO INFORMATION', NOT 'NO CHANGE'. The rows above barely move "
          f"because\nthe selected half-life is short, and it is short because nine observations "
          f"cannot settle it:\nfour strategies score within "
          f"{max(r['cv_mean_error_pp'] for r in summary) - min(r['cv_mean_error_pp'] for r in summary):.2f} pp "
          f"of each other yet disagree by up to {spread:.1f} pp at 2100.\nThis model has no "
          f"mechanism -- no births, deaths, migration or conversion -- so a flat answer is what a\n"
          f"trend fitted to {len(years)} global aggregates can support, not a claim about the world.")

    _write_csv("forecast.csv", forecast_rows)
    _write_csv("validation_cross_validated.csv", summary)
    _write_csv("validation_folds.csv", folds)
    _write_csv("validation_by_horizon.csv", horizon_rows)
    _write_csv("validation_by_group.csv", group_rows)
    _write_csv("history_vs_forecast.csv", [
        {"year": y, "kind": "observed", **{g: round(100 * shares[y][g], 4) for g in groups}}
        for y in years
    ] + [
        {"year": r["year"], "kind": "forecast", **{g: r[g] for g in groups}}
        for r in forecast_rows
    ])
    print(f"\nWrote {len(list(RESULTS.glob('*.csv')))} CSVs to {RESULTS}")
    return 0


def show_validation(args) -> int:
    years, shares, groups = (*data.load()[:2], data.GROUPS)
    half_life, scored, holdout = validate.select_half_life(years, shares, groups, holdout_cuts=1)

    _rule("HALF-LIFE SELECTION CURVE (early cuts only)")
    print(f"{'half-life':>10}{'error pp':>11}")
    for row in scored:
        print(f"{str(row['half_life']):>10}{row['selection_error_pp']:>11.3f}")

    _rule("EVERY BACKTEST FORECAST (chosen half-life)")
    print(f"{'cut':>6}{'target':>8}{'horizon':>9}{'total variation pp':>20}")
    for row in validate.composition_errors(validate.backtest(years, shares, groups, half_life), groups):
        print(f"{row['cut_year']:>6}{row['target_year']:>8}{row['horizon_years']:>9}"
              f"{row['total_variation_pp']:>20.3f}")

    summary, folds = validate.cross_validated_comparison(years, shares, groups)
    _rule("CROSS-VALIDATED FOLDS")
    print(f"{'held out':>9}{'half-life':>11}" + "".join(f"{s:>13}" for s in validate.STRATEGIES))
    for f in folds:
        print(f"{f['held_out_cut']:>9}{str(f['chosen_half_life']):>11}"
              + "".join(f"{f[s]:>13.3f}" for s in validate.STRATEGIES))
    return 0


def selftest(args) -> int:
    """The properties the model is supposed to guarantee, checked rather than asserted in prose."""
    years, shares, provenance = data.load()
    groups = data.GROUPS
    trends = model.fit(years, shares, groups)
    checks = []

    def check(name, condition):
        checks.append((name, bool(condition)))

    check("history sums to 1 in every year",
          all(abs(sum(shares[y].values()) - 1) < 1e-12 for y in years))
    check("history has no zero or negative share",
          all(v > 0 for y in years for v in shares[y].values()))

    far = [2030, 2100, 3026, 12026]
    for year in far:
        p = model.predict(trends, years[-1], year, 60)
        check(f"{year}: shares sum to 1", abs(sum(p.values()) - 1) < 1e-12)
        check(f"{year}: every share strictly inside (0, 1)",
              all(0 < v < 1 for v in p.values()))

    frozen = model.predict(trends, years[-1], 3026, 0)
    check("zero half-life reproduces the last observation exactly",
          max(abs(frozen[g] - shares[years[-1]][g]) for g in groups) < 1e-12)

    undamped_far = model.predict(trends, years[-1], 3026, None)
    damped_far = model.predict(trends, years[-1], 3026, 60)
    moved = lambda p: sum(abs(p[g] - shares[years[-1]][g]) for g in groups)
    check("damping moves the composition less than no damping",
          moved(damped_far) < moved(undamped_far))

    limit = model.long_run_limit(trends, 60)
    check("the damped forecast converges to its stated limit",
          max(abs(model.predict(trends, years[-1], 20000, 60)[g] - limit[g]) for g in groups) < 1e-9)

    summary, folds = validate.cross_validated_comparison(years, shares, groups)
    scores = {row["strategy"]: row["cv_mean_error_pp"] for row in summary}
    check("the backtest scores every strategy", set(scores) == set(validate.STRATEGIES))
    check("cross-validated error is reported in plausible units (0-50 pp)",
          all(0 < v < 50 for v in scores.values()))

    # The headline structural claim: the manual algorithm's clip is irreversible and this model
    # has no clip. Checked on real data rather than argued for in the README.
    manual_2100 = validate.manual_algorithm(years, shares, groups, 2100)
    check("the manual algorithm does drive a group to exactly zero by 2100",
          any(v == 0.0 for v in manual_2100.values()))
    check("this model never does, at any horizon",
          all(model.predict(trends, years[-1], y, None)[g] > 0
              for y in (2100, 3026, 12026) for g in groups))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} passed")
    if failed:
        print("FAILED: " + "; ".join(failed), file=sys.stderr)
    return 1 if failed else 0


def methodology(args) -> int:
    """Audit of the validation itself. Reproduces why the headline comparison does not hold.

    Separate from `selftest` on purpose: selftest checks the model's guaranteed properties and is
    unchanged. This checks whether the *evaluation* is sound, and reports the corrected result.
    """
    import copy
    years, shares, _ = data.load()
    groups = data.GROUPS
    checks = []

    def check(name, condition):
        checks.append((name, bool(condition)))

    _rule("1. LEAKAGE IN THE ORIGINAL CROSS-VALIDATION")
    usable = list(range(validate.MIN_TRAIN - 1, len(years) - 1))
    leaked = total = 0
    for h in usable:
        test = set(years[h + 1:])
        tuning = set().union(*(set(years[c + 1:]) for c in usable if c != h))
        leaked += len(test & tuning)
        total += len(test)
    print(f"{leaked} of {total} test targets ({100 * leaked / total:.0f}%) are also scored when the "
          f"half-life is tuned,\nso each fold's half-life is chosen with knowledge of its own answers.")

    _rule("2. LEAKAGE-FREE NESTED FORWARD-CHAINING")
    summary, folds = validate.nested_forward_comparison(years, shares, groups)
    print(f"{'cut':>5}{'half-life':>11}{'tuned on':>10}" + "".join(f"{s:>12}" for s in validate.STRATEGIES))
    for f in folds:
        print(f"{f['cut_year']:>5}{str(f['chosen_half_life']):>11}{f['inner_forecasts_used_for_tuning']:>7} fc"
              + "".join(f"{f[s]:>12.3f}" for s in validate.STRATEGIES))
    print()
    for r in summary:
        print(f"  {r['strategy']:12} mean {r['mean_error_pp']:.3f} pp   beats persistence "
              f"{r['beats_persistence']}/{r['folds']}")

    _rule("3. IS ANY STRATEGY DISTINGUISHABLE FROM PERSISTENCE?")
    tests = []
    print(f"{'strategy':12}{'n':>3}{'mean gain pp':>14}{'p two-sided':>13}{'smallest p possible':>21}")
    for st in [s for s in validate.STRATEGIES if s != "persistence"]:
        t = validate.sign_flip_test([f["persistence"] - f[st] for f in folds])
        tests.append({"strategy": st, **t})
        print(f"{st:12}{t['n']:>3}{t['mean_difference']:>+14.3f}{t['p_value_two_sided']:>13.3f}"
              f"{t['smallest_attainable_p']:>21.3f}")
    floor = tests[0]["smallest_attainable_p"]
    print(f"\nWith {tests[0]['n']} leakage-free folds no paired test can return p below {floor:.3f}, "
          f"so no strategy\ncan be shown to beat persistence at the 5% level, whatever the data say.")

    _rule("4. LEAKAGE TEST: PERTURB ONLY THE FUTURE")
    base_nested = {f["cut_year"]: f["chosen_half_life"] for f in folds}
    _, orig = validate.cross_validated_comparison(years, shares, groups)
    base_orig = {f["held_out_cut"]: f["chosen_half_life"] for f in orig}
    moved_nested, moved_orig = [], []
    for cut in sorted(base_orig):
        altered = copy.deepcopy(shares)
        for yr in years:
            if yr > cut:
                altered[yr]["Islam"] *= 1.6
                altered[yr]["Unaffiliated"] /= 1.6
                tot = sum(altered[yr].values())
                altered[yr] = {g: v / tot for g, v in altered[yr].items()}
        _, pn = validate.nested_forward_comparison(years, altered, groups)
        _, po = validate.cross_validated_comparison(years, altered, groups)
        if cut in base_nested:
            moved_nested.append(base_nested[cut] != {f["cut_year"]: f["chosen_half_life"] for f in pn}[cut])
        moved_orig.append(base_orig[cut] != {f["held_out_cut"]: f["chosen_half_life"] for f in po}[cut])
    print(f"Altering only data after each cut moved the chosen half-life in "
          f"{sum(moved_orig)}/{len(moved_orig)} folds of the original CV and "
          f"{sum(moved_nested)}/{len(moved_nested)} folds of the nested one.")

    check("the original CV leaks: most test targets are used in tuning", leaked / total > 0.5)
    check("the nested CV's half-life never depends on data after its cut", not any(moved_nested))
    check("the original CV's half-life does depend on data after its cut", any(moved_orig))
    check("the nested CV uses only cuts that can be tuned from the past", len(folds) < len(usable))
    check("no strategy can reach p < 0.05 with this many folds", floor > 0.05)

    _write_csv("methodology_nested_folds.csv", folds)
    _write_csv("methodology_nested_summary.csv", summary)
    _write_csv("methodology_significance.csv", tests)
    half_life, _, _ = validate.select_half_life(years, shares, groups, holdout_cuts=1)
    _write_csv("methodology_by_horizon.csv", validate.horizon_matched(years, shares, groups, half_life))

    _rule("METHODOLOGY CHECKS")
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    failed = [n for n, ok in checks if not ok]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} passed")
    return 1 if failed else 0


def rebuild(args) -> int:
    years, shares, provenance = data.build_from_raw(start_year=args.start_year)
    data.save(years, shares, provenance)
    print(f"Rebuilt {data.DERIVED.name}: {provenance['observations']} observations "
          f"({provenance['start_year']}-{provenance['end_year']}), "
          f"{provenance['countries']} countries, "
          f"{provenance['coverage_2010_pct']:.1f}% of 2010 world population")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("forecast", help="the forecast and the evidence for it (default)")
    sub.add_parser("validate", help="full backtest tables")
    sub.add_parser("selftest", help="check the model's guaranteed properties")
    sub.add_parser("methodology", help="audit the validation itself and report the corrected comparison")
    rebuild_parser = sub.add_parser("rebuild-data", help="regenerate the derived CSV from raw WRP")
    rebuild_parser.add_argument("--start-year", type=int, default=data.DEFAULT_START,
                                help=f"first year of the balanced panel (default {data.DEFAULT_START})")
    args = parser.parse_args(argv)
    return {"validate": show_validation, "selftest": selftest, "methodology": methodology,
            "rebuild-data": rebuild}.get(args.command, report)(args)


if __name__ == "__main__":
    raise SystemExit(main())
