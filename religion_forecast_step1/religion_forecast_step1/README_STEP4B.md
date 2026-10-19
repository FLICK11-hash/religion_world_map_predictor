# Step 4B — Test persistence + LightGBM blends

Runs in the same directory as `step4_train_validate.py`; requires its completed `data/models/one_step_predictions.csv`. No new libraries are needed beyond Step 4 requirements.

```powershell
.\.venv\Scripts\python.exe step4b_blend_validate.py
.\.venv\Scripts\python.exe verify_step4b.py
Import-Csv .\data\models\step4b\rolling_blend_summary.csv | Format-Table -AutoSize
Import-Csv .\data\models\step4b\rolling_blend_selections.csv | Format-Table -AutoSize
```

What it does:
- Constructs blends `(1 - alpha) * persistence + alpha * LightGBM`. `alpha` is in [0,1], so all religion shares still sum to 1.
- Adds a plurality-margin gated variant: changes are considered only when two religious groups are relatively close at the forecast origin.
- Evaluates fixed blends as **exploratory diagnostics**. It does **not** select the best on its own test data.
- Picks either overall-MAE or transition-weighted-MAE blending parameters from earlier fold outcomes only (the 1975 origin outcome in 1980 is first available for choosing at the 1980 forecast origin).
- Tests on forecast origins 1980 through 2005, with target years 1985 through 2010.
- Reports per-category share MAE, dominant religion accuracy, correct changes, false change alarms, wrong religion switches, and 95% country-cluster bootstrap intervals for share MAE differences against persistence.

Outputs in `data/models/step4b/`:
- `rolling_blend_predictions.csv`: held-out predictions and exact evaluation labels
- `rolling_blend_selections.csv`: each date's chosen blend and latest calibration target year
- `rolling_blend_summary.csv`: comparisons on the **same** 1980–2005 origin samples
- `fixed_blend_diagnostics_EXPLORATORY.csv`: fixed blending weights, NOT a final holdout score
- `fixed_blend_mae.png`, `rolling_blend_comparison.png`
- `step4b_report.json`: methods and caveats

**Important:** These one-step tests cannot establish which blend works out to 2100, much less 3026. Current WRP-reconstructed demographics are retrospective; Pew data is not used. Transition cases are uncommon, which makes conclusions on changing majorities uncertain. Any improvement is only within this evaluation design, and should be verified using an independent test where possible.
