"""Step 3: leakage-aware religion features and rolling-origin evaluation plans.

Run from the directory containing data/raw/ and data/processed/:
    .\\.venv\\Scripts\\python.exe step3_engineer_features.py

Inputs created in Step 2:
  data/processed/wrp_training_only_8groups.csv
  data/processed/pew_anchor_only_8groups.csv
  data/raw/ne_50m_admin_0_countries.zip

Outputs are placed in data/features/. No model is trained here.

Interpretation:
  Each training example at origin year t predicts shares at t+5 using only
  WRP religion observations from t, t-5, t-10 and UN demographic values at t.
  Spatial features use observed shares at t of other countries, never t+5.
  Adjacency is a MODERN-country approximation, not an historical borders dataset.
  WPP 2024 historical revisions are retrospective data; not vintage forecasts.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "features"
RELIGIONS = [
    "Christianity", "Islam", "Hinduism", "Buddhism", "Judaism",
    "Folk_Traditional", "Other", "Unaffiliated",
]
SHARES = [f"share_{religion}" for religion in RELIGIONS]
DEMOGRAPHICS = [
    "tfr", "median_age", "wpp_population", "net_migrations",
    "crude_net_migration_rate",
]
VALIDATION_ORIGINS = [1975, 1980, 1985, 1990, 1995, 2000, 2005]
HORIZONS = [5, 10, 20, 30]


def load_panel(filename: str, expected_source: str) -> pd.DataFrame:
    path = PROCESSED / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Complete Step 2 first.")
    df = pd.read_csv(path, low_memory=False)
    required = {"country_id", "year", "source", *SHARES}
    absent = required - set(df.columns)
    if absent:
        raise ValueError(f"{filename} is missing fields: {sorted(absent)}")
    if not df["source"].eq(expected_source).all():
        raise ValueError(f"{filename}: expected only {expected_source} records")
    if df[["country_id", "year"]].isna().any().any():
        raise ValueError(f"{filename}: missing country/year")
    if df.duplicated(["country_id", "year"]).any():
        raise ValueError(f"{filename}: duplicate country/year")
    df["year"] = pd.to_numeric(df["year"], errors="raise").astype(int)
    df[SHARES] = df[SHARES].apply(pd.to_numeric, errors="raise")
    values = df[SHARES].to_numpy(dtype=float)
    if not np.isfinite(values).all() or not np.allclose(values.sum(axis=1), 1, atol=1e-8):
        raise ValueError(f"{filename}: invalid religion-share totals")
    if (values < -1e-9).any() or (values > 1 + 1e-9).any():
        raise ValueError(f"{filename}: religion shares outside [0,1]")
    for col in DEMOGRAPHICS:
        if col not in df:
            raise ValueError(f"{filename}: missing {col}; rerun step2_finalize_panels.py")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.sort_values(["country_id", "year"]).reset_index(drop=True)


def geographic_reference() -> tuple[dict[str, str], dict[str, list[str]]]:
    """Map country -> continent, and direct land-border neighbor ISO3 codes.

    Modern geography is used only to define proxy features. Historic polity codes
    have no invented polygons, and islands legitimately have no land neighbors.
    """
    archive = RAW / "ne_50m_admin_0_countries.zip"
    if not archive.exists():
        raise FileNotFoundError(f"Missing Natural Earth shapefile: {archive}")
    geo = gpd.read_file("zip://" + str(archive.resolve()))
    geo["iso3"] = geo["ISO_A3"].astype(str).str.upper()
    fallback = ~geo["iso3"].str.fullmatch(r"[A-Z]{3}")
    geo.loc[fallback, "iso3"] = geo.loc[fallback, "ADM0_A3"].astype(str).str.upper()
    geo = geo.loc[geo.iso3.str.fullmatch(r"[A-Z]{3}")].copy()
    continents = (geo.drop_duplicates("iso3").set_index("iso3")["CONTINENT"]
                  .astype(str).to_dict())

    # Merge multipolygons for repeated keys; avoid assuming row order or first feature.
    borders = geo[["iso3", "geometry"]].dissolve(by="iso3").reset_index()
    country_ids = borders["iso3"].to_list()
    land_neighbors = {k: [] for k in country_ids}
    index = borders.sindex
    for i, geom in enumerate(borders.geometry):
        if geom is None or geom.is_empty:
            continue
        # Bounding-box matches are filtered by exact topology.
        candidates = index.query(geom, predicate="touches")
        land_neighbors[country_ids[i]] = sorted({
            country_ids[int(j)] for j in candidates if int(j) != i
        })
    return continents, land_neighbors


def peer_features(
    wrp: pd.DataFrame,
    continents: dict[str, str],
    neighbors: dict[str, list[str]],
) -> pd.DataFrame:
    """Origin-year peer means only; excludes the focal country itself."""
    by_year = {
        int(year): frame.set_index("country_id", verify_integrity=True)[SHARES]
        for year, frame in wrp.groupby("year", sort=False)
    }
    results = []
    for row in wrp[["country_id", "year"]].itertuples(index=False):
        cid, year = str(row.country_id), int(row.year)
        current = by_year[year]
        region = continents.get(cid)
        bordering = [other for other in neighbors.get(cid, []) if other in current.index]
        peer = current.loc[bordering].mean(axis=0) if bordering else pd.Series(np.nan, index=SHARES)
        continent_ids = [other for other in current.index
                         if other != cid and region is not None and continents.get(str(other)) == region]
        continental = (current.loc[continent_ids].mean(axis=0) if continent_ids
                       else pd.Series(np.nan, index=SHARES))
        result = {
            "country_id": cid,
            "origin_year": year,
            "continent": region,
            "modern_geography_available": cid in continents,
            "n_land_neighbors_observed": len(bordering),
            "n_continent_peers_observed": len(continent_ids),
        }
        for sh in SHARES:
            result[f"border_mean_{sh}"] = float(peer[sh])
            result[f"continent_mean_{sh}"] = float(continental[sh])
        results.append(result)
    return pd.DataFrame(results)


def create_origin_features(wrp: pd.DataFrame, peers: pd.DataFrame) -> pd.DataFrame:
    """Origin t includes current shares and true observation lags at t-5 and t-10."""
    src = wrp.copy().sort_values(["country_id", "year"]).reset_index(drop=True)
    src = src.rename(columns={"year": "origin_year"})
    grouped = src.groupby("country_id", sort=False)
    prior_year = grouped["origin_year"].shift(1)
    twice_prior_year = grouped["origin_year"].shift(2)
    history_complete = (src["origin_year"].sub(prior_year).eq(5)
                        & src["origin_year"].sub(twice_prior_year).eq(10))
    for share in SHARES:
        src[f"lag5_{share}"] = grouped[share].shift(1)
        src[f"lag10_{share}"] = grouped[share].shift(2)
        src[f"change5_{share}"] = src[share] - src[f"lag5_{share}"]
        src[f"change10_{share}"] = src[share] - src[f"lag10_{share}"]
    # Do not turn across-gap changes into actual five/ten-year changes.
    src = src.loc[history_complete].copy()
    src = src.merge(peers, on=["country_id", "origin_year"], how="left", validate="one_to_one")
    for col in DEMOGRAPHICS:
        src[f"missing_{col}"] = src[col].isna().astype(int)
    src["log_population"] = np.log1p(src["wpp_population"].clip(lower=0))
    src["border_mean_missing"] = src["n_land_neighbors_observed"].eq(0).astype(int)
    src["continent_mean_missing"] = src["n_continent_peers_observed"].eq(0).astype(int)
    src["dominant_at_origin"] = src[SHARES].idxmax(axis=1).str.removeprefix("share_")
    src["row_id"] = src["country_id"].astype(str) + "__" + src["origin_year"].astype(str)
    if src.duplicated("row_id").any():
        raise ValueError("Repeated feature row id")
    return src.sort_values(["origin_year", "country_id"]).reset_index(drop=True)


def add_targets(origin: pd.DataFrame, wrp: pd.DataFrame) -> pd.DataFrame:
    target = wrp[["country_id", "year", *SHARES]].rename(
        columns={"year": "target_year", **{sh: f"target_{sh}" for sh in SHARES}})
    frame = origin.copy()
    frame["target_year"] = frame["origin_year"] + 5
    frame = frame.merge(target, on=["country_id", "target_year"], how="left", validate="one_to_one")
    available = frame[[f"target_{s}" for s in SHARES]].notna().all(axis=1)
    samples = frame.loc[available].copy()
    samples["dominant_at_target"] = samples[[f"target_{s}" for s in SHARES]].idxmax(axis=1).str.replace(
        "target_share_", "", regex=False)
    if not (samples["target_year"] - samples["origin_year"]).eq(5).all():
        raise AssertionError("The label is not 5 years after the origin")
    if not np.allclose(samples[[f"target_{s}" for s in SHARES]].sum(axis=1), 1, atol=1e-8):
        raise AssertionError("Target shares do not sum to 1")
    # Do not put target shares in feature_columns.json. They exist only as labels.
    return samples.sort_values(["target_year", "country_id"]).reset_index(drop=True)


def create_one_step_splits(samples: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Train labels <= T; evaluate ONLY T->T+5 for each T.

    Later horizons require recursive prediction; teacher forcing with real future
    religion shares is not legitimate multi-horizon validation.
    """
    allocations = []
    report = []
    for cutoff in VALIDATION_ORIGINS:
        train = samples.loc[samples["target_year"] <= cutoff]
        validation = samples.loc[
            samples["origin_year"].eq(cutoff) & samples["target_year"].eq(cutoff + 5)]
        if train.empty or validation.empty:
            raise ValueError(f"No training/validation data for origin {cutoff}")
        if train["target_year"].max() > cutoff or not validation["origin_year"].eq(cutoff).all():
            raise AssertionError("Forward-chain time leakage")
        for subset, label in ((train, "train"), (validation, "validation")):
            keep = subset[["row_id", "country_id", "origin_year", "target_year"]].copy()
            keep["fold_origin"] = cutoff
            keep["split"] = label
            allocations.append(keep)
        report.append({
            "forecast_origin": cutoff,
            "training_examples": len(train),
            "validation_examples": len(validation),
            "max_training_label_year": int(train["target_year"].max()),
            "validation_label_year": cutoff + 5,
        })
    return pd.concat(allocations, ignore_index=True), report


