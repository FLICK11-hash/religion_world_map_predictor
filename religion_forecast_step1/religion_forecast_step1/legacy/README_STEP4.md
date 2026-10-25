# Step 4 — Train and evaluate historical religion-share forecasts

This package is meant to be **extracted into the same folder** as `step3_engineer_features.py`, `verify_step3.py`, `.venv`, and `data/`.

## Windows PowerShell

```powershell
cd C:\Users\conra\religion_world_map_predictor\religion_forecast_step1\religion_forecast_step1

# After downloading religion_forecast_step4.zip to Downloads:
$zip = Get-ChildItem -Path "$env:USERPROFILE\Downloads", ([Environment]::GetFolderPath('Desktop')) -File -Recurse -Filter 'religion_forecast_step4.zip' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $zip) { throw 'Download religion_forecast_step4.zip first.' }
Expand-Archive -LiteralPath $zip.FullName -DestinationPath . -Force

.\.venv\Scripts\python.exe -m pip install -r requirements_step4.txt
.\.venv\Scripts\python.exe step4_train_validate.py
.\.venv\Scripts\python.exe verify_step4.py
Import-Csv .\data\models\model_comparison_by_horizon.csv | Format-Table -AutoSize
```

## Models

- **Persistence:** predicts the current eight shares at all future horizons.
- **Linear trend:** projects the last 5-year share change and projects the result onto the probability simplex.
- **LightGBM:** eight independent boosting regressors predict the change in *centered log-ratio* (CLR) space. The predicted CLR change is applied with a softmax to current religious shares.
- **Neural network:** a small scikit-learn `MLPRegressor` (48 and 24 hidden units) trained for up to 175 **epochs** predicts the same CLR change. Inputs receive fold-specific, training-only median imputation and standardization. `early_stopping=False` prevents random internal holdout validation.

Model selection is based on country-weighted **five-year** share MAE over seven forward-origin folds, not on dominant-label accuracy. Both 5-year and recursive 10-/20-/30-year comparisons are reported. Changed-label accuracy is shown with its actual denominator; values are blank if there were no true changes to evaluate.

## Files created under `data/models/`

- `one_step_fold_metrics.csv` — 7 origins × 4 models, share MAE and dominant-label accuracy.
- `one_step_predictions.csv` — each five-year validation prediction and truth.
- `multihorizon_fold_metrics.csv` — evaluation metrics for 5, 10, 20 and 30 years.
- `multihorizon_predictions.csv` — observed/predicted country shares at the various horizons.
- `model_comparison_by_horizon.csv` — country-weighted summary; indicates if each model beats persistence on share MAE.
- `lightgbm_all_wrp.joblib`, `neural_network_all_wrp.joblib`, `best_model.joblib` — fits on the full WRP historical training data. `best_model.joblib` also handles a winning baseline.
- `share_mae_by_horizon.png` and `dominant_accuracy_by_horizon.png` — plots of error/accuracy decay over 5, 10, 20, and 30 years.
- `step4_report.json` — numeric summaries and limitations.

## Scientific limitations

1. Models and validation are **WRP-only**; Pew is reserved as a separately calibrated 2020 forecast anchor. Never train on the apparent WRP→Pew discontinuity.
2. A valid one-step test predicts t+5 using t, t−5, t−10. In multihorizon tests, predicted religion shares are recursively fed back at each step; **actual** t+5, t+10, etc., are used only when scoring the requested endpoint.
3. All demography is held fixed at the origin over multihorizon simulations; this prevents using post-origin demographic observations but reduces realism. Step 5 will add UN future projection scenarios as separately stated assumptions.
4. The historical demographic covariates come from the **WPP 2024** reconstructed time series. Even though the religion response is time-split, the demographic data may incorporate later knowledge. Thus results are *retrospective backtests*, not fully vintage-realistic forecast evaluations.
5. Land borders use **current** Natural Earth polygons, a historical approximation. No fabricated historical boundaries are used.
6. Different source measurements and structural changes (e.g. Soviet Union dissolution) make it inappropriate to describe 2200–3026 forecasts as empirically validated.
7. Only 1,334 labeled transitions have uninterrupted t, t−5, t−10 context. Changed-dominant-country evaluations may have very small denominators. Model-selection comparisons are not unbiased estimates from a held-out final test set.
8. The compositional output uses an epsilon floor of `1e-5` for numerical log stability. This means modeled exact zeros may become tiny positives. Baselines preserve exact zeros unless linear projection changes them.

## Next

After reviewing `step4_report.json` and `model_comparison_by_horizon.csv`, proceed to Step 5 (Pew anchor, demographics/scenarios, and uncertainty ensembles), **not before**.
