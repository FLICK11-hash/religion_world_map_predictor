# Step 7 data sources

Collected 2026-10-20. Every dataset below is used only if its file is present; each run's `step7_report.json`
(`inputs`) records what was found. Nothing is filled in when a file is missing: the model switches to a labelled
fallback, and the report says which one.

Folder conventions (from the step folder `religion_forecast_step1/religion_forecast_step1/`):
- `data/raw/` holds the inputs of earlier steps. `data/raw/step7/` holds the new optional inputs. Both are git-ignored.
- `step7_inputs/` holds small published figures, each with its citation. This folder is tracked in Git.

## 1. Inputs Step 7 requires (already used by earlier steps)

| Dataset | File | Used for | Coverage | Licence / access |
|---|---|---|---|---|
| UN World Population Prospects 2024, demographic indicators (medium) | `data/raw/WPP2024_Demographic_Indicators_Medium.csv.gz` | National TFR, life expectancy, under-5 mortality, mean age at childbearing, female share, population and net migration, 1950-2100. Also the development index used by switching. | 237 countries/areas, 1950-2100 (2101 empty) | CC BY 3.0 IGO; direct download (Step 1) |
| World Religion Project, national (Correlates of War) | `data/raw/WRP_national.csv` | Historical shares 1945-2010 for the history tests and the net-switching evidence | 200 states, 5-year steps; 90 country-years fail the population check and are dropped | Free; direct download (Step 1) |
| Natural Earth admin-0, 1:50m | `data/raw/ne_50m_admin_0_countries.zip` | Distances, land borders and continents for the gravity part of migration; all maps | Present-day borders | Public domain |
| Pew Research Center, religious composition 2010 and 2020 (June 2025) | `data/raw/pew_2010_2020.xlsx`, processed by Step 2 into `data/processed/pew_harmonized.csv` | 2020 start state; the Pew 2010-2020 history window | 201 countries, 7 groups (folk religions inside "other religions") | Free Pew account; Pew terms of use. DOI 10.58094/vhrw-k516 |

**Without `data/processed/pew_harmonized.csv`** (as in the build environment), Step 7 starts from Step 5D's exported 2020 state, `results_step5/headline_country_shares.csv`. That is the same Pew 2020 data with the same Folk/Other split. In that case the Pew 2010-2020 window is neither fitted nor tested. To get it, run Step 2 on your machine.

**Pew's seven groups vs the project's eight.** Pew counts folk religions inside "Other religions". Step 2 splits that group into Folk/Traditional and Other using each country's WRP ratio from 2010 or earlier. The split is a proxy, labelled `folk_split_method`. Step 7 keeps the eight categories:
- WRP history windows are compared only within WRP.
- The Pew window is compared only within Pew.
- Survey and migrant figures in Pew's seven groups are compared with Folk + Other combined.

## 2. Optional inputs fetched by `step7_fetch_data.py`

Run `step7_fetch_data.py`. It tries the official URL first, then a public GitHub mirror (needs `git`).

| Dataset | Official source | GitHub mirror (verified clonable) | File produced | Used for | Status in the build run |
|---|---|---|---|---|---|
| UN DESA International Migrant Stock 2024, destination × origin | https://www.un.org/development/desa/pd/content/international-migrant-stock (file `undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx`; URL pattern inferred) | `tigi/2026-migrant-stock` (unmodified UN file, sha256 `0e10179d…7316`) | the xlsx itself | Migrant network for flows. Each country's mobility (immigrant + emigrant stock per person), which scales its two-way circulation. First-generation stocks and their origin mix in every start year from 1990. Calibration of migrants' religion. | used (68,941 pair-years, 1990-2024) |
| UN WPP 2024 population by 5-year age group and sex (medium) | `…/CSV_FILES/WPP2024_PopulationByAge5GroupSex_Medium.csv.gz` | `open-numbers/ddf--unpop--wpp_population` (`population_age5/`) | `WPP2024_age5_condensed.csv.gz` (years divisible by 5, 0-4 … 80+, total and female) | Real age pyramids for every start year; female share of each reproductive age group for births. This matters in, for example, the Gulf states. | used (237 countries, 1950-2100) |
| UNHCR refugee population statistics | https://api.unhcr.org/population/v1/population/ (CSV zip, no key) | `rfordatascience/tidytuesday` 2023-08-22 (2010-2022) | `unhcr_population.csv` | Loaded and reported. Refugees are already inside the UN migrant stocks, so there is no separate displacement component (see Limitations). | loaded (64,809 rows) |
| World Bank WDI: GDP per capita PPP (NY.GDP.PCAP.PP.KD), urban share (SP.URB.TOTL.IN.ZS) | https://api.worldbank.org/v2/ | `open-numbers/ddf--open_numbers--world_development_indicators` | `wdi_covariates.csv` | Available for covariate tests. Not used in the fitted model: WPP life expectancy and fertility already give a complete 1950-2100 development index. | loaded |
| Pew 2015 country projections 2010-2050 | `assets.pewresearch.org/…/Religious_Composition_by_Country_2010-2050.xlsx` | `datasets/world-religion-projections` (lossy: "<10,000" became 10,000) | `pew2015_rounded_population.csv` | Comparison only | loaded |

