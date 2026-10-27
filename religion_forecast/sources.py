"""Country-year religion shares from WRP (1945-2010), demography from WPP, and geography from
Natural Earth, without geopandas. Used by step5e_wrp_hindcast.py to test the cohort model on history.

Share rules replicate Step 2 (WRP_FIELDS and normalize_valid). The COW -> ISO3 map is written out
here and checked against WPP population for every country-year (see check_population_match).
Historic polities with no WPP counterpart are excluded rather than guessed.
"""
from __future__ import annotations

import struct
import zipfile
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

RELIGIONS = ["Christianity", "Islam", "Hinduism", "Buddhism", "Judaism",
             "Folk_Traditional", "Other", "Unaffiliated"]
WRP_FIELDS = {
    "Christianity": ["chrstgenpct"], "Islam": ["islmgenpct"], "Hinduism": ["hindgenpct"],
    "Buddhism": ["budgenpct"], "Judaism": ["judgenpct"],
    "Folk_Traditional": ["shntgenpct", "taogenpct", "confgenpct", "syncgenpct", "anmgenpct"],
    "Other": ["zorogenpct", "sikhgenpct", "bahgenpct", "jaingenpct", "othrgenpct"],
    "Unaffiliated": ["nonreligpct"],
}

# COW state code -> ISO3 for the states in WRP that exist in WPP. Historic codes are left out on purpose:
# 260/265 (West/East Germany), 315 (Czechoslovakia), 345 (Yugoslavia), 678/680 (North/South Yemen),
# 817 (South Vietnam). Their later successors are matched only where the population check passes.
COW_TO_ISO3 = {
    2: "USA", 20: "CAN", 31: "BHS", 40: "CUB", 41: "HTI", 42: "DOM", 51: "JAM", 52: "TTO", 53: "BRB",
    54: "DMA", 55: "GRD", 56: "LCA", 57: "VCT", 58: "ATG", 60: "KNA", 70: "MEX", 80: "BLZ", 90: "GTM",
    91: "HND", 92: "SLV", 93: "NIC", 94: "CRI", 95: "PAN", 100: "COL", 101: "VEN", 110: "GUY",
    115: "SUR", 130: "ECU", 135: "PER", 140: "BRA", 145: "BOL", 150: "PRY", 155: "CHL", 160: "ARG",
    165: "URY", 200: "GBR", 205: "IRL", 210: "NLD", 211: "BEL", 212: "LUX", 220: "FRA", 221: "MCO",
    223: "LIE", 225: "CHE", 230: "ESP", 232: "AND", 235: "PRT", 255: "DEU", 290: "POL", 305: "AUT",
    310: "HUN", 316: "CZE", 317: "SVK", 325: "ITA", 331: "SMR", 338: "MLT", 339: "ALB", 341: "MNE",
    343: "MKD", 344: "HRV", 346: "BIH", 347: "XKX", 349: "SVN", 350: "GRC", 352: "CYP", 355: "BGR",
    359: "MDA", 360: "ROU", 365: "RUS", 366: "EST", 367: "LVA", 368: "LTU", 369: "UKR", 370: "BLR",
    371: "ARM", 372: "GEO", 373: "AZE", 375: "FIN", 380: "SWE", 385: "NOR", 390: "DNK", 395: "ISL",
    402: "CPV", 403: "STP", 404: "GNB", 411: "GNQ", 420: "GMB", 432: "MLI", 433: "SEN", 434: "BEN",
    435: "MRT", 436: "NER", 437: "CIV", 438: "GIN", 439: "BFA", 450: "LBR", 451: "SLE", 452: "GHA",
    461: "TGO", 471: "CMR", 475: "NGA", 481: "GAB", 482: "CAF", 483: "TCD", 484: "COG", 490: "COD",
    500: "UGA", 501: "KEN", 510: "TZA", 516: "BDI", 517: "RWA", 520: "SOM", 522: "DJI", 530: "ETH",
    531: "ERI", 540: "AGO", 541: "MOZ", 551: "ZMB", 552: "ZWE", 553: "MWI", 560: "ZAF", 565: "NAM",
    570: "LSO", 571: "BWA", 572: "SWZ", 580: "MDG", 581: "COM", 590: "MUS", 591: "SYC", 600: "MAR",
    615: "DZA", 616: "TUN", 620: "LBY", 625: "SDN", 630: "IRN", 640: "TUR", 645: "IRQ", 651: "EGY",
    652: "SYR", 660: "LBN", 663: "JOR", 666: "ISR", 670: "SAU", 679: "YEM", 690: "KWT", 692: "BHR",
    694: "QAT", 696: "ARE", 698: "OMN", 700: "AFG", 701: "TKM", 702: "TJK", 703: "KGZ", 704: "UZB",
    705: "KAZ", 710: "CHN", 712: "MNG", 713: "TWN", 731: "PRK", 732: "KOR", 740: "JPN", 750: "IND",
    760: "BTN", 770: "PAK", 771: "BGD", 775: "MMR", 780: "LKA", 781: "MDV", 790: "NPL", 800: "THA",
    811: "KHM", 812: "LAO", 816: "VNM", 820: "MYS", 830: "SGP", 835: "BRN", 840: "PHL", 850: "IDN",
    860: "TLS", 900: "AUS", 910: "PNG", 920: "NZL", 935: "VUT", 940: "SLB", 946: "KIR", 947: "TUV",
    950: "FJI", 955: "TON", 970: "NRU", 983: "MHL", 986: "PLW", 987: "FSM", 990: "WSM",
}
# Natural Earth code -> WPP code where they differ (step6 uses the same alias).
NE_ALIAS = {"KOS": "XKX"}


