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
| Migration - who arrives | If `data/raw/migrant_bilateral.csv` is present, arrivals take the religious mix of their actual origin countries (weight `lam_od`, sampled 0.6-1.0). Destinations without bilateral data use land neighbours (`lam_nb`), the same continent (`lam`) and the world, weighted by origin outflows. WPP sets how many arrive; the bilateral table sets who arrives. |
| Migration - ledger | `migration_by_religion.csv` records inflow and outflow by country and religion for 2020-2050 and 2020-2100 (headline scenario, mean over runs). Persons are counted before the rescale to WPP totals, so they are approximate to about 1-2%. |
| Switching | NET switching = Pew 2020 minus a no-switching 2010->2020 hindcast, capped at 10 pp/decade, decaying (30-120 yr half-life); zero for countries lacking a Pew 2010 baseline |

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
1. `demography_only` - fertility, age, migration; no switching.
2. `demography_plus_switching` - **headline**; written to the standard `country_year_uncertainty.csv` / `global_share_uncertainty.csv` that Step 6 maps read.
3. `equal_fertility_counterfactual` - fertility gaps off. Compare with 1 to see what fertility differences do.
4. `no_migration_counterfactual` - migration off. Compare with 1 to see what migration does.

All four scenarios are in the `*_by_scenario.csv` files. Counterfactuals are not forecasts.

## Honest limits
- Migration counts come from WPP net migration, which does not balance across countries, so gross flows are not an exact accounting of the world's migrants.
- Religion of migrants is the origin's adult mix. It ignores that migrants may differ from stayers (e.g. more likely to be young or religiously unaffiliated); no migrant-religion data are used beyond that.
- Migrants keep origin-country fertility and age structure after arrival. Assimilation of fertility toward the destination is not modelled.
- `step5d_assumptions.json` numbers (Pew 2015 global TFR and median ages) were typed from memory of the report. **Verify them.**
- There are no country x religion fertility or age data. Global ratios damped by `phi`/`psi` are a judgement, not an estimate; ranges are in the JSON.
- Switching absorbs every error in the hindcast (births, deaths, migration, Pew definitions, rounding); it is not a measured conversion rate.
- Migrant religion mix uses pooled WPP outflows, not origin-destination data; WPP net migration does not sum to zero across countries.
- Post-2100 national demography is the stylised Step 5 rule; 2200-3026 are mechanism explorations, not predictions.
- The hindcast table (`hindcast_diagnostics.csv`) compares demography-only 2020 with persistence. If demography does not beat persistence for a religion, trust that religion's projection less.
- Monte Carlo spread comes from parameter ranges and one persistent country x group draw per run, not from calibrated errors.