Also checked but not used:
- **Abel & Cohen bilateral flow estimates** (figshare 10.6084/m9.figshare.7731233). Their 2010-2020 global total, from the processed copy in `code-4you/world-migration-flows`, implies about 0.0016 movers per person per year. Step 7 uses a lower circulation rate (0-0.0004). The model counts returning emigrants as foreign-born, so higher rates overshoot the UN 2020 foreign-born stocks when simulating from 1990 (see `migration_foreign_born_check.csv`).
- **Barro-Lee schooling** (`barrolee/BarroLeeDataSet`). Available as a covariate; not used.

## 3. Published figures transcribed into `step7_inputs/` (tracked, with citations)

These came from web search excerpts of Pew pages, because pewresearch.org could not be reached from the build environment. Each row carries `evidence_type`. **Check rows marked `pew_page_text` against the report PDFs before citing them.** Set `verified=no` in a row to exclude it.

| File | Content | Used how |
|---|---|---|
| `switching_lifetime_observed.csv` | 44 lifetime cells (percent of adults raised in A who now identify with B) for 12 countries. Sources: Pew 2025 switching report (2024 surveys; ESP, SWE, KOR, JPN, TUR, SGP, LKA, THA, IND, BGD, ISR); Pew US Religious Landscape Study 2023-24; Pew 2014 RLS full matrix via FiveThirtyEight. Each derivation is stated, e.g. Spain: (87 raised Christian − 36 left) / 87. | Binomial likelihood terms in the switching fit, with effective n 150-500. Never used in history tests: they would leak post-2020 information. |
| `switching_global_targets.csv` | Pew 2025, adults 18-54 in 117 countries: left per 100 raised. Christians 17.1, Buddhists 22.1, unaffiliated 7.5, Muslims and Hindus about 1. Also joined per 100 and HDI medians. | Calibrates the "survey level" of switching. Runs mix it with the level fitted to net changes. |
| `migrant_religion_published.csv` | Pew 2024 religious composition of migrant stocks: world (47% Christian, 29% Muslim, 13% unaffiliated …), migrants living in Europe and MENA, India-born migrants (16% Christian vs 2% of India), US foreign-born adults | Calibrates who migrates where (`step7_estimate.calibrate_affinity`: destination affinity κ and minority effect λ) |
| `second_generation_published.csv` | France TeO2 (Insee-Ined 2023): retention of raised Muslims 91%, raised Christians 67-69%. ESS 33 countries (Molteni & van Tubergen 2022): disaffiliation of Christian-origin immigrants, second generation 17.75% vs first 14.27% | Sets the ranges for generation switching intensity |
| `published_reference_figures.csv` | Pew 2025 world shares 2010/2020, regional 2020 shares, TFR 2010-15 (Muslims 3.1, Christians 2.7) | Checks |

## 4. Needs a manual download (free registration), then a tidy CSV

| Data | Where | What to save | Why it matters |
|---|---|---|---|
| Pew, *Religious Composition of the World's Migrants, 1990-2020* (Aug 2024; DOI 10.58094/zk7y-q042) | https://www.pewresearch.org/dataset/dataset-religious-composition-of-the-worlds-migrants-1990-2020/ (free Pew account) | `data/raw/step7/pew_migrants_religion.csv` with columns `country_iso3, side (emigrants/immigrants), year`, plus one column per Pew group (Christians, Muslims, Hindus, Buddhists, Jews, Other religions, Religiously unaffiliated) | Replaces the aggregate selectivity calibration with country-level religion of emigrants and immigrants. If the download includes origin × destination pairs, ask for a corridor-level loader (not verified that it does). |
| Pew Spring 2024 Global Attitudes survey (36 countries; childhood vs current religion) | https://www.pewresearch.org/dataset/spring-2024-survey-data/ (free account; SPSS) | Tabulate weighted raised × current shares by country into `data/raw/step7/switching_lifetime_observed.csv` (same columns as the tracked file; set `n_raised` to the unweighted base) | Replaces the search-excerpt cells with the full 36-country matrices |
| ISSP 2018 Religion IV (GESIS ZA7570; raised religion asked) | https://www.gesis.org/en/issp/data-and-documentation/religion/2018 (free GESIS registration) | Same tidy format | About 30 more countries' lifetime matrices |
| US General Social Survey (RELIG16 × RELIG) | https://gss.norc.org/get-the-data.html (no account) | Same tidy format, by decade | US cohort trends in switching |
| ESS (rlgblg, rlgblge: ever belonged) | https://ess.sikt.no (free account) | Disaffiliation shares only (ESS does not ask the religion raised in) | European disaffiliation by cohort |
| Religion-specific fertility (censuses, DHS, India NFHS, Israel CBS …) | National statistical offices | `data/raw/step7/religion_fertility_observed.csv`: `country_iso3, religion, tfr, period, source, url, verified` | Replaces the damped Pew global ratios country by country |
| WVS wave 7 | https://www.worldvaluessurvey.org (free, conditions of use) | Not used: no raised-religion item was found in wave 7 | — |

## 5. Known limitations of the data

- WPP 2024 historical estimates are revised series, not what was known at the time, so the history tests are retrospective.
- The UN migrant stocks give each person's birth country, not their religion. Each corridor's religious mix comes from the origin's mix, the minority effect and destination affinity, calibrated to Pew's aggregate figures. The world Christian share of migrants remains about 5 points too low. Pew's corridor-level data would replace this calibration.
- Pew's search-excerpt figures have not been checked against the PDFs in this environment.
- Refugee movements are in the stocks and in WPP net migration. There is no separate stochastic displacement shock, because no estimate of displacement frequency from UNHCR data has been validated yet.