def _dbf_frame(blob: bytes) -> pd.DataFrame:
    n, header_len, record_len = struct.unpack("<xxxxIHH", blob[:12])
    fields, off = [], 32
    while blob[off] != 0x0D:
        fields.append((blob[off:off + 11].split(b"\0")[0].decode("latin1"), blob[off + 16]))
        off += 32
    rows, pos = [], header_len
    for _ in range(n):
        rec, k, row = blob[pos:pos + record_len], 1, {}
        for name, ln in fields:
            row[name] = rec[k:k + ln].decode("utf8", "replace").strip()
            k += ln
        rows.append(row)
        pos += record_len
    return pd.DataFrame(rows)


def _shp_records(blob: bytes) -> list[list[np.ndarray]]:
    """Polygon rings per record (empty list for null shapes)."""
    shape_type = struct.unpack("<i", blob[32:36])[0]
    if shape_type not in (0, 5, 15, 25):
        raise ValueError(f"Expected polygon shapefile, got shape type {shape_type}")
    out, off = [], 100
    while off + 8 <= len(blob):
        _, clen = struct.unpack(">ii", blob[off:off + 8])
        off += 8
        content = blob[off:off + 2 * clen]
        off += 2 * clen
        if struct.unpack("<i", content[:4])[0] == 0:
            out.append([])
            continue
        nparts, npts = struct.unpack("<ii", content[36:44])
        parts = np.frombuffer(content, dtype="<i4", count=nparts, offset=44)
        pts = np.frombuffer(content, dtype="<f8", count=2 * npts, offset=44 + 4 * nparts).reshape(-1, 2)
        bounds = list(parts) + [npts]
        out.append([pts[bounds[i]:bounds[i + 1]] for i in range(nparts)])
    return out


def _ring_centroid(ring: np.ndarray) -> tuple[float, float, float]:
    x, y = ring[:, 0], ring[:, 1]
    x1, y1 = np.roll(x, -1), np.roll(y, -1)
    cross = x * y1 - x1 * y
    area = cross.sum() / 2
    if abs(area) < 1e-12:
        return float(x.mean()), float(y.mean()), 0.0
    return (float(((x + x1) * cross).sum() / (6 * area)), float(((y + y1) * cross).sum() / (6 * area)),
            float(abs(area)))


