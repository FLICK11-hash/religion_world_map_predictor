#!/usr/bin/env python3
"""Compare the committed projection with Pew's own 2026 projections (Hackett et al. 2026).

    python scripts/benchmark_pew2026.py

Pew's country projections for 2030-2070 are written to data/processed/pew_projections_2030_2070.csv
by scripts/prepare_pew_panel.py from Pew's Global Religious Futures dataset (free Pew account, not
redistributed). They never enter the model: this compares two projections built separately from the
same 2020 estimates, which is a check of agreement, not of accuracy. When data/processed/
pew_harmonized.csv is present, the script also reports how much Pew's own country compositions
changed between 2010 and 2020 (the error of a no-change forecast over that decade).

Writes, from the committed results and Pew's file:
  results/validation/benchmark_pew2026_world.csv          world shares by decade, 2030-2070
  results/validation/benchmark_pew2026_countries_2050.csv country shares in 2050, with this
                                                          projection's 90% predictive interval
  results/validation/benchmark_pew2026_summary.json       the headline numbers
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
SCENARIO = "stabilising"

# Pew's seven groups; folk religions are inside Pew's "other religions".
GROUPS = ["Christianity", "Islam", "Hinduism", "Buddhism", "Judaism", "Unaffiliated", "Other7"]
WITH_INTERVAL = ["Christianity", "Islam", "Hinduism", "Buddhism", "Judaism", "Unaffiliated"]


def seven(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Eight model groups to Pew's seven: Other7 = Other + Folk_Traditional."""
    out = pd.DataFrame({g: df[f"{prefix}{g}"] for g in WITH_INTERVAL}, index=df.index)
    out["Other7"] = df[f"{prefix}Other"] + df.get(f"{prefix}Folk_Traditional", 0.0)
    return out


def pew_shares(pew: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({g: pew[f"share_{g}"] for g in WITH_INTERVAL}, index=pew.index)
    out["Other7"] = pew["share_Other"] + pew.get("share_Folk_Traditional", 0.0)
    return out


def world_table(pew: pd.DataFrame) -> pd.DataFrame:
    ours = pd.read_csv(RESULTS / "projection" / "global_share_by_scenario.csv")
    ours = ours[ours.scenario.eq(SCENARIO)]
    rows = []
    for year, block in pew.groupby("year"):
        counts = pew_shares(block).mul(block["population"], axis=0).sum() / block["population"].sum()
        mine = ours[ours.year.eq(year)].set_index("religion")
        if mine.empty:
            continue
        for g in GROUPS:
            if g == "Other7":
                mean = mine.loc[["Other", "Folk_Traditional"], "mean"].sum()
                lo = hi = np.nan
            else:
                mean, lo, hi = mine.loc[g, ["mean", "pi05", "pi95"]]
            rows.append(dict(year=int(year), religion=g, pew_share=counts[g], model_mean=mean,
                             model_pi05=lo, model_pi95=hi,
                             pew_inside_interval=bool(lo <= counts[g] <= hi) if pd.notna(lo) else np.nan))
    return pd.DataFrame(rows)


def country_table(pew: pd.DataFrame, year: int = 2050) -> tuple[pd.DataFrame, dict]:
    bands = pd.read_csv(RESULTS / "projection" / "country_target_years_reference_with_bands.csv")
    bands = bands[bands.scenario.eq(SCENARIO) & bands.year.eq(year)].set_index("country_id")
    p = pew[pew.year.eq(year)].dropna(subset=["country_id"]).set_index("country_id")
    common = p.index.intersection(bands.index)
    mine, theirs = seven(bands.loc[common], "mean_"), pew_shares(p.loc[common])
    tv = 0.5 * (mine - theirs).abs().sum(axis=1)
    weight = p.loc[common, "population"] / p.loc[common, "population"].sum()
    table = pd.DataFrame({"tv_distance": tv, "largest_model": mine.idxmax(axis=1),
                          "largest_pew": theirs.idxmax(axis=1), "pew_population": p.loc[common, "population"]})
    inside = {}
    for g in GROUPS:
        table[f"pew_{g}"] = theirs[g]
        table[f"model_{g}"] = mine[g]
        if g in WITH_INTERVAL:
            lo, hi = bands.loc[common, f"pi05_{g}"], bands.loc[common, f"pi95_{g}"]
            table[f"model_pi05_{g}"], table[f"model_pi95_{g}"] = lo, hi
            ok = (theirs[g] >= lo - 1e-9) & (theirs[g] <= hi + 1e-9)
            table[f"pew_inside_{g}"] = ok
            inside[g] = float(ok.mean())
    differ = table.index[table.largest_model.ne(table.largest_pew)].tolist()
    summary = {
        "year": year,
        "countries": int(len(common)),
        "population_weighted_tv_pp": round(100 * float((tv * weight).sum()), 2),
        "median_country_tv_pp": round(100 * float(tv.median()), 2),
        "largest_religion_agrees": int(len(common) - len(differ)),
        "largest_religion_differs": differ,
        "pew_share_inside_model_90pct_interval": {g: round(v, 3) for g, v in inside.items()},
        "pew_share_inside_overall": round(float(np.mean([table[f"pew_inside_{g}"].mean() for g in WITH_INTERVAL])), 3),
        "largest_tv_countries_pp": {k: round(100 * v, 1) for k, v in tv.sort_values(ascending=False).head(8).items()},
    }
    return table.sort_values("tv_distance", ascending=False).reset_index(), summary


def pew_decade_change(panel_path: Path) -> dict | None:
    if not panel_path.is_file():
        return None
    panel = pd.read_csv(panel_path)
    panel = panel[panel.get("quality_pass", True).astype(bool) & panel.country_id.notna()]
    a = panel[panel.year.eq(2010)].set_index("country_id")
    b = panel[panel.year.eq(2020)].set_index("country_id")
    common = a.index.intersection(b.index)
    tv = 0.5 * (pew_shares(b.loc[common]) - pew_shares(a.loc[common])).abs().sum(axis=1)
    weight = b.loc[common, "population_source"] / b.loc[common, "population_source"].sum()
    return {"countries": int(len(common)), "population_weighted_tv_pp": round(100 * float((tv * weight).sum()), 2),
            "note": "seven groups; the error of a no-change forecast of Pew's 2020 estimates from Pew's 2010 estimates"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pew", type=Path, default=PROCESSED / "pew_projections_2030_2070.csv")
    ap.add_argument("--pew-panel", type=Path, default=PROCESSED / "pew_harmonized.csv")
    ap.add_argument("--out", type=Path, default=RESULTS / "validation")
    args = ap.parse_args()
    if not args.pew.is_file():
        print(f"Missing {args.pew}. Put Pew's Global Religious Futures dataset in data/raw/ and run "
              "python scripts/prepare_pew_panel.py first.")
        return 1
    pew = pd.read_csv(args.pew)
    world = world_table(pew)
    countries, summary = country_table(pew)
    gap = (world.model_mean - world.pew_share).abs().groupby(world.religion).max()
    summary["world_largest_gap_pp"] = {g: round(100 * float(gap[g]), 1) for g in GROUPS}
    change = pew_decade_change(args.pew_panel)
    if change:
        summary["pew_2010_2020_no_change_error"] = change
    args.out.mkdir(parents=True, exist_ok=True)
    world.to_csv(args.out / "benchmark_pew2026_world.csv", index=False)
    countries.to_csv(args.out / "benchmark_pew2026_countries_2050.csv", index=False)
    (args.out / "benchmark_pew2026_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
