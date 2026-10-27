"""Step 2: create an auditable country-year panel from WRP, Pew, UN and Natural Earth.

Run from the folder containing data/raw:
    python step2_clean_merge.py

Requires: pandas, geopandas, requests, openpyxl, pycountry.
Downloads an auxiliary (time-aware, imperfect) COW->ISO crosswalk from GitHub.
All raw inputs remain unchanged. Outputs are written to data/processed/.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import re

import geopandas as gpd
import numpy as np
import pandas as pd
import pycountry
import requests

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
CROSSWALK_URL = "https://raw.githubusercontent.com/leops95/cow2iso/master/cow2iso.csv"

RELIGIONS = ["Christianity", "Islam", "Hinduism", "Buddhism", "Judaism",
             "Folk_Traditional", "Other", "Unaffiliated"]
SHARES = [f"share_{r}" for r in RELIGIONS]

# WRP's aggregate totals are used ONCE. Do not also sum Christian/Muslim subgroups.
WRP_FIELDS = {
    "Christianity": ["chrstgenpct"],
    "Islam": ["islmgenpct"],
    "Hinduism": ["hindgenpct"],
    "Buddhism": ["budgenpct"],
    "Judaism": ["judgenpct"],
    # Operational definition; debated practices and dual belonging must be audited.
    "Folk_Traditional": ["shntgenpct", "taogenpct", "confgenpct", "syncgenpct", "anmgenpct"],
    "Other": ["zorogenpct", "sikhgenpct", "bahgenpct", "jaingenpct", "othrgenpct"],
    "Unaffiliated": ["nonreligpct"],
}
PEW_COUNTS = {
    "Christianity": "Christians", "Islam": "Muslims", "Hinduism": "Hindus",
    "Buddhism": "Buddhists", "Judaism": "Jews",
    "Unaffiliated": "Religiously_unaffiliated", "Other": "Other_religions",
}

# Deliberate NON-ISO identifiers: historic polity != present-day successor.
# Never divide or relabel a predecessor's shares as one successor's shares.
def historical_entity(cow_id: int, year: int) -> tuple[str, str] | None:
    rules = [
        (365, year <= 1991, "SUN", "Soviet Union"),
        (315, year <= 1992, "CSK", "Czechoslovakia"),
        (345, year <= 1991, "YUG", "Yugoslavia"),
        (345, 1992 <= year <= 2006, "SCG", "Federal Republic of Yugoslavia / Serbia and Montenegro"),
        (260, year <= 1990, "DEU_W", "West Germany"),
        (265, year <= 1990, "DEU_E", "East Germany"),
        (625, year <= 2010, "SDN_PRE2011", "Sudan before South Sudan independence"),
        (770, year <= 1971, "PAK_PRE1972", "Pakistan including East Pakistan"),
        (530, year <= 1992, "ETH_PRE1993", "Ethiopia before Eritrea independence"),
        (816, year <= 1975, "VNM_N", "North Vietnam"),
        (817, year <= 1975, "VNM_S", "South Vietnam"),
        (678, year <= 1990, "YEM_N", "North Yemen"),
        (680, year <= 1990, "YEM_S", "South Yemen"),
        (730, year <= 1948, "KOR_PRE1948", "Pre-division Korea"),
    ]
    for state, applies, key, label in rules:
        if cow_id == state and applies:
            return key, label
    return None


def must_exist() -> None:
    names = ["WRP_national.csv", "pew_2010_2020.xlsx",
             "WPP2024_Demographic_Indicators_Medium.csv.gz", "ne_50m_admin_0_countries.zip"]
    absent = [n for n in names if not (RAW / n).is_file()]
    if absent:
        raise FileNotFoundError(f"Missing input files in {RAW}: {absent}. Run Step 1 first.")
    OUT.mkdir(parents=True, exist_ok=True)


def clean_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(",", "", regex=False), errors="coerce")


def country_from_pew(row: pd.Series) -> tuple[str | None, str]:
    """Pew 'Countrycode' is UN M49/ISO numeric, NOT a COW code."""
    name = str(row["Country"]).strip()
    overrides = {
        "Kosovo": "XKX",  # user-assigned code, not official ISO 3166-1
        "Channel Islands": "CHI_ISLANDS",  # aggregate (Jersey + Guernsey)
    }
    if name in overrides:
        return overrides[name], "manual_special"
    code = pd.to_numeric(row["Countrycode"], errors="coerce")
    if pd.notna(code):
        match = pycountry.countries.get(numeric=f"{int(code):03d}")
        if match:
            return match.alpha_3, "m49_numeric"
    return None, "unmatched"


def get_cow_crosswalk() -> pd.DataFrame:
    p = RAW / "cow2iso.csv"
    if not p.exists():
        print("[GET] Auxiliary COW→ISO crosswalk (not a substitute for country-history auditing)")
        r = requests.get(CROSSWALK_URL, timeout=45)
        r.raise_for_status()
        if not r.text.startswith("cow_id,cow3,iso_id"):
            raise ValueError("Crosswalk URL did not return the expected CSV")
        p.write_bytes(r.content)
    df = pd.read_csv(p, dtype={"iso3": "string", "cow3": "string"}, low_memory=False)
    required = {"cow_id", "iso3", "valid_from", "valid_until"}
    if not required.issubset(df.columns):
        raise ValueError(f"Unexpected COW crosswalk columns: {df.columns.tolist()}")
    df["cow_id"] = pd.to_numeric(df["cow_id"], errors="coerce")
    df["valid_from"] = pd.to_numeric(df["valid_from"], errors="coerce")
    df["valid_until"] = pd.to_numeric(df["valid_until"], errors="coerce")
    return df


def build_cow_mapper(crosswalk: pd.DataFrame):
    groups = {int(k): group.copy() for k, group in crosswalk.dropna(subset=["cow_id"]).groupby("cow_id")}
    code_overrides = {58: "ATG", 713: "TWN", 221: "MCO", 223: "LIE", 347: "XKX", 816: "VNM"}  # known crosswalk gaps/errors

    def lookup(code: int, year: int) -> tuple[str | None, str, str]:
        special = historical_entity(code, year)
        if special:
            return special[0], "historic_entity", special[1]
        if code in code_overrides:
            return code_overrides[code], "manual_override", ""
        if code not in groups:
            return None, "unmatched_code", ""
        options = groups[code]
        choices = options[
            (options["valid_from"].isna() | (options["valid_from"] <= year)) &
            (options["valid_until"].isna() | (options["valid_until"] >= year))
        ]
        status = "cow_crosswalk_valid_year"
        if choices.empty:
            # Before coverage started (commonly before 1962), use earliest available
            # crosswalk ONLY if all nonmissing entries agree on the identity.
            options = options.dropna(subset=["iso3"])
            distinct = options["iso3"].dropna().unique().tolist()
            if len(distinct) != 1:
                return None, "ambiguous_outside_crosswalk_years", ""
            choices = options
            status = "cow_crosswalk_year_extrapolated"
        iso = str(choices.sort_values("valid_from", na_position="first").iloc[-1]["iso3"]).strip()
        if not re.fullmatch(r"[A-Z]{3}", iso) or iso == "NAN":
            return None, "crosswalk_missing_iso3", ""
        # Historical codes must not be silently assigned to present-day states.
        return iso, status, ""

    return lookup


def normalize_valid(df: pd.DataFrame, source: str, quality: pd.Series) -> pd.DataFrame:
    """Normalize only near-one category totals; never rescale invalid multi-affiliation rows."""
    totals = df[SHARES].sum(axis=1, min_count=len(SHARES))
    df["raw_sum"] = totals
    valid = totals.between(0.99, 1.01) & df[SHARES].ge(-1e-8).all(axis=1)
    valid &= quality
    df["quality_pass"] = valid
    df["quality_reason"] = np.where(valid, "ok", "review_or_exclude")
    df.loc[valid, SHARES] = df.loc[valid, SHARES].clip(lower=0).div(totals.loc[valid], axis=0)
    # Mark unusable rows as missing shares in the model-ready source; raw values
    # are preserved in the audit output (original raw inputs are never changed).
    df.loc[~valid, SHARES] = np.nan
    df["source"] = source
    return df


def wrp_data(lookup) -> pd.DataFrame:
    wrp = pd.read_csv(RAW / "WRP_national.csv", low_memory=False)
    required = {"year", "state", "name", "dualrelig", "pop"} | set(sum(WRP_FIELDS.values(), []))
    missing = required - set(wrp.columns)
    if missing:
        raise KeyError(f"WRP missing columns: {sorted(missing)}")
    out = pd.DataFrame({
        "year": pd.to_numeric(wrp["year"], errors="raise").astype(int),
        "cow_id": pd.to_numeric(wrp["state"], errors="raise").astype(int),
        "country_name": wrp["name"].astype(str),
        "population_source": clean_num(wrp["pop"]),
        "dualrelig": pd.to_numeric(wrp["dualrelig"], errors="coerce"),
        "wrp_total_recorded": clean_num(wrp["total"]) if "total" in wrp else np.nan,
        "wrp_reliability": wrp["reliabilevel"].astype(str) if "reliabilevel" in wrp else "",
        "wrp_datatype": wrp["datatype"] if "datatype" in wrp else np.nan,
    })
    for religion, cols in WRP_FIELDS.items():
        vals = pd.concat([clean_num(wrp[c]) for c in cols], axis=1)
        out[f"share_{religion}"] = vals.sum(axis=1, min_count=len(cols))
    ids = [lookup(int(code), int(year)) for code, year in zip(out.cow_id, out.year)]
    out["country_id"] = [x[0] for x in ids]
    out["country_match_method"] = [x[1] for x in ids]
    out["historical_country_note"] = [x[2] for x in ids]
    raw_sum = out[SHARES].sum(axis=1, min_count=8)
    warnings = (out.loc[(out.dualrelig.ne(0)) | (~raw_sum.between(.99, 1.01)),
                        ["year", "cow_id", "country_name", "dualrelig", "country_id"]].copy())
    warnings["sum_of_eight_raw"] = raw_sum.loc[warnings.index]
    warnings.to_csv(OUT / "audit_wrp_religion_exceptions.csv", index=False)
    out = normalize_valid(out, "WRP", out.dualrelig.eq(0) & out.country_id.notna())
    return out


def pew_data() -> pd.DataFrame:
    pew = pd.read_excel(RAW / "pew_2010_2020.xlsx", sheet_name="Unrounded counts")
    expected = {"Country", "Year", "Countrycode", "Level", "Population"} | set(PEW_COUNTS.values())
    if not expected.issubset(pew.columns):
        raise KeyError(f"Unexpected Pew worksheet columns. Missing {expected-set(pew.columns)}")
    pew = pew.loc[clean_num(pew["Level"]).eq(1)].copy()  # excludes WORLD and regions
    out = pd.DataFrame({
        "country_name": pew["Country"].astype(str),
        "year": clean_num(pew["Year"]).astype(int),
        "pew_m49_code": clean_num(pew["Countrycode"]).astype("Int64"),
        "population_source": clean_num(pew["Population"]),
    }, index=pew.index)
    ids = [country_from_pew(row) for _, row in pew.iterrows()]
    out["country_id"] = [x[0] for x in ids]
    out["country_match_method"] = [x[1] for x in ids]
    for religion in RELIGIONS:
        out[f"share_{religion}"] = 0.0
    for religion, original_col in PEW_COUNTS.items():
        out[f"share_{religion}"] = clean_num(pew[original_col]) / out["population_source"]
    # Other includes Folk/Traditional in Pew. Split is deferred below.
    out["folk_split_method"] = "pew_other_not_yet_split"
    out = normalize_valid(out, "Pew", out.country_id.notna() & out.population_source.gt(0))
    return out.reset_index(drop=True)


def pew_folk_split(pew: pd.DataFrame, wrp: pd.DataFrame) -> pd.DataFrame:
    """Disaggregate Pew's 'Other' only by an explicitly labeled WRP proxy.

    Estimate = (Pew other) * (WRP folk / (WRP folk + WRP other)).
    This is NOT a Pew-observed folk share. Never infer folk split by geography.
    """
    clean = wrp.loc[wrp.quality_pass & wrp.country_id.notna(),
                    ["country_id", "year", "share_Folk_Traditional", "share_Other"]].copy()
    clean["denom"] = clean["share_Folk_Traditional"] + clean["share_Other"]
    clean = clean.loc[clean.denom > 1e-8]
    clean["folk_ratio"] = clean["share_Folk_Traditional"] / clean.denom
    # Most recent <=2010 historical WRP estimate within each modern country's data.
    nearest = (clean[clean.year <= 2010].sort_values("year")
               .drop_duplicates("country_id", keep="last")
               .set_index("country_id")[["folk_ratio", "year"]])
    result = pew.copy()
    ratio = result.country_id.map(nearest["folk_ratio"])
    proxy_year = result.country_id.map(nearest["year"])
    other_combined = result["share_Other"].copy()
    mask = ratio.notna() & result.quality_pass
    result.loc[mask, "share_Folk_Traditional"] = other_combined.loc[mask] * ratio.loc[mask]
    result.loc[mask, "share_Other"] = other_combined.loc[mask] * (1 - ratio.loc[mask])
    result["folk_split_method"] = np.where(mask, "WRP_2010_or_earlier_proxy", "not_identified_all_to_Other")
    result["folk_proxy_wrp_year"] = proxy_year
    return result


def load_un() -> pd.DataFrame:
    path = RAW / "WPP2024_Demographic_Indicators_Medium.csv.gz"
    un = pd.read_csv(path, low_memory=False)
    cols = ["ISO3_code", "Time", "Location", "LocID", "Variant", "TFR",
            "MedianAgePop", "TPopulation1July", "NetMigrations", "CNMR"]
    if not set(cols).issubset(un.columns):
        raise KeyError("WPP column list has changed; inspect the original header")
    un = un.loc[un.ISO3_code.notna() & un.Variant.astype(str).str.lower().eq("medium"), cols].copy()
    un = un.rename(columns={"ISO3_code": "country_id", "Time": "year",
                            "TPopulation1July": "wpp_population_thousands",
                            "MedianAgePop": "median_age", "NetMigrations": "net_migrations_thousands",
                            "TFR": "tfr", "CNMR": "crude_net_migration_rate"})
    un["year"] = clean_num(un["year"]).astype(int)
    for c in ["wpp_population_thousands", "median_age", "net_migrations_thousands", "tfr", "crude_net_migration_rate"]:
        un[c] = clean_num(un[c])
    # WPP uses thousands for total population and net migration; convert to persons.
    un["wpp_population"] = un.pop("wpp_population_thousands") * 1000
    un["net_migrations"] = un.pop("net_migrations_thousands") * 1000
    duplicated = un.duplicated(["country_id", "year"], keep=False)
    if duplicated.any():
        un.loc[duplicated].to_csv(OUT / "audit_wpp_duplicate_country_years.csv", index=False)
        raise ValueError("Duplicate ISO3/year after WPP filtering; inspect audit_wpp_duplicate_country_years.csv")
    # This is the 2024 revision. Mark forecasts as projections, not observations.
    un["wpp_is_projection"] = un.year >= 2024
    return un.drop(columns=["LocID", "Location", "Variant"])


def load_map() -> pd.DataFrame:
    geo = gpd.read_file("zip://" + str((RAW / "ne_50m_admin_0_countries.zip").resolve()))
    geo["map_iso3"] = geo["ISO_A3"].astype(str)
    missing = ~geo.map_iso3.str.fullmatch(r"[A-Z]{3}")
    geo.loc[missing, "map_iso3"] = geo.loc[missing, "ADM0_A3"].astype(str)
    return geo[["map_iso3", "NAME", "CONTINENT"]].rename(columns={"NAME": "map_name", "CONTINENT": "continent"})


def check(df: pd.DataFrame, name: str) -> None:
    df = df.loc[df.quality_pass & df.country_id.notna()].copy()
    if df.empty:
        raise ValueError(f"{name}: no valid mapped country-year rows")
    if df.duplicated(["country_id", "year"]).any():
        dupe = df[df.duplicated(["country_id", "year"], keep=False)]
        dupe.to_csv(OUT / f"audit_{name}_duplicates.csv", index=False)
        raise ValueError(f"{name}: repeated country_id/year; review audit file")
    total = df[SHARES].sum(axis=1)
    assert np.allclose(total.to_numpy(), 1, atol=1e-8), f"{name}: share sums invalid"
    assert df[SHARES].ge(-1e-8).all().all() and df[SHARES].le(1 + 1e-8).all().all()
    print(f"[PASS] {name}: {len(df):,} clean country-years, shares sum to 1")


def main() -> None:
    must_exist()
    lookup = build_cow_mapper(get_cow_crosswalk())
    wrp = wrp_data(lookup)
    pew = pew_folk_split(pew_data(), wrp)
    wpp = load_un()
    world = load_map()

    wrp.to_csv(OUT / "wrp_harmonized_all_rows.csv", index=False)
    pew.to_csv(OUT / "pew_harmonized.csv", index=False)
    check(wrp, "wrp")
    check(pew, "pew")

    # 7-bin apples-to-apples comparison at 2010 (Other+Folk combined).
    a = wrp.loc[wrp.quality_pass & wrp.year.eq(2010) & wrp.country_id.notna()].copy()
    b = pew.loc[pew.quality_pass & pew.year.eq(2010) & pew.country_id.notna()].copy()
    a["Other_7"] = a["share_Other"] + a["share_Folk_Traditional"]
    b["Other_7"] = b["share_Other"] + b["share_Folk_Traditional"]
    comparison_cols = ["Christianity", "Islam", "Hinduism", "Buddhism", "Judaism", "Unaffiliated"]
    cols = [f"share_{r}" for r in comparison_cols] + ["Other_7"]
    comparison = a[["country_id", "country_name"] + cols].merge(
        b[["country_id"] + cols], on="country_id", suffixes=("_wrp", "_pew"), how="inner")
    for col in cols:
        comparison[f"difference_{col}"] = comparison[f"{col}_pew"] - comparison[f"{col}_wrp"]
    comparison["mae_7_categories"] = comparison[[f"difference_{c}" for c in cols]].abs().mean(axis=1)
    comparison.sort_values("mae_7_categories", ascending=False).to_csv(
        OUT / "audit_2010_wrp_vs_pew.csv", index=False)

    # Prefer Pew for 2010 and 2020. No WRP 2010 values are overwritten.
    selected_wrp = wrp.loc[wrp.quality_pass & wrp.country_id.notna() & wrp.year.lt(2010)].copy()
    selected_pew = pew.loc[pew.quality_pass & pew.country_id.notna()].copy()
    selected = pd.concat([selected_wrp, selected_pew], ignore_index=True, sort=False)
    selected = selected.sort_values(["country_id", "year"]).reset_index(drop=True)
    if selected.duplicated(["country_id", "year"]).any():
        raise ValueError("Panel includes duplicate country/year after choosing source")
    total = selected[SHARES].sum(axis=1)
    if not np.allclose(total, 1, atol=1e-8):
        raise ValueError("Selected rows do not sum to 1")
    # Avoid mistaken interpretation of jumps across WRP/Pew definition change.
    selected["previous_source"] = selected.groupby("country_id")["source"].shift(1)
    selected["source_break_from_previous"] = (selected.previous_source.notna() &
        selected.source.ne(selected.previous_source))
    selected["dominant_religion"] = selected[SHARES].idxmax(axis=1).str.removeprefix("share_")
    selected = selected.merge(wpp.drop(columns=["wpp_is_projection"]), on=["country_id", "year"], how="left", validate="many_to_one")
    # Flag 2024+ projection years separately when constructing future prediction features.
    map_codes = set(world.map_iso3.dropna())
    selected["mapped_on_natural_earth"] = selected.country_id.isin(map_codes)
    selected.to_csv(OUT / "religion_panel_8groups.csv", index=False)

    # Named audit files: unmapped rows may still have useful religion estimates.
    wrp.loc[wrp.country_id.isna(), ["year", "cow_id", "country_name", "country_match_method"]].to_csv(
        OUT / "audit_unmatched_wrp.csv", index=False)
    pew.loc[pew.country_id.isna(), ["year", "country_name", "pew_m49_code"]].to_csv(
        OUT / "audit_unmatched_pew.csv", index=False)
    selected.loc[~selected.mapped_on_natural_earth,
                 ["year", "country_id", "country_name", "source"]].drop_duplicates().to_csv(
        OUT / "audit_missing_map_polygons.csv", index=False)
    selected.loc[selected.source_break_from_previous,
                 ["country_id", "year", "country_name", "previous_source", "source"]].to_csv(
        OUT / "audit_source_breaks.csv", index=False)
    # Full WPP retains projection years for downstream feature engineering.
    wpp.to_csv(OUT / "wpp_country_year.csv", index=False)
    world.to_csv(OUT / "natural_earth_country_keys.csv", index=False)

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "wrp_rows_raw": int(len(wrp)),
        "wrp_rows_accepted": int(wrp.quality_pass.sum()),
        "wrp_dual_affiliation_rows": int(wrp.dualrelig.eq(1).sum()),
        "wrp_unmatched_rows": int(wrp.country_id.isna().sum()),
        "pew_rows_accepted": int(pew.quality_pass.sum()),
        "pew_folk_ratio_proxy_rows": int(pew.folk_split_method.eq("WRP_2010_or_earlier_proxy").sum()),
        "pew_unsplit_other_rows": int(pew.folk_split_method.eq("not_identified_all_to_Other").sum()),
        "panel_rows": int(len(selected)),
        "panel_distinct_countries_and_historical_entities": int(selected.country_id.nunique()),
        "panel_date_range": [int(selected.year.min()), int(selected.year.max())],
        "panel_wpp_demographics_matched_pct": round(float(selected.tfr.notna().mean() * 100), 1),
        "panel_map_codes_matched_pct": round(float(selected.mapped_on_natural_earth.mean() * 100), 1),
        "shared_2010_wrp_pew_countries": int(len(comparison)),
        "2010_wrp_pew_average_7group_MAE": (float(comparison.mae_7_categories.mean()) if len(comparison) else None),
        "caveats": [
            "Pew 2010+ folk/other split is proxy-derived or unknown, not Pew-observed.",
            "Sources use distinct religious-identification methods; 2005->2010 jumps can be artificial.",
            "WRP dualrelig=1 rows are excluded, not naively renormalized.",
            "Historic predecessor borders are not assigned to any successor country.",
            "Natural Earth boundaries are modern, not historically valid for 1945 onward.",
            "UN 2024+ values are projections; do not leak them into retrospective validation.",
            "WPP totals may disagree with religion-source population totals."
        ]
    }
    (OUT / "step2_quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n=== STEP 2 QUALITY REPORT ===")
    print(json.dumps(report, indent=2))
    print("\nOutput:", OUT)
    print("Do not start training yet: review audit files and source transitions first.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    main()