def load_geography(zip_path: Path, cell: float = 0.02, min_shared_cells: int = 2):
    """Returns (table, neighbours). table: iso3, name, continent, lat, lon, index into neighbours.
    neighbours: dict iso3 -> set of land neighbours, inferred from vertices shared between countries
    (two or more shared cells). Approximates geopandas 'touches' on Natural Earth 50m."""
    with zipfile.ZipFile(zip_path) as z:
        dbf = _dbf_frame(z.read("ne_50m_admin_0_countries.dbf"))
        recs = _shp_records(z.read("ne_50m_admin_0_countries.shp"))
    if len(dbf) != len(recs):
        raise ValueError("Natural Earth .dbf and .shp record counts differ")
    iso = dbf["ISO_A3"].astype(str).str.upper()
    fallback = ~iso.str.fullmatch("[A-Z]{3}")
    iso = iso.where(~fallback, dbf["ADM0_A3"].astype(str).str.upper())
    iso = iso.replace(NE_ALIAS)
    rows, points = [], defaultdict(list)
    best = {}
    for i, rings in enumerate(recs):
        code = iso.iat[i]
        if not isinstance(code, str) or len(code) != 3 or not rings:
            continue
        for ring in rings:
            points[code].append(ring)
            cx, cy, area = _ring_centroid(ring)
            if code not in best or area > best[code][2]:
                best[code] = (cx, cy, area)
        rows.append({"iso3": code, "name": dbf["NAME"].iat[i], "continent": dbf["CONTINENT"].iat[i]})
    table = (pd.DataFrame(rows).drop_duplicates("iso3").set_index("iso3"))
    table["lon"] = [best[c][0] for c in table.index]
    table["lat"] = [best[c][1] for c in table.index]

    grid = defaultdict(set)
    for code, rings in points.items():
        pts = np.vstack(rings)
        keys = np.unique(np.round(pts / cell).astype(np.int64), axis=0)
        for kx, ky in keys:
            grid[(int(kx), int(ky))].add(code)
    shared = Counter()
    for members in grid.values():
        if len(members) > 1:
            for a, b in combinations(sorted(members), 2):
                shared[(a, b)] += 1
    neighbours = {c: set() for c in table.index}
    for (a, b), k in shared.items():
        if k >= min_shared_cells and a in neighbours and b in neighbours:
            neighbours[a].add(b)
            neighbours[b].add(a)
    return table, neighbours


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dlam = p2 - p1, np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlam / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def load_wpp(raw: Path) -> pd.DataFrame:
    p = pd.read_csv(raw / "WPP2024_Demographic_Indicators_Medium.csv.gz", low_memory=False)
    p = p[p.ISO3_code.notna() & p.Variant.astype(str).str.lower().eq("medium")]
    num = lambda s: pd.to_numeric(s, errors="coerce")
    return pd.DataFrame({
        "country_id": p.ISO3_code.astype(str), "year": num(p.Time).astype(int),
        "tfr": num(p.TFR), "median_age": num(p.MedianAgePop), "e0": num(p.LEx),
        "pop": num(p.TPopulation1July) * 1000.0, "net_migrations": num(p.NetMigrations) * 1000.0,
    }).reset_index(drop=True)


def load_wrp(raw: Path) -> pd.DataFrame:
    """Valid country-years only (dualrelig == 0 and category totals within 1%), shares renormalised."""
    w = pd.read_csv(raw / "WRP_national.csv", low_memory=False)
    out = pd.DataFrame({"year": w.year.astype(int), "cow": w.state.astype(int), "name": w.name.astype(str),
                        "wrp_pop": pd.to_numeric(w["pop"], errors="coerce"),
                        "dualrelig": pd.to_numeric(w.dualrelig, errors="coerce")})
    out["country_id"] = out.cow.map(COW_TO_ISO3)
    for religion, cols in WRP_FIELDS.items():
        vals = pd.concat([pd.to_numeric(w[c], errors="coerce") for c in cols], axis=1)
        out[f"share_{religion}"] = vals.sum(axis=1, min_count=len(cols))
    cols = [f"share_{r}" for r in RELIGIONS]
    total = out[cols].sum(axis=1, min_count=len(cols))
    ok = (out.dualrelig.eq(0) & out.country_id.notna() & total.between(0.99, 1.01)
          & out[cols].ge(-1e-8).all(axis=1))
    out["valid"] = ok
    out[cols] = out[cols].clip(lower=0).div(total, axis=0).where(ok, np.nan)
    return out


def check_population_match(wrp: pd.DataFrame, wpp: pd.DataFrame, lo: float = 0.8, hi: float = 1.25) -> pd.DataFrame:
    """WRP persons / WPP persons per country-year. Rows outside [lo, hi] are flagged, not used."""
    m = wrp.merge(wpp[["country_id", "year", "pop"]], on=["country_id", "year"], how="left")
    m["pop_ratio"] = m.wrp_pop / m["pop"]
    m["pop_ok"] = m.pop_ratio.between(lo, hi)
    return m


def load_all(raw: Path, zip_path: Path):
    wpp = load_wpp(raw)
    wrp = check_population_match(load_wrp(raw), wpp)
    wrp["use"] = wrp.valid & wrp.pop_ok
    geo, nbrs = load_geography(zip_path)
    return wrp, wpp, geo, nbrs
