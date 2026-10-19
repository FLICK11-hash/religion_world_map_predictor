"""Step 2 finalization: retain source-consistent WRP training and Pew anchor panels.

Run from the folder that contains data/processed/:
    python step2_finalize_panels.py

This script does not modify downloaded datasets or Step 2's existing outputs.
It DOES NOT resolve cross-source religious-definition differences.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"
SHARES = [
    "share_Christianity", "share_Islam", "share_Hinduism", "share_Buddhism",
    "share_Judaism", "share_Folk_Traditional", "share_Other", "share_Unaffiliated",
]
WPP_FEATURES = [
    "country_id", "year", "tfr", "median_age", "wpp_population",
    "net_migrations", "crude_net_migration_rate",
]


def load_valid_source(filename: str, label: str) -> pd.DataFrame:
    path = PROCESSED / filename
    frame = pd.read_csv(path, low_memory=False)
    required = {"country_id", "year", "quality_pass", "source"} | set(SHARES)
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{filename} missing columns: {sorted(missing)}")
    ok = frame["quality_pass"].astype(str).str.lower().eq("true")
    frame = frame.loc[ok & frame["country_id"].notna()].copy()
    if frame.empty or frame["source"].ne(label).any():
        raise ValueError(f"{filename}: no valid records, or unexpected source")
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    frame[SHARES] = frame[SHARES].apply(pd.to_numeric, errors="coerce")
    if frame[SHARES].isna().any().any():
        raise ValueError(f"{filename}: missing religion shares in accepted rows")
    if not np.allclose(frame[SHARES].sum(axis=1).to_numpy(), 1.0, atol=1e-8):
        raise ValueError(f"{filename}: invalid religion share totals")
    if frame[SHARES].lt(0).any().any() or frame[SHARES].gt(1).any().any():
        raise ValueError(f"{filename}: negative or >1 shares")
    if frame.duplicated(["country_id", "year"]).any():
        raise ValueError(f"{filename}: duplicate country/year")
    frame["dominant_religion"] = frame[SHARES].idxmax(axis=1).str.replace("share_", "", regex=False)
    return frame.sort_values(["country_id", "year"]).reset_index(drop=True)


def main() -> None:
    wrp = load_valid_source("wrp_harmonized_all_rows.csv", "WRP")
    pew = load_valid_source("pew_harmonized.csv", "Pew")
    if wrp["year"].max() != 2010 or not set(pew["year"]).issubset({2010, 2020}):
        raise ValueError("Unexpected years in WRP or Pew; inspect the datasets")

    # Historical training must not use Pew's 2010 values as the next WRP period.
    wrp["has_previous_5yr"] = wrp.groupby("country_id")["year"].diff().eq(5)
    wrp["has_previous_10yr"] = (
        wrp.groupby("country_id")["year"].diff(2).eq(10)
        & wrp["has_previous_5yr"]
    )
    # The 2020 Pew observation is 10 years after the 2010 Pew observation:
    # they are NOT a 5-year time series.
    pew["has_previous_5yr"] = False

    # Append demographic information, preserving raw religion estimates and
    # disclosing that these variables are from the WPP 2024 revision.
    wpp = pd.read_csv(PROCESSED / "wpp_country_year.csv", low_memory=False)
    if not set(WPP_FEATURES).issubset(wpp.columns):
        raise ValueError("WPP feature columns missing")
    wpp = wpp[WPP_FEATURES].copy()
    if wpp.duplicated(["country_id", "year"]).any():
        raise ValueError("WPP contains duplicate country/year rows")
    wrp = wrp.merge(wpp, on=["country_id", "year"], how="left", validate="many_to_one")
    pew = pew.merge(wpp, on=["country_id", "year"], how="left", validate="many_to_one")
    wrp["demographics_source"] = "UN_WPP_2024_revision"
    pew["demographics_source"] = "UN_WPP_2024_revision"

    wrp_path = PROCESSED / "wrp_training_only_8groups.csv"
    pew_path = PROCESSED / "pew_anchor_only_8groups.csv"
    wrp.to_csv(wrp_path, index=False)
    pew.to_csv(pew_path, index=False)

    # Flag substantial 2010 differences; do not blend or rewrite the estimates.
    audit = pd.read_csv(PROCESSED / "audit_2010_wrp_vs_pew.csv")
    audit["mae_7_categories"] = pd.to_numeric(audit["mae_7_categories"], errors="raise")
    categories = ["Christianity", "Islam", "Hinduism", "Buddhism", "Judaism", "Unaffiliated"]
    cols = [f"share_{name}" for name in categories] + ["Other_7"]
    for suffix in ["wrp", "pew"]:
        arr = audit[[f"{col}_{suffix}" for col in cols]].to_numpy(dtype=float)
        audit[f"dominant_{suffix}_7groups"] = np.asarray(categories + ["Other_7"])[arr.argmax(axis=1)]
    audit["dominant_disagrees"] = audit["dominant_wrp_7groups"].ne(audit["dominant_pew_7groups"])
    audit["large_discrepancy"] = audit["mae_7_categories"].ge(0.05)
    audit.loc[audit["large_discrepancy"] | audit["dominant_disagrees"]].sort_values(
        "mae_7_categories", ascending=False
    ).to_csv(PROCESSED / "audit_high_risk_source_differences.csv", index=False)

    report = {
        "wrp_clean_rows": int(len(wrp)),
        "wrp_5year_transition_targets": int(wrp["has_previous_5yr"].sum()),
        "wrp_rows_with_two_5year_lags": int(wrp["has_previous_10yr"].sum()),
        "wrp_countries_or_historical_entities": int(wrp["country_id"].nunique()),
        "wrp_un_demographics_matched_pct": round(float(wrp["tfr"].notna().mean() * 100), 1),
        "pew_rows": int(len(pew)),
        "pew_2010_rows": int(pew["year"].eq(2010).sum()),
        "pew_2020_rows": int(pew["year"].eq(2020).sum()),
        "pew_2010_2020_5year_transitions": 0,
        "shared_2010_countries": int(len(audit)),
        "large_mae_5pct_points_per_group_countries": int(audit["large_discrepancy"].sum()),
        "different_2010_dominant_groups": int(audit["dominant_disagrees"].sum()),
        "notes": [
            "Train WRP historical transitions only within WRP; never cross the WRP-to-Pew source switch.",
            "Pew is a modern anchor; its Folk/Other split includes WRP-derived proxies.",
            "WPP demographic history is from the 2024 revision; forecast-origin evaluation needs its own leakage protocol.",
            "Unmapped historical borders remain deliberate; do not assign predecessor countries to successors.",
            "No model has been trained and no source differences have been silently corrected.",
        ],
    }
    (PROCESSED / "step2_finalization_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("SUCCESS: Source-consistent Step 2 datasets written.")
    print(json.dumps(report, indent=2))
    print("Created:")
    print(" -", wrp_path)
    print(" -", pew_path)
    print(" -", PROCESSED / "audit_high_risk_source_differences.csv")
    print(" -", PROCESSED / "step2_finalization_report.json")


if __name__ == "__main__":
    main()
