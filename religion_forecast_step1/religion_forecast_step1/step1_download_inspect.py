"""Step 1: Download and inspect WRP, Pew, UN WPP 2024 and Natural Earth.

Usage:
    python step1_download_inspect.py
    python step1_download_inspect.py --no-download
    python step1_download_inspect.py --data-dir ./my_raw_data

Only raw files and inspection reports are produced. No cleaning/merging occurs.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import geopandas as gpd
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SOURCES = {
    "wrp": {
        "url": "https://correlatesofwar.org/wp-content/uploads/WRP_national.csv",
        "name": "WRP_national.csv",
    },
    "wpp": {
        "url": (
            "https://population.un.org/wpp/assets/Excel%20Files/"
            "1_Indicator%20(Standard)/CSV_FILES/"
            "WPP2024_Demographic_Indicators_Medium.csv.gz"
        ),
        "name": "WPP2024_Demographic_Indicators_Medium.csv.gz",
    },
    "natural_earth": {
        "url": "https://naturalearth.s3.amazonaws.com/50m_cultural/"
               "ne_50m_admin_0_countries.zip",
        "name": "ne_50m_admin_0_countries.zip",
    },
}


def get_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3, connect=3, read=2, backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "ReligionForecastResearch/0.1 (academic dataset download)"})
    return session


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(session: requests.Session, url: str, target: Path) -> Path:
    if target.is_file() and target.stat().st_size > 0:
        print(f"[CACHE] {target.name} ({target.stat().st_size:,} bytes)")
        return target
    print(f"[GET] {url}")
    temp = target.with_name(target.name + ".part")
    try:
        with session.get(url, stream=True, timeout=(25, 180)) as response:
            response.raise_for_status()
            mime = response.headers.get("content-type", "").lower()
            if "text/html" in mime:
                raise ValueError(f"HTML received instead of a dataset: {url}")
            with temp.open("wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        if temp.stat().st_size == 0:
            raise ValueError("Empty download")
        with temp.open("rb") as f:
            magic = f.read(8)
        if target.suffix == ".gz" and not magic.startswith(b"\x1f\x8b"):
            raise ValueError("Expected a gzip file; server returned a different format")
        if target.suffix == ".zip" and not magic.startswith(b"PK"):
            raise ValueError("Expected a ZIP file; server returned a different format")
        if magic.lstrip().lower().startswith((b"<html", b"<!doct")):
            raise ValueError("The server returned a web page rather than data")
        temp.replace(target)
        print(f"[OK] Saved {target.name}: {target.stat().st_size:,} bytes")
        return target
    finally:
        temp.unlink(missing_ok=True)


def preview(title: str, frame: pd.DataFrame, rows: int = 5) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")
    print(f"Shape: {frame.shape[0]:,} rows x {frame.shape[1]:,} columns")
    print("Columns:", ", ".join(map(str, frame.columns)))
    print("Dtypes:")
    print(frame.dtypes.astype(str).to_string())
    print(f"First {rows} rows:")
    print(frame.head(rows).to_string(index=False, max_cols=12))
    missing = frame.isna().mean().sort_values(ascending=False).head(10)
    print("Highest missing-value fractions:")
    print((missing * 100).round(1).astype(str).add("%").to_string())


def inspect_wrp(path: Path) -> None:
    try:
        df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, low_memory=False, encoding="latin-1")
    preview("WRP — national religion", df)
    cols = {c.upper(): c for c in df.columns}
    year_col = cols.get("YEAR")
    if year_col:
        years = pd.to_numeric(df[year_col], errors="coerce").dropna().astype(int)
        print(f"Years: {years.min()}–{years.max()} ({years.nunique()} distinct)")
        print("Rows by year:", years.value_counts().sort_index().to_dict())
    print("Country identifiers present:", [cols[x] for x in
          ("COUNTRY", "COWCODE", "STATE", "ISO3", "NUMISO") if x in cols])
    if "ISO3" in cols:
        print("Missing or blank ISO3:",
              int(df[cols["ISO3"]].isna().sum() +
                  df[cols["ISO3"]].astype(str).str.strip().eq("").sum()))
    print("Religion share columns (*PCT):", [c for c in df.columns if
          str(c).upper().endswith("PCT")])
    for check in ("TOTAL", "DUALRELIG", "DUALREL", "DATATYPE", "RECRELIAB"):
        if check in cols:
            print(f"Inspection field {check}: ",
                  df[cols[check]].value_counts(dropna=False).head(8).to_dict())
    if {"COWCODE", "YEAR"}.issubset(cols):
        print("Duplicate (COWCODE, YEAR) rows:",
              int(df.duplicated([cols["COWCODE"], cols["YEAR"]]).sum()))
    print("NOTE: No share renormalization yet. WRP may include dual affiliation.")


def find_csv_header(path: Path, max_lines: int = 70) -> int:
    """UN bulk CSV releases may contain metadata before the actual header."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", errors="replace", newline="") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            fields = [value.strip().strip('"').lower()
                      for value in next(csv.reader([line]))]
            if ("time" in fields or "year" in fields) and any(
                col in fields for col in ("locid", "location", "iso3_code")
            ):
                return i
    raise ValueError("Couldn't find a header containing Time/Year and LocID/Location. "
                     "Inspect the first 70 lines to determine the format.")


