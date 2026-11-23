# Results of one run

Small copies of one complete run, written by `python run.py report --export`, so the numbers can be checked without running anything. The full outputs stay in `data/`, which is git-ignored.

## Where to start

- `comparison_report.md`: the run report, every table in one page.
- `figures/index.html`: every map and chart (download the folder and open the page; hover over a country for its values).
- `run_stamp.json`: the commit the run was made at and whether the integrity checks passed; `integrity_checks.txt` is their output.

## Folders

| Folder | Contents | Start with |
|---|---|---|
| `validation/` | history tests, interval calibration, migration checks and the estimator study | `inference.csv`, `predictive_calibration.csv`, `estimator_recovery.csv` |
| `projection/` | the scenario projections to 3026, with predictive intervals to 2100 | `global_share_by_scenario.csv`, `country_target_years_reference_with_bands.csv`, `dominant_change.csv` |
| `experiments/` | mechanism ablations, global sensitivity and the migrant-sorting experiment | `ablation_effects.csv`, `sensitivity_coefficients.csv` |

Shares are fractions of the population (0.25 = 25%). Columns named `q05`/`q95` are the spread of the Monte Carlo runs (parameter uncertainty only); `pi05`/`pi95` are the 90% predictive intervals, which add the forecast errors the model made on 1970-2010 and are given to 2100. `docs/RESULTS.md` explains every table.

Files named `validation/benchmark_pew2026_*`, when present, compare the run with Pew's own 2026 projections (country shares in 2050 and world shares by decade). They are written after the run by `python scripts/benchmark_pew2026.py`, which needs Pew's Global Religious Futures dataset, and are removed when the run is re-exported.
