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
| Fertility | group TFR = national WPP TFR x relative multiplier (Pew global TFR ratio, damped by `phi` to a within-country gap); gaps converge with half-life-like `Hf`; renormalised so the national aggregate TFR equals WPP |
| Age structure | stable-population-like pyramid at the WPP median age; group medians offset by Pew global median ages (damped by `psi`); one common shift per country so the national median matches WPP |
| Deaths | one model life table (group differences arise from age structure only) |
| Population totals | every country rescaled to WPP (to 2100) or the Step 5 rule (after) each step; the size of the rescale is reported |
| Migration | WPP net migrants; arrivals take the religious mix of an emigrant pool (global, blended with same-continent) built from WPP net outflows, not an unweighted continental mean |
| Switching | NET switching = Pew 2020 minus a no-switching 2010->2020 hindcast, capped at 10 pp/decade, decaying (30-120 yr half-life); zero for countries lacking a Pew 2010 baseline |

## Scenarios (equal run counts)
1. `demography_only` - fertility, age, migration; no switching.
2. `demography_plus_switching` - **headline**; written to the standard `country_year_uncertainty.csv` / `global_share_uncertainty.csv` that Step 6 maps read.
3. `equal_fertility_counterfactual` - fertility gaps off. Compare with 1 to see what fertility differences do.
4. `no_migration_counterfactual` - migration off. Compare with 1 to see what migration does.

All four scenarios are in the `*_by_scenario.csv` files. Counterfactuals are not forecasts.

## Honest limits
- `step5d_assumptions.json` numbers (Pew 2015 global TFR and median ages) were typed from memory of the report. **Verify them.**
- There are no country x religion fertility or age data. Global ratios damped by `phi`/`psi` are a judgement, not an estimate; ranges are in the JSON.
- Switching absorbs every error in the hindcast (births, deaths, migration, Pew definitions, rounding); it is not a measured conversion rate.
- Migrant religion mix uses pooled WPP outflows, not origin-destination data; WPP net migration does not sum to zero across countries.
- Post-2100 national demography is the stylised Step 5 rule; 2200-3026 are mechanism explorations, not predictions.
- The hindcast table (`hindcast_diagnostics.csv`) compares demography-only 2020 with persistence. If demography does not beat persistence for a religion, trust that religion's projection less.
- Monte Carlo spread comes from parameter ranges and one persistent country x group draw per run, not from calibrated errors.
