# Data

Collected 2026-10. Every dataset is used only if its file is present, and
`data/projections/projection_report.json` (`inputs`) records what each run found. Nothing is
filled in when a file is missing: the model switches to a labelled fallback and says which.

Folder conventions, relative to the repository root. Every input below is listed with its
source URL, the SHA-256 of the exact file the committed results used, and its licence in
`config/data_manifest.json`; `python scripts/verify_data.py` checks a local `data/` against it.

- `data/raw/` holds downloaded source data; `data/raw/extra/` the optional datasets. Both are
  git-ignored. (`data/raw/step7/` is the old name for `extra` and is still read, so an existing
  download need not be repeated.)
- `inputs/` holds small published figures transcribed with citations. Tracked in git.

## 1. Required

| Dataset | File | Used for | Coverage | Licence / access |
|---|---|---|---|---|
| UN World Population Prospects 2024, demographic indicators (medium) | `data/raw/WPP2024_Demographic_Indicators_Medium.csv.gz` | national TFR, life expectancy, under-5 mortality, mean age at childbearing, female share, population, net migration 1950-2100; also the development index used by switching | 237 countries and areas, 1950-2100 | CC BY 3.0 IGO; direct download |
| World Religion Project, national (Correlates of War) | `data/raw/WRP_national.csv` | historical shares 1945-2010 for the backtests and the net-change evidence | 200 states, 5-year steps; 90 country-years fail the population check and are dropped | free; direct download |
| Natural Earth admin-0, 1:50m | `data/raw/ne_50m_admin_0_countries.zip` | distances, land borders, continents and every map | present-day borders | public domain |
| Pew Research Center, religious composition 2010 and 2020 (June 2025) | `data/raw/pew_2010_2020.xlsx` → `data/processed/pew_harmonized.csv` | the 2020 start state and the Pew 2010-2020 backtest window | 201 countries, 7 groups | free Pew account; Pew terms of use. DOI 10.58094/vhrw-k516 |

`python scripts/prepare_raw_data.py` fetches the first three and writes a SHA-256 manifest. The Pew
workbook is behind a free account and must be downloaded by hand; `python scripts/prepare_pew_panel.py`
then builds the harmonised panel.

**Without `data/processed/pew_harmonized.csv`** — as in the environment where the committed
results were produced — the model starts from `results_step5/headline_country_shares.csv`, the
same Pew 2020 data exported by the earlier Step 5D pipeline with the same Folk/Other split. In
that case the Pew 2010-2020 window is neither fitted nor tested, and every report says so.

**Pew's seven groups against the model's eight.** Pew's 2025 release counts folk religions inside
"other religions". `scripts/prepare_pew_panel.py` splits that group using each country's WRP ratio from
2010 or earlier; the split is a proxy and is labelled `folk_split_method`. The model keeps eight
categories: WRP windows are compared only within WRP, the Pew window only within Pew, and survey
or migrant figures given in Pew's seven are compared with Folk + Other combined.

## 2. Optional, fetched by `run.py fetch`

Each tries the official URL first, then a public GitHub mirror.

| Dataset | Official source | File produced | Used for | In the committed run |
|---|---|---|---|---|
| UN DESA International Migrant Stock 2024, destination × origin | un.org/development/desa/pd/content/international-migrant-stock | the xlsx itself | the migrant network; each country's mobility; first-generation stocks and their origin mix from 1990; calibration of the religion of migrants | used (68,941 pair-years, 1990-2024) |
| UN WPP 2024 population by 5-year age group and sex | UN WPP CSV files | `WPP2024_age5_condensed.csv.gz` | real age pyramids for every start year; the female share of each reproductive age group | used (237 countries, 1950-2100) |
| UNHCR refugee population statistics | api.unhcr.org/population/v1/population/ | `unhcr_population.csv` | loaded and reported; refugees are already inside the UN migrant stocks, so there is no separate displacement component | loaded (64,809 rows) |
| World Bank WDI: GDP per capita PPP, urban share | api.worldbank.org/v2/ | `wdi_covariates.csv` | available for covariate tests; not used, because WPP life expectancy and fertility already give a complete 1950-2100 development index | loaded |
| Pew 2015 country projections 2010-2050 | assets.pewresearch.org | `pew2015_rounded_population.csv` | the external benchmark and the forecast-skill yardstick (section 5) | used |

Also checked: **Abel & Cohen** bilateral flow estimates (figshare 10.6084/m9.figshare.7731233),
which imply about 0.0016 movers per person per year. The model uses a lower circulation rate
because it counts returning emigrants as foreign-born; see `docs/METHODS.md`.

## 3. Published figures transcribed into `inputs/` (tracked, with citations)

These were read in web-search result text that quotes the source, because the publishers' sites
could not be reached from the build environment. Every row carries an `evidence` field, and rows
whose only trace is a single uncited compilation are marked `verified=no` and are not used.

