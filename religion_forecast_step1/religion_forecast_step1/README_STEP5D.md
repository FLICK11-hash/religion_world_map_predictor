# Step 5D - religion-specific cohort model

Alternative to 5/5B/5C (their outputs are untouched). Instead of tilting shares, every country is split into
religious groups, each with its own age structure, fertility, migration share and net switching, and shares are
read off the resulting populations.

## Run (from this folder)

```powershell
.\.venv\Scripts\python.exe test_step5d_engine.py          # engine unit tests, no data needed
.\.venv\Scripts\python.exe step5d_cohort_forecast.py --runs 120 --seed 62
.\.venv\Scripts\python.exe verify_step5d.py
.\.venv\Scripts\python.exe step5d_make_maps.py
.\.venv\Scripts\python.exe step5d_make_scenario_maps.py
```
Outputs: `data/forecasts_step5d/`, `outputs/maps_step5d/`. Read the DIAGNOSTICS block that `verify_step5d.py` prints first.

## What is modelled

| Mechanism | How |
|---|---|
| Fertility | group TFR = national WPP TFR x relative multiplier (Pew global TFR ratio, damped by `phi` to a within-country gap); the gap is applied as a ratio, as a fixed number of children, or a blend (`w_add`, sampled) because gaps look closer to additive where fertility is low; gaps converge with time scale `Hf`; renormalised so the national aggregate TFR equals WPP |
| Age structure | stable-population-like pyramid at the WPP median age; group medians offset by Pew global median ages (damped by `psi`); one common shift per country so the national median matches WPP |
| Deaths | one model life table (group differences arise from age structure only) |
| Population totals | every country rescaled to WPP (to 2100) or the Step 5 rule (after) each step; the size of the rescale is reported |
| Migration - who leaves | WPP net migration sets how many leave each country (ages 15-44). Leavers carry that country's own adult religious mix, so emigrants from a Muslim-majority country are mostly Muslim. |
| Migration - who arrives | If `data/raw/migrant_bilateral.csv` is present, arrivals take the religious mix of their actual origin countries (weight `lam_od`, sampled 0.6-1.0, the rest from the pools). Without a table, the gravity matrix is used on its own (`lam_od` = 1, as in the Step 5E tests); blending it with the pools would bring back the continent bias. WPP sets how many arrive; the matrix sets who arrives. |
| Migration - ledger | `migration_by_religion.csv` records inflow and outflow by country and religion for 2020-2050 and 2020-2100 (headline scenario, mean over runs). Persons are counted before the rescale to WPP totals, so they are approximate to about 1-2%. |
| Switching (sensitivity only) | NET switching = Pew 2020 minus a no-switching 2010->2020 hindcast, capped at 10 pp/decade, decaying (30-120 yr half-life); zero for countries lacking a Pew 2010 baseline. Not in the headline. |

## Migration data (you supply it)
The bilateral table is what makes "which countries and religions are coming in" data-driven rather than pooled. I could not download it (the network is blocked here). Put a CSV at `religion_forecast_step1\religion_forecast_step1\data\raw\migrant_bilateral.csv` with these columns:

| column | meaning |
|---|---|
| `origin_iso3` | origin country, ISO3 (the same codes as WPP) |
| `dest_iso3` | destination country, ISO3 |
| `migrants` | number of migrants (stock or flow; only the shares matter) |

Suggested source: UN DESA, International Migrant Stock 2020 (bilateral, origin x destination, persons). The download is an Excel file that uses UN numeric country codes, so it must be converted to ISO3 first. Send me the file or its header and I'll write the converter. Without it, the model uses the neighbour/continent/world fallback, and `verify_step5d.py` says so.

The table gives origin composition, not religion. Religion still comes from each origin's Pew 2020 shares, so a migrant from Syria carries Syria's religious mix, not a Syrian-refugee-specific one. Pew's 2017 'Europe's Growing Muslim Population' and refugee-specific sources would refine that, but I can't access them from here.

## Optional: calibrate the fertility gap
`step5d_cohort_forecast.py --calibrate-phi` samples `phi` within +/-0.15 of the value that best reproduces Pew 2010->2020 (from the hindcast scan), instead of the 0.3-0.7 judgement range. It fits one decade, so it can overfit; the chosen range is stored in `step5d_report.json`. `hindcast_phi_scan.csv` is written on every run.

## Scenarios (equal run counts)
1. `demography_only` - **headline** (since Step 5E): fertility gaps, age structure and migration; no switching. Written to the standard `country_year_uncertainty.csv` / `global_share_uncertainty.csv` that Step 6 maps read.
2. `demography_plus_switching` - sensitivity only. Step 5E hindcasts show that extrapolating recent switching hurt the 1990-2010 decades (see README_STEP5E.md).
3. `equal_fertility_counterfactual` - fertility gaps off. Compare with 1 to see what fertility differences do.
4. `no_migration_counterfactual` - migration off. Compare with 1 to see what migration does.

All four scenarios are in the `*_by_scenario.csv` files. Counterfactuals are not forecasts.