def create_multihorizon_plan(origins: pd.DataFrame, wrp: pd.DataFrame) -> pd.DataFrame:
    # Ground truth years are used solely to count scoreable countries; their
    # religious values are NOT copied into the feature files for this plan.
    entities_by_year = {
        int(year): set(frame["country_id"])
        for year, frame in wrp.groupby("year", sort=False)
    }
    records = []
    max_year = int(wrp["year"].max())
    for year in VALIDATION_ORIGINS:
        origin_countries = set(origins.loc[origins.origin_year.eq(year), "country_id"])
        for horizon in HORIZONS:
            end = year + horizon
            if end > max_year:
                continue
            records.append({
                "forecast_origin": year,
                "horizon_years": horizon,
                "target_year": end,
                "countries_with_origin_features_and_ground_truth": len(
                    origin_countries & entities_by_year.get(end, set())),
                "validation_method": "recursive_no_future_observed_religion_inputs",
            })
    return pd.DataFrame(records)


def create_pew_anchor(pew: pd.DataFrame) -> pd.DataFrame:
    # This is a modern 10-year change, NOT a measured 2015 observation or a
    # valid five-year model transition.
    a = pew.loc[pew.year.eq(2010), ["country_id", *SHARES]].rename(
        columns={s: f"pew_2010_{s}" for s in SHARES})
    b = pew.loc[pew.year.eq(2020)].copy()
    if b.empty:
        raise ValueError("Pew has no 2020 observations")
    b = b.merge(a, on="country_id", how="left", validate="one_to_one")
    for s in SHARES:
        b[f"pew_delta_2010_2020_{s}"] = b[s] - b[f"pew_2010_{s}"]
    b["has_pew_2010_baseline"] = b[f"pew_2010_{SHARES[0]}"].notna()
    b["five_year_lag_observed"] = False
    b["pew_2010_2020_note"] = "10-year Pew change; 2015 unavailable; do not train as 5-year transition"
    return b


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wrp = load_panel("wrp_training_only_8groups.csv", "WRP")
    pew = load_panel("pew_anchor_only_8groups.csv", "Pew")
    if wrp["year"].max() != 2010 or set(pew["year"].unique()) != {2010, 2020}:
        raise ValueError("Unexpected source years; inspect Step 2 inputs")
    continents, neighbors = geographic_reference()
    spatial = peer_features(wrp, continents, neighbors)
    origins = create_origin_features(wrp, spatial)
    samples = add_targets(origins, wrp)
    splits, split_report = create_one_step_splits(samples)
    horizon_plan = create_multihorizon_plan(origins, wrp)
    pew_anchor = create_pew_anchor(pew)

    # Separate predictors from targets, identifiers, quality labels, and metadata.
    predictors = (SHARES
        + [f"lag{lag}_{s}" for lag in [5, 10] for s in SHARES]
        + [f"change{lag}_{s}" for lag in [5, 10] for s in SHARES]
        + DEMOGRAPHICS + ["log_population"]
        + [f"missing_{col}" for col in DEMOGRAPHICS]
        + [f"border_mean_{s}" for s in SHARES]
        + [f"continent_mean_{s}" for s in SHARES]
        + ["border_mean_missing", "continent_mean_missing",
           "n_land_neighbors_observed", "n_continent_peers_observed"])
    unknown = set(predictors) - set(samples.columns)
    if unknown:
        raise ValueError(f"Unexpected absent predictors: {sorted(unknown)}")
    labels = [f"target_{s}" for s in SHARES]
    if any(name.startswith("target_") for name in predictors):
        raise AssertionError("Target appears in predictor list")
    if not np.isfinite(samples[SHARES].to_numpy()).all():
        raise AssertionError("Nonfinite current share values")

    origins.to_csv(OUT / "wrp_origin_features.csv", index=False)
    samples.to_csv(OUT / "wrp_training_transitions.csv", index=False)
    splits.to_csv(OUT / "rolling_origin_one_step_splits.csv", index=False)
    horizon_plan.to_csv(OUT / "multihorizon_evaluation_plan.csv", index=False)
    pew_anchor.to_csv(OUT / "pew_2020_anchor_context.csv", index=False)

    report = {
        "wrp_rows_loaded": len(wrp),
        "wrp_origin_rows_with_consecutive_5_and_10_year_history": len(origins),
        "wrp_labeled_5year_transitions_with_full_lag_history": len(samples),
        "origin_year_range": [int(origins.origin_year.min()), int(origins.origin_year.max())],
        "label_year_range": [int(samples.target_year.min()), int(samples.target_year.max())],
        "country_entities_with_training_examples": int(samples.country_id.nunique()),
        "percent_origin_rows_with_observed_land_neighbors": round(
            100 * origins.n_land_neighbors_observed.gt(0).mean(), 1),
        "percent_origin_rows_with_continent_peers": round(
            100 * origins.n_continent_peers_observed.gt(0).mean(), 1),
        "percent_training_examples_missing_tfr": round(100 * samples.tfr.isna().mean(), 1),
        "rolling_origin_one_step_folds": split_report,
        "multi_horizon_plans": len(horizon_plan),
        "pew_2020_anchors": len(pew_anchor),
        "pew_2020_anchors_with_2010_pew_history": int(pew_anchor.has_pew_2010_baseline.sum()),
        "feature_columns": predictors,
        "target_columns": labels,
        "cautions": [
            "Training targets and lag features are WRP-only. Pew is a separate anchor.",
            "The 2020 Pew anchors do not include observed 2015 shares; 5-year lag setup needs an explicit future initialization rule.",
            "Land neighbors are derived from present-day Natural Earth borders and are historical geographic proxies.",
            "Unmapped historical entities do not receive fabricated land neighbors.",
            "Regional peer averages use other countries observed in the same origin year; no future religion values.",
            "Missing demographic values remain missing; Step 4 must fit any imputer using training folds only.",
            "UN WPP 2024 retrospective estimates may contain information learned after each historic forecast origin.",
            "One-step folds do not validate 10/20/30-year forecasts; Step 4 must run recursive horizon backtests.",
        ],
    }
    (OUT / "step3_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "feature_columns.json").write_text(
        json.dumps({"predictors": predictors, "targets": labels}, indent=2), encoding="utf-8")
    print("SUCCESS: Step 3 features and rolling-origin plans created. No model trained.")
    for name in ["wrp_origin_features.csv", "wrp_training_transitions.csv",
                 "rolling_origin_one_step_splits.csv", "multihorizon_evaluation_plan.csv",
                 "pew_2020_anchor_context.csv", "feature_columns.json", "step3_report.json"]:
        print(" -", OUT / name)
    print("\nSUMMARY:")
    print(json.dumps({k: report[k] for k in [
        "wrp_rows_loaded", "wrp_origin_rows_with_consecutive_5_and_10_year_history",
        "wrp_labeled_5year_transitions_with_full_lag_history",
        "percent_origin_rows_with_observed_land_neighbors",
        "percent_training_examples_missing_tfr", "pew_2020_anchors",
        "rolling_origin_one_step_folds", "multi_horizon_plans"]}, indent=2))


if __name__ == "__main__":
    main()