| File | Content | Used how |
|---|---|---|
| `fertility_by_religion.csv` | fertility by religious group at three levels: world (Pew 2015, all eight groups), region (Pew 2015: Europe, sub-Saharan Africa) and country (India NFHS-5 2019-21, Israel CBS 2022, Nigeria from Stonawski et al. 2016, United States Pew 2025) | the `rel` term in births. Country figures cover 24% of world population, regional 21%, world the remaining 55%. |
| `switching_lifetime_observed.csv` | 67 lifetime cells (percent of adults raised in A who now identify with B) in 33 countries. Pew 2025 switching report, the US Religious Landscape Study, and the 2014 RLS matrix via FiveThirtyEight | binomial likelihood terms in the switching fit, effective n 150-500. Never used in the history tests, which they would contaminate with post-2020 information. |
| `switching_global_targets.csv` | Pew 2025, adults 18-54 in 117 countries: left per 100 raised (Christians 17.1, Buddhists 22.1, unaffiliated 7.5, Muslims and Hindus about 1) | calibrates the survey level of switching |
| `migrant_religion_published.csv` | Pew 2024 religious composition of migrant stocks: world, Europe, MENA, India-born, US foreign-born | calibrates κ and λ, who migrates where |
| `second_generation_published.csv` | France TeO2 (Insee-Ined 2023); ESS 33 countries (Molteni & van Tubergen 2022) | sets the ranges for generation switching intensity |
| `published_reference_figures.csv` | Pew 2025 world shares 2010 and 2020, regional 2020 shares | checks |

### What changed in the fertility data

Earlier versions used one global ratio per religion for every country, damped by `phi`, with no
country figures at all. Three consequences were wrong and are now fixed:

- **Israel.** Jewish fertility is now *above* Muslim fertility in Israel (CBS: 3.06 against 2.75
  in 2024; the crossover was about 2020). The global ratios had it the other way round, so the
  model made Israel's Jewish share fall for a reason that is not true.
- **Europe.** Pew's regional figures put Christian fertility exactly *at* the regional average and
  unaffiliated fertility at 0.875 of it, where the global ratios imply 1.08 and 0.68.
- **Buddhism.** The world figure was 1.7, carried over from a file that recorded it as entered
  from memory. Pew's published value is 1.6.

## 4. Still needs a manual download

| Data | Where | What to save | Why it matters |
|---|---|---|---|
| Pew, *Religious Composition of the World's Migrants, 1990-2020* (DOI 10.58094/zk7y-q042) | pewresearch.org dataset page (free account) | `data/raw/extra/pew_migrants_religion.csv` with `country_iso3, side, year` and one column per Pew group | replaces the two-parameter calibration with country-level religion of migrants |
| Pew Spring 2024 Global Attitudes (36 countries; childhood and current religion) | pewresearch.org dataset page (free account, SPSS) | weighted raised × current shares per country, in the format of `inputs/switching_lifetime_observed.csv` | replaces the search-excerpt cells with full matrices |
| ISSP 2018 Religion IV (GESIS ZA7570) | gesis.org (free registration) | the same format | about 30 more countries |
| US General Social Survey (RELIG16 × RELIG) | gss.norc.org | the same format, by decade | US cohort trends |
| DHS final reports: fertility by religion | dhsprogram.com | rows in `inputs/fertility_by_religion.csv` | the religion cross-tabulation is in the full country reports, not the headline tables or STATcompiler; it would extend country-level fertility coverage across sub-Saharan Africa |
| Israel CBS, *Fertility Rates by Level of Religiosity 1979-2024* | cbs.gov.il | rows in `inputs/fertility_by_religion.csv` | the primary table behind the Israel figures used here, which came through the Taub Center |

## 5. Known limitations of the data

- WPP 2024 historical estimates are a revised series, not what was known at the time, so the
  backtests are retrospective.
- **Two Pew vintages disagree about the same year by more than most projected thirty-year change.**
  Pew's 2015 report puts the 2020 world Christian share at 31.1%; Pew's 2025 measurement puts it
  at 28.8%. Scored country by country the gap is 10.7 points population-weighted, and **China
  alone accounts for 69% of it** (Vietnam a further 6%) — a reclassification between folk religion
  and the unaffiliated, not a forecasting error. Any country-level result for China should be read
  with this in mind.
- The UN migrant stocks give each person's country of birth, not their religion. Each corridor's
  mix comes from the origin's mix, the minority effect and destination affinity, calibrated to
  Pew's aggregates. The world Christian share of migrants remains about 5 points too low.
- UN stocks also carry historical corridors into the network: about 0.9 million each way between
  India and Pakistan in 2020-2050 is a legacy of 1947.
- Refugee movements are inside the stocks and inside WPP net migration. There is no separate
  displacement shock, because no estimate of displacement frequency has been validated here.
- The Pew search-excerpt figures have not been checked against the PDFs; no host was reachable
  from the build environment.