## Honest limits
- Step 5E tested the mechanisms on 1950-2010 history. Within-country fertility gaps are barely identified (flat on the test decades), migration did not improve the hindcast, and momentum in switching hurt 1990-2010. See README_STEP5E.md.
- Migration counts come from WPP net migration, which does not balance across countries, so gross flows are not an exact accounting of the world's migrants.
- Religion of migrants is the origin's adult mix. It ignores that migrants may differ from stayers (e.g. more likely to be young or religiously unaffiliated); no migrant-religion data are used beyond that.
- Migrants keep origin-country fertility and age structure after arrival. Assimilation of fertility toward the destination is not modelled.
- `step5d_assumptions.json` numbers (Pew 2015 global TFR and median ages) were typed from memory of the report. **Verify them.**
- There are no country x religion fertility or age data. Global ratios damped by `phi`/`psi` are a judgement, not an estimate; ranges are in the JSON.
- Switching absorbs every error in the hindcast (births, deaths, migration, Pew definitions, rounding); it is not a measured conversion rate.
- Without a bilateral table, the migrant mix comes from the GRAVITY matrix (`migration_od.py`): distance, land borders and continent, balanced to WPP net migration. It is consistent with WPP totals but is a geographic prior. It uses NET flows, so big two-way corridors are understated (Mexico to USA gets about 9% of US arrivals, and Pakistan is the largest source). Its US result, about 8% Muslim by 2050, is implausibly high against Pew's 2017 projections (about 2%, from memory: please verify). Do not use destination-level religion results for the USA, Europe or the Gulf without a bilateral table.
- Gravity flows are averaged over 5 years, because single WPP years swing a lot.
- WPP net migration does not sum to zero across countries.
- Post-2100 national demography is the stylised Step 5 rule; 2200-3026 are mechanism explorations, not predictions.
- The hindcast table (`hindcast_diagnostics.csv`) compares demography-only 2020 with persistence. If demography does not beat persistence for a religion, trust that religion's projection less.
- Monte Carlo spread comes from parameter ranges and one persistent country x group draw per run, not from calibrated errors.

## Checks before trusting the headline (`demography_only`)
Run `verify_step5d.py` and read these in its output:
0. **Decomposition.** `unaffiliated_decomposition.csv` (and the DECOMPOSITION block) runs four single deterministic
   projections, switching off fertility gaps, then migration, then age offsets. If the unaffiliated share still falls
   with no fertility gaps and no migration, the cause is the starting age structure. Report that result: it means
   the headline decline is not a fertility assumption.
1. **Sensitivity table.** The correlation of each 2050 world share with each parameter, across the headline runs.
   If the unaffiliated share is driven by `psi`, that is an age-structure assumption, not evidence.
2. **Headline shares.** The unaffiliated share has fallen by more than 3 points in earlier runs of the headline. History
   shows the unaffiliated rising since 1990, so treat any large fall as a sign of a modelling problem until explained.
3. **Christianity.** The headline has no switching, so Christianity can rise. History shows it falling since 1990 through
   switching, which demography cannot reproduce.
4. **Migration matrix.** Without a bilateral table, check the destinations you care about. The USA result is not credible
   (see the limits above).
5. **Within-country gap.** The Pew 2010-2020 hindcast and the Step 5E history tests both show the gap is not identified.

## Reading the headline: what moves the world shares
A world share is an average of country shares, weighted by population. So a change in the world share has two parts:
- **within countries**: fertility gaps, age structure and migration change a group's share inside each country;
- **population weighting**: countries that hold more or fewer of a group's people grow or shrink relative to the world.

`verify_step5d.py` prints this split for every religion. From the run of commit 72fd808 (headline, 2020 to 2050):

| religion | 2020 -> 2050 | within countries | population weighting |
|---|---|---|---|
| Unaffiliated | 24.2% -> 18.0% (-6.2 pp) | -0.6 | -5.6 |
| Islam | 25.6% -> 31.2% (+5.6 pp) | +1.0 | +4.6 |
| Christianity | 28.8% -> 30.6% (+1.9 pp) | -0.2 | +2.1 |

- **The unaffiliated decline is almost all population weighting, and most of that is China.** In the 2020 start state China
  has 90% unaffiliated and holds 67% of the world's unaffiliated people. WPP projects China to fall 12% by 2050, so its
  weight drops and the world share falls with it. China alone accounts for -4.5 of the -5.6 pp.
- **Islam's rise is mostly population growth in Pakistan, Nigeria, Ethiopia, Afghanistan and Sudan** (+4.6 pp of weighting),
  not conversion or higher fertility inside countries (+1.0 pp).
- **The headline has no conversion.** Religion changes only through fertility gaps and migration, so the headline is
  what population growth does on its own. It is not a forecast of belief.

### Decision needed: which folk-religion classification
Pew and WRP divide religion into different categories, and the gap is large:

| | Pew 2010 | Pew 2020 | WRP 2010 |
|---|---|---|---|
| World unaffiliated | 22.0% | 24.2% | 11.5% |
| World folk religion | 1.4% | 1.4% | 11.4% |
| China unaffiliated | - | 89.6% | 32.5% |
| China folk religion | - | 3.0% | 46.3% |

The 1950-2010 history tests (Step 5E) use WRP's categories, while the forecast starts from Pew's. So the
unaffiliated findings from history do not carry over to the forecast as it stands.

- **Option A, Pew as published (current default).** The start state is Pew's 2020 data. The unaffiliated headline is
  24.2% in 2020 and 18.0% in 2050 under the no-conversion assumption, and it is driven by China.
- **Option B, WRP-consistent folk.** Where WRP measures more folk religion than Pew 2020, move the difference out of
  Pew's unaffiliated into folk, capped at the unaffiliated share. This affects 83 countries and 0.66 billion people,
  mostly China (43 points moved). It gives unaffiliated 15.8% and folk 9.7% in 2020. The 2050 population-weighting effect
  for the unaffiliated falls from -5.6 to -3.6 points, so the decline shrinks but does not disappear.
- Option B agrees with the history tests; Option A agrees with Pew's published 2020 figures.

To check the source yourself, open `pew_2010_2020.xlsx`, sheet "Unrounded counts", and find China for 2010 and 2020.
Compare `Religiously_unaffiliated` and `Other_religions` with `Population`.

