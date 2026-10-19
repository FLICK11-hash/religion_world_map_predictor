# World Religion Forecast — Step 3: Features and Forward-Chaining Splits

## Before running

Complete Steps 1 and 2, including `step2_finalize_panels.py`.

Expected files (relative to your project script folder):

- `data/processed/wrp_training_only_8groups.csv`
- `data/processed/pew_anchor_only_8groups.csv`
- `data/raw/ne_50m_admin_0_countries.zip`

## Run (Windows PowerShell)

Put `step3_engineer_features.py` and `verify_step3.py` next to your Step 2 scripts:

```powershell
cd C:\Users\conra\religion_world_map_predictor\religion_forecast_step1\religion_forecast_step1
.\.venv\Scripts\python.exe step3_engineer_features.py
.\.venv\Scripts\python.exe verify_step3.py
Get-Content .\data\features\step3_report.json
```

Uses the pandas, geopandas, numpy, shapely, and pyogrio packages already installed in Step 1.

## Generated files

- `data/features/wrp_origin_features.csv`: WRP feature rows at year t using religion information from t, t-5 and t-10, plus demographic and spatial features available at t. Includes last WRP year for later recursive prediction.
- `data/features/wrp_training_transitions.csv`: above plus actual target shares at t+5, only if WRP has a matching row in t+5.
- `data/features/rolling_origin_one_step_splits.csv`: explicit rolling-origin train/validation row assignments using training labels `<=T` and validation origin `T` to target `T+5`.
- `data/features/multihorizon_evaluation_plan.csv`: evaluation plan for horizon lengths of 5, 10, 20 and 30 years, subject to real 2010 endpoint. **Does not contain future shares as features.** Recursive evaluation will occur in Step 4.
- `data/features/pew_2020_anchor_context.csv`: 2020 Pew estimates with 2010 Pew context; contains 10-year observed changes, **not made-up 2015 shares**.
- `data/features/feature_columns.json`: safe predictor names separated from target columns.
- `data/features/step3_report.json`: counts, fold diagnostics, warnings.

## Important methodological decisions

1. **No source mixing.** The WRP model trains on WRP five-year transitions. Pew is reserved for a modern 2010/2020 reference. Treat Pew 2020 as a forecast anchor, not five-year training data.
2. **Valid compositional target.** Eight shares sum to one; dominant religion is derived from the shares. We will predict all eight shares in Step 4.
3. **No observed future religion inputs.** `origin_year` t has religion features from t, t-5 and t-10; target `target_year` t+5 is kept apart. Border/continent peer averages are from year t only and exclude the target country.
4. **Border disclaimer.** Natural Earth modern geography is a proxy for historical adjacency, not an accurate 1945 border map. Countries that don't have a matching modern polygon keep spatial features missing, not fictitiously matched to successors.
5. **No imputation here.** Missing demographic and spatial values remain NaN. Fit any numerical imputer only on each training fold in Step 4.
6. **Vintage caveat.** The UN WPP 2024 historical series reflects later revisions. Backtesting with it is retrospective and must not be described as using strictly vintage-available population estimates.
7. **Longer horizons.** To fairly measure 10/20/30-year errors, Step 4 must recursively feed model-predicted shares and recomputed peer inputs back into the model. Reading actual intermediate-year shares would constitute leakage.
8. **Pew 2020 initialization.** Pew lacks an observed 2015 split. When forecasting from 2020, we need a separate documented way to initialize 5-year lags (scenario-based or trained model), rather than silently interpolating and labeling it observed.

## How to check

Run `verify_step3.py` to confirm that every sample's t-10, t-5, t, t+5 share values match the original WRP dataset and every chronological split respects the cutoff.

After reporting Step 3 results, do not train until the user and assistant have reviewed them.
