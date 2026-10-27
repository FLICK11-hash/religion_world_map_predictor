# Archived experiments

The project's earlier generations, kept as a record of what was tried and what it showed. The
current package grew out of them, and the audit of their weaknesses (`docs/AUDIT_STATIC.md`) is
what it was built to answer. None of this runs as part of `run.py all`, and `religion_forecast/`
imports none of it.

## Two earlier generations

**Generation 1, Steps 1 to 6: machine learning on share changes.** A country-year panel from WRP
and Pew, lagged and spatial features, and LightGBM and a neural network trained to predict
five-year changes in each religion's share, blended with persistence and run forward as a Monte
Carlo. It treated religious change as a statistical pattern to be learned.

**Generation 2, Steps 5D and 5E: the first cohort-component model.** Country × religion × age,
moved forward by births and deaths, with the first history tests on WRP decades. It treated
religious change as the outcome of demographic mechanisms. `religion_forecast/` is its direct
descendant: `step5d_engine.py` became `engine.py`, and `step5e_wrp_hindcast.py` became
`backtest.py`, which does strictly more.

The move from the first to the second is the project's central methodological decision, and the
reason is in the record: a learned model of share changes has nothing to say about the mechanisms
behind them, and those mechanisms are what the questions are about.

## What each experiment tested

| Step | What it tested | Its own record |
|---|---|---|
| `scripts/prepare_raw_data.py` (was `step1_download_inspect.py`) | download and inspect the raw sources | `README_STEP1.md` |
| `scripts/prepare_pew_panel.py` (was `step2_clean_merge.py`) | harmonise WRP and Pew into one country-year panel | still live: builds the preferred start state |
| `step2_finalize_panels.py` | split that panel into source-pure training and anchor files | `README_STEP3.md` |
| `step3_engineer_features.py` | lagged, peer and spatial features; rolling-origin splits | `README_STEP3.md` |
| `step4_train_validate.py` | LightGBM and a neural network on five-year share deltas, against persistence and a linear trend, over seven forward origins | `README_STEP4.md` |
| `step4b_blend_validate.py` | blends of persistence and LightGBM, with blend weights chosen from earlier folds only and 95% country-cluster bootstrap intervals against persistence | `README_STEP4B.md` |
| `step5_forecast_scenarios.py` | Monte Carlo built on the LightGBM deltas | `README_STEP5.md` |
| `step5b_dynamic_scenarios.py` | stress tests by mechanism family | `README_STEP5B.md` |
| `step5c_evidence_sensitivity.py` | separating observed 2010-2020 movement from hypothetical tilts | `README_STEP5C.md` |
| `step5d_*` | the first cohort-component model | `README_STEP5D.md` |
| `step5e_wrp_hindcast.py` | the first history tests: settings chosen on training decades, scored on test decades | `README_STEP5E.md` |
| `step6_make_maps.py`, `make_step5_charts.py` | maps and a chart page | — |
| `migration_od.py` | gravity kernel and Sinkhorn balancing, now `religion_forecast/migration.py` | — |
| `export_results.py` | wrote `results_step5/` | — |
| `verify_step*.py` | each step's own check of its outputs, run after the step | — |

Step 4B's design deserves a note because it is better than its later neighbour. It chose blend
weights from earlier folds only, and its own README warns that "any improvement is only within
this evaluation design". The trend baseline in `baselines/` did not take the same care, and its
headline result turned out to be leakage (`docs/COMPARABILITY.md`).

Step 5E's own record reports the result that carried forward into the current model: demography
"helps a little", beating persistence on the 1990 and 2000 test decades and doing worse on
1960-1980. The current backtests reach the same conclusion with more windows.

## What still runs

The four Step 5D and 5E test suites run from the repository root and pass:

```bash
python legacy/test_step5d_engine.py
python legacy/test_step5d_diagnostics.py
python legacy/test_step5d_simulate.py
python legacy/test_step5e.py
```

Two small repairs made that possible, both to damage done by moving these files rather than to
the experiments themselves:

- Four scripts import `wrp_history`, which was renamed to `religion_forecast/sources.py` without
  a byte changing. `wrp_history.py` here is a three-line shim that re-exports it.
- `test_step5d_simulate.py` read a sibling script by a path relative to the working directory, and
  now reads it relative to its own file.

The Generation 1 machine-learning steps need `lightgbm`, `scikit-learn`, `joblib` and `scipy`
(`pip install -e '.[legacy]'`, which replaces the old `requirements_step4.txt`) and a `data/processed/` panel built from the Pew workbook. Neither
was available where the current repository was verified, so **they have not been re-run and are
not claimed to work.** Their original layout, with the scripts beside `data/` as they expect, is
preserved at the tag `archive/pre-merge-main`, the tip of the former `main` history.

## Paths in these READMEs

The per-step READMEs describe how each script was run at the time, from a project folder that was
then two directories deep, often in Windows paths such as
`C:\Users\conra\religion_world_map_predictor\religion_forecast_step1\religion_forecast_step1`.
They are left as written, as a record. They are not instructions for the current layout.

## Still live: `results_step5/`

`results_step5/`, at the repository root, holds the exported results of Step 5D. Two files in it
are read by the current package, which is why it is not in this folder:

- `headline_country_shares.csv` is the 2020 start state whenever
  `data/processed/pew_harmonized.csv` is absent. Every committed result in `results/` used it.
- `global_share_uncertainty.csv` is the Step 5D comparison in the generated report.