def inspect_wpp(path: Path) -> None:
    header_row = find_csv_header(path)
    print(f"\nUN WPP header detected at zero-indexed CSV line {header_row}.")
    df = pd.read_csv(path, skiprows=header_row, low_memory=False,
                     encoding="utf-8-sig", compression="infer")
    preview("UN WPP 2024 — medium demographic indicators", df)
    names = {str(c).lower(): c for c in df.columns}
    for feature in ("time", "year", "iso3_code", "location", "locid",
                    "variant", "tfr", "medianagepop", "tpopulation1july",
                    "netmigrations", "cnmr"):
        if feature in names:
            print(f"Feature candidate {feature}: {names[feature]}")
    year_key = names.get("time", names.get("year"))
    if year_key:
        years = pd.to_numeric(df[year_key], errors="coerce").dropna()
        if len(years):
            print(f"UN years: {int(years.min())}–{int(years.max())}")
    if "iso3_code" in names:
        print("UN rows with ISO3_code:",
              int(df[names["iso3_code"]].notna().sum()))
    print("NOTE: Rows without ISO3_code often represent regional aggregates.")
    print("NOTE: WPP 2024's 2024–2100 values are projections, not observations.")


def inspect_natural_earth(path: Path) -> None:
    if not zipfile.is_zipfile(path):
        raise ValueError("Not a valid Natural Earth ZIP")
    with zipfile.ZipFile(path) as z:
        shapes = [n for n in z.namelist() if n.lower().endswith(".shp")]
    if len(shapes) != 1:
        raise ValueError(f"Expected one shapefile in ZIP, found: {shapes}")
    # The zip:// path is recognized by GDAL/pyogrio; no unzip required.
    gdf = gpd.read_file("zip://" + str(path.resolve()))
    preview("Natural Earth — contemporary country polygons",
            pd.DataFrame(gdf.drop(columns="geometry")))
    print("CRS:", gdf.crs)
    print("Geometry types:", gdf.geometry.geom_type.value_counts().to_dict())
    print("Suggested map identifier fields:", [c for c in
          ("ADM0_A3", "ISO_A3", "SOV_A3", "NAME", "CONTINENT")
          if c in gdf.columns])
    print("NOTE: These polygons are contemporary, not historical borders.")


def inspect_pew(data_dir: Path) -> bool:
    files = sorted(p for p in data_dir.iterdir() if p.is_file() and
                   p.suffix.lower() in {".xlsx", ".xls", ".csv"} and
                   ("pew" in p.name.lower() or "religious_composition" in p.name.lower()))
    if not files:
        print("\n[MANUAL] Pew dataset not found. Sign in at:")
        print("https://www.pewresearch.org/dataset/dataset-of-global-religious-composition-estimates-for-2010-and-2020/")
        print("Save the downloaded workbook as: data/raw/pew_2010_2020.xlsx")
        return False
    for path in files:
        print(f"\n{'=' * 72}\nPEW — {path.name}\n{'=' * 72}")
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path, nrows=8, encoding="utf-8-sig")
            print("Columns:", list(df.columns))
            print(df.head(5).to_string(index=False, max_cols=12))
        elif path.suffix.lower() == ".xlsx":
            with pd.ExcelFile(path, engine="openpyxl") as xls:
                print("Sheets:", xls.sheet_names)
                for sheet in xls.sheet_names[:12]:
                    # 'header=None' preserves title rows for structural inspection.
                    top = pd.read_excel(xls, sheet_name=sheet,
                                        header=None, nrows=7)
                    print(f"\nSheet {sheet!r}, first 7 unmodified rows:")
                    print(top.to_string(index=False, header=False, max_cols=12))
        else:
            print("Older .xls detected: save it as .xlsx, or install xlrd to inspect it.")
    print("NOTE: Prefer Pew's unrounded counts for statistical analysis; do not")
    print("      infer a separate Folk/Traditional share from Pew's 'Other religions'.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--no-download", action="store_true")
    args = parser.parse_args()
    raw = args.data_dir.resolve()
    raw.mkdir(parents=True, exist_ok=True)
    session = get_session()
    results = {}
    for name, info in SOURCES.items():
        path = raw / info["name"]
        if not args.no_download:
            try:
                download(session, info["url"], path)
            except Exception as exc:
                print(f"[WARNING] Couldn't download {name}: {exc}")
                print(f"  Manually download from {info['url']} into {raw}")
        if not path.is_file():
            results[name] = "missing"
            continue
        try:
            {"wrp": inspect_wrp, "wpp": inspect_wpp,
             "natural_earth": inspect_natural_earth}[name](path)
            results[name] = "inspected"
        except Exception as exc:
            results[name] = f"error: {exc}"
            print(f"[ERROR] Cannot inspect {path.name}: {exc}")
    try:
        results["pew"] = "inspected" if inspect_pew(raw) else "missing (manual download)"
    except Exception as exc:
        results["pew"] = f"error: {exc}"
        print(f"[ERROR] Cannot inspect Pew: {exc}")
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_urls": {k: v["url"] for k, v in SOURCES.items()},
        "files": {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
                  for p in sorted(raw.iterdir()) if p.is_file()},
        "inspection_status": results,
    }
    output = raw.parent / "step1_manifest.json"
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nSaved provenance and results to {output}")
    print("FINAL STATUS:", json.dumps(results, indent=2))
    print("Step 1 completed; no data has been cleaned or merged.")
    return 0 if results.get("wrp") == "inspected" else 2


if __name__ == "__main__":
    sys.exit(main())
