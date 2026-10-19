# Step 5 — World Religion Forecast Scenario Ensemble

## What this does

Run exploratory *five-year* simulations from the **Pew 2020** religion-share anchor through 3030, returning a separately interpolated **3026**. Outputs include all five-year dates and detailed country/global summaries for 2050, 2100, 2200, 2500, and 3026.

Simulates **120 runs by default**: 30 each in four combinations of:

1. **Post-2100 fertility:** national total fertility rates converge toward 2.1 births/woman, versus retaining 2100 differences.
2. **Religious disaffiliation:** a small, explicitly assumed transition toward the unaffiliated continues after 2100, versus a rate that plateaus after 2100.

The scenario ensembles vary the disaffiliation parameter, fertility shift, small LightGBM blending weight, and scale of resampled historical out-of-fold residuals. Scenario weights are **assumed equal** and are **not estimates of their real-world probabilities**. Bands are **scenario sensitivity intervals**, NOT calibrated predictive confidence intervals.

## Setup and run (Windows PowerShell)

1. Download this package into `Downloads`.
2. In your **existing project folder**, containing `step3_engineer_features.py`, `step4_train_validate.py`, and `data/`:

```powershell
cd C:\Users\conra\religion_world_map_predictor\religion_forecast_step1\religion_forecast_step1

Expand-Archive "$env:USERPROFILE\Downloads\religion_forecast_step5.zip" -DestinationPath . -Force

.\.venv\Scripts\python.exe step5_forecast_scenarios.py --runs 120 --seed 42

.\.venv\Scripts\python.exe verify_step5.py

Get-Content .\data\forecasts\step5_report.json | Select-Object -First 45

Import-Csv .\data\forecasts\pew_2050_sanity_check.csv |
  Format-Table religion,scenario_ensemble_2050_pct,pew_2015_projection_2050_pct,difference_pct_points -AutoSize
```

All dependencies were installed in Step 4 (`numpy`, `pandas`, `scipy`, `scikit-learn`, `geopandas`, `joblib`, `lightgbm`). No new installation should be needed.

## Expected inputs

- `data/features/pew_2020_anchor_context.csv`
- `data/processed/wpp_country_year.csv`
- `data/models/lightgbm_all_wrp.joblib`
- `data/models/one_step_predictions.csv` (out-of-fold WRP residuals)
- `data/raw/ne_50m_admin_0_countries.zip`
- Step 3/Step 4 scripts in same folder

The first five-year lag uses a *synthetic 2015 midpoint* between Pew 2010 and 2020 (not a survey or observed value). Countries without Pew 2010 use constant synthetic 2010/2015 values. This initialization is labeled in the JSON report.

## Outputs

All are saved under `data/forecasts/`:

- `ensemble_shares_float32.npy` — run x year x country x religion array (can exceed 100 MB)
- `ensemble_populations_float32.npy` — scenario populations for population-weighted global totals
- `country_year_uncertainty.csv` — mean and 5th/50th/95th share percentiles, plus modal dominant group and fraction of runs in agreement, for **every 5-year date and 3026**
- `global_share_by_run.csv` — population-weighted worldwide religion shares for every run/year
- `global_share_uncertainty.csv` — share distributions by religion and year
- `scenario_parameters.csv` — audit trail of four scenarios and sampled parameters
- `deterministic_tracks.csv` — untouched-share persistence benchmark and recursive LightGBM trajectory
- `pew_2050_sanity_check.csv` — comparison with Pew's **2015** published 2050 shares
- `step5_report.json` — coverage, input assumptions, and limitations

The scenario arrays can be large. **Keep `data/forecasts/` out of Git**. Add `data/forecasts/` to `.gitignore` if needed, and commit only source code, README, and small reports.

## Scientific cautions

- Country total fertility rate **does not describe religious-group fertility**. Therefore the model does *not* invent religion-specific fertility rates or religious conversion probabilities.
- UN WPP projections end at 2100 in this workflow. **Population/age/fertility beyond 2100 are scenario extrapolations, not UN forecasts.** A stylized population-growth rule lets 2100 growth fade over time. Do not interpret it as a demographic prediction.
- LightGBM did not beat simple persistence in 5–30-year historical share backtests. In Monte Carlo simulations its contribution is small, decreasing after 2100 and disappearing at 2200. The deterministic full-LightGBM track is illustrative and has no long-term validation.
- Pew's 2010 and 2020 religion definitions and WRP 1945–2010 definitions are not identical. Folk/Traditional is proxy-derived from WRP for many Pew 2020 records.
- Today's countries and geographic borders are held fixed for the simulated horizon; future splits/mergers are not predicted.
- Even 2050 is not validated against an *observed* future; it is just compared against Pew's older 2015 projection from a different starting vintage. Pew's 2050 projection shares used here are published rounding values, which sum to 100.1%.
- After 2100, especially by 2200–3026, conclusions reflect assumptions much more than observed evidence. Do not cite ensemble agreement as an objectively calibrated probability.

## Sources

Pew (2015) *The Future of World Religions: Population Growth Projections, 2010–2050*: https://www.pewresearch.org/religion/2015/04/02/population-projections-by-religious-group/

UN Population Division, *World Population Prospects, 2024 Revision*: https://population.un.org/wpp/

World Religion Project (WRP v1.1): https://correlatesofwar.org/data-sets/world-religion-data/

Natural Earth: https://www.naturalearthdata.com/about/terms-of-use/
