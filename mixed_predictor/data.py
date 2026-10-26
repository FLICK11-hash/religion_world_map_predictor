"""World religious composition, 1970-2010, from the World Religion Project.

The manual predictor hardcodes seven year-snapshots, three of which its own header admits came
from an AI overview. This module replaces them with a published dataset, and in doing so has to
deal with the one thing that makes that dataset tricky: WRP follows the Correlates of War state
system, so countries *enter* it as they gain independence -- 65 states in 1945, 194 in 2010.
Summing every country in each year therefore measures decolonisation as much as religious change.
We use a balanced panel: only countries observed in every year of the window.

Source: Zeev Maoz and Errol A. Henderson (2013), "The World Religion Dataset, 1945-2010",
International Interactions 39(3), 265-291. National-level file, religionists by denomination.
"""
from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
DERIVED = HERE / "world_shares_wrp.csv"
# The raw file lives with the research model. Only needed for --rebuild-data; the derived CSV
# above is committed so this package runs on its own.
RAW = HERE.parent / "religion_forecast_step1" / "religion_forecast_step1" / "data" / "raw" / "WRP_national.csv"

GROUPS = ["Christianity", "Islam", "Hinduism", "Buddhism",
          "Judaism", "Folk_Traditional", "Other", "Unaffiliated"]

# WRP count columns per group. Same grouping the research model uses, so the three
# implementations are comparing the same eight categories.
WRP_COLUMNS = {
    "Christianity": ["chrstgen"],
    "Islam": ["islmgen"],
    "Hinduism": ["hindgen"],
    "Buddhism": ["budgen"],
    "Judaism": ["judgen"],
    "Folk_Traditional": ["shntgen", "taogen", "confgen", "syncgen", "anmgen"],
    "Other": ["zorogen", "sikhgen", "bahgen", "jaingen", "othrgen"],
    "Unaffiliated": ["nonrelig"],
}

# 1945 is excluded whatever window is asked for: 65 states, no India, and a world total of
# 1.65bn against 2.27bn in 1950. It is a coverage gap, not a measurement.
FIRST_USABLE_YEAR = 1950
DEFAULT_START = 1970


def _number(text: str) -> float:
    return float(text) if text not in ("", ".", "NA") else 0.0


def build_from_raw(start_year: int = DEFAULT_START, raw: Path = RAW) -> tuple[list[int], dict, dict]:
    """Return (years, {year: {group: share}}, provenance) from the raw WRP file."""
    if not raw.exists():
        raise FileNotFoundError(
            f"{raw} not found. It is git-ignored; fetch it with the research model's\n"
            f"  python run.py fetch\n"
            f"or just use the committed {DERIVED.name}, which needs no raw data."
        )
    rows = list(csv.DictReader(raw.open(encoding="utf8")))
    years = sorted({int(r["year"]) for r in rows if int(r["year"]) >= max(start_year, FIRST_USABLE_YEAR)})
    if len(years) < 4:
        raise ValueError(f"start_year={start_year} leaves only {len(years)} observations; need 4+")

    seen = {y: {r["state"] for r in rows if int(r["year"]) == y} for y in years}
    balanced = set.intersection(*seen.values())

    totals = {y: {g: 0.0 for g in GROUPS} for y in years}
    population = {y: 0.0 for y in years}
    for r in rows:
        y = int(r["year"])
        if y not in totals or r["state"] not in balanced:
            continue
        population[y] += _number(r["pop"])
        for group, columns in WRP_COLUMNS.items():
            totals[y][group] += sum(_number(r[c]) for c in columns)

    shares = {}
    for y in years:
        counted = sum(totals[y].values())
        shares[y] = {g: totals[y][g] / counted for g in GROUPS}

    all_2010 = sum(_number(r["pop"]) for r in rows if int(r["year"]) == 2010)
    kept_2010 = sum(_number(r["pop"]) for r in rows
                    if int(r["year"]) == 2010 and r["state"] in balanced)
    provenance = {
        "source": "WRP national file (Maoz & Henderson 2013)",
        "start_year": years[0],
        "end_year": years[-1],
        "observations": len(years),
        "countries": len(balanced),
        "panel": "balanced: countries present in every year of the window",
        "coverage_2010_pct": 100.0 * kept_2010 / all_2010,
        "world_population_2010_covered": kept_2010,
    }
    return years, shares, provenance


def save(years, shares, provenance, path: Path = DERIVED) -> None:
    with path.open("w", newline="", encoding="utf8") as fh:
        for key, value in provenance.items():
            fh.write(f"# {key}: {value}\n")
        fh.write("# shares sum to 1 across the eight groups in every row\n")
        writer = csv.writer(fh)
        writer.writerow(["year", *GROUPS])
        for y in years:
            writer.writerow([y, *(f"{shares[y][g]:.6f}" for g in GROUPS)])


def load(path: Path = DERIVED) -> tuple[list[int], dict, dict]:
    """Read the committed derived CSV. This is what the model uses by default."""
    provenance, body = {}, []
    for line in path.read_text(encoding="utf8").splitlines():
        if line.startswith("#"):
            key, _, value = line[1:].strip().partition(": ")
            if value:
                provenance[key] = value
        elif line.strip():
            body.append(line)
    rows = list(csv.DictReader(body))
    years = [int(r["year"]) for r in rows]
    shares = {}
    for row in rows:
        raw = {g: float(row[g]) for g in GROUPS}
        total = sum(raw.values())  # the file rounds to 6dp, so renormalise to exactly 1
        shares[int(row["year"])] = {g: v / total for g, v in raw.items()}
    return years, shares, provenance
