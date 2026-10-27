# Superseded pipelines

Everything here is kept for the record: it is the work the current model grew out of, and the
audit of its weaknesses (`docs/AUDIT_STATIC.md`) is what the current model was built to answer.
**None of it runs as part of the pipeline, and none of it is used by `religion_forecast/`.**

| Step | What it did | Why it is here |
|---|---|---|
| `step2_finalize_panels.py` | split the harmonised panel into source-pure training and anchor files for the machine-learning steps | only steps 3-4 consumed it |
| `step3_engineer_features.py` | lagged, peer and spatial features; rolling-origin split plans | the cohort model needs no feature matrix |
| `step4_train_validate.py` | LightGBM and a neural network on five-year share deltas | replaced by a mechanistic model; the residual learner that survives has weight 0 |
| `step4b_blend_validate.py` | leakage-aware blending of those models with persistence | only meaningful with step 4 |
| `step5_forecast_scenarios.py` | Monte Carlo on top of the LightGBM deltas | superseded twice over |
| `step5b_dynamic_scenarios.py` | mechanism-family stress tests | replaced by labelled scenarios with drawn parameters |
| `step5c_evidence_sensitivity.py` | momentum extrapolation and hypothetical tilts | replaced by the hierarchical switching model |
| `step5d_*` | the first cohort-component model (country × religion × age) | the direct ancestor of `religion_forecast/engine.py` |
| `step5e_wrp_hindcast.py` | the first history tests on WRP decades | replaced by `religion_forecast/backtest.py`, which does strictly more |
| `step6_make_maps.py` | choropleths | its drawing helpers now live in `religion_forecast/figures/mpl.py` |
| `make_step5_charts.py` | a self-contained HTML chart page for the step 5 results | replaced by `religion_forecast/figures/charts.py` |
| `migration_od.py` | gravity kernel and Sinkhorn balancing | replaced by `religion_forecast/migration.py` |
| `export_results.py` | exported `results_step5/` | replaced by `run.py report --export` |
| `verify_step*.py`, `test_step5*.py` | per-step checks and tests | each belongs to its step |

Two things in `results_step5/` are still live and must not be moved:

- `headline_country_shares.csv` is the fallback 2020 start state, used whenever
  `data/processed/pew_harmonized.csv` is absent;
- `global_share_uncertainty.csv` is the Step 5D comparison in the generated report.

The machine-learning steps need `lightgbm`, `scikit-learn`, `joblib` and `matplotlib`
(`requirements_step4.txt`). The current pipeline needs none of them.
