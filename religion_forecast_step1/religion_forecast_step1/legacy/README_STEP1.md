# World Religion Forecasting — Step 1

## What it does
Downloads original source files for World Religion Project v1.1, UN WPP 2024 medium-variant indicators and Natural Earth 1:50m countries. Prints dataset shapes, headers, example rows, missingness, years and useful identifiers. If a Pew workbook is placed in `data/raw/`, inspects its sheet names and unmodified top rows. Saves a SHA-256 provenance manifest in `data/step1_manifest.json`. Does not merge, recode or alter the original data.

## Setup

From PowerShell on Windows:

```powershell
mkdir religion-forecast
cd religion-forecast
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python step1_download_inspect.py
```

If PowerShell refuses to activate the virtual environment, use `\.venv\Scripts\python.exe -m pip install -r requirements.txt` and `\.venv\Scripts\python.exe step1_download_inspect.py` instead.

From Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python step1_download_inspect.py
```

## Pew manual download
1. Open: https://www.pewresearch.org/dataset/dataset-of-global-religious-composition-estimates-for-2010-and-2020/
2. Sign into a free Pew Research Center account, agree to their dataset terms, and download the workbook.
3. Save/rename it to: `data/raw/pew_2010_2020.xlsx`
4. Run `python step1_download_inspect.py --no-download` to inspect every available raw dataset without trying the network again.

Pew combines folk/traditional beliefs with **Other religions**, unlike the eight-target-category specification. We will not invent an eighth Pew category.

## If downloads are blocked
Use the three official pages, download their files manually and place them in `data/raw/` with these exact names:
- `WRP_national.csv` from https://correlatesofwar.org/data-sets/world-religion-data/
- `WPP2024_Demographic_Indicators_Medium.csv.gz` from https://population.un.org/wpp/ under CSV downloads
- `ne_50m_admin_0_countries.zip` from https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/

The script prints explicit missing-file errors and can still inspect whichever files are present.

## Interpretation warnings
- WRP percentages are in [0,1]. Its codebook documents occasional overlapping religion memberships (`DUALREL`), plus interpolation/hand adjustments. Do not force a sum of one without a documented decision.
- WRP `COWCODE` / `STATE` is not an ISO3 code; `ISO3` may be missing or historical. UN WPP typically uses `ISO3_code`; Natural Earth uses `ADM0_A3`/`ISO_A3`. Handle country changes separately in Step 2.
- WPP 2024 projections (2024–2100) must not be treated as observations when doing forward-chaining validation.
- Natural Earth uses contemporary country geometry, so 1950 maps will need an explicit choice of geographic reference frame.
- From 2025 in five-year increments, the final point before 3026 would be 3025. Treat 3026 separately with one-year interpolation or an explicit annual transition, rather than silently changing the target year.
