# Manuscript

`manuscript.md` is the working draft of the paper. Every number in it comes from the committed run
in `../results/`, and every figure is one of the SVG files in `../results/figures/`, which the code
regenerates (`python run.py all`). If the run changes, the numbers below change with it.

| Figure | File | Shows |
|---|---|---|
| 1 | `results/figures/world_projection_2100.svg` | world shares 2020-2100 with parameter and predictive intervals |
| 2 | `results/figures/validation_skill.svg` | history-test skill relative to persistence, country-level intervals |
| 3 | `results/figures/interval_calibration.svg` | coverage, interval score and error growth of the intervals |
| 4 | `results/figures/shift_share.svg` | change in world share within countries against population weighting |
| 5 | `results/figures/mechanism_ablation.svg` | what switching, fertility differences and migration contribute |
| 6 | `results/figures/prob_dominant_change_2100.svg` | predictive probability that a country's largest religion changes by 2100 |
| S1 | `results/figures/sensitivity.svg` | which parameters move the results |
| S2 | `results/figures/scenario_comparison.svg` | world shares in 2100 under every scenario |
| S3 | `results/figures/world_composition_long_run.svg` | exploratory horizons to 3026 |

| Number | Source file |
|---|---|
| history-test errors | `results/validation_summary.csv`, `results/validation_by_window.csv` |
| country-level differences from persistence | `results/inference.csv` |
| error model (b, beta) and its record | `results/forecast_error_model.json`, `results/forecast_error_record.csv` |
| interval coverage and scores | `results/predictive_calibration.csv`, `results/predictive_calibration_world.csv` |
| world shares and intervals | `results/global_share_by_scenario.csv` |
| shift-share | `results/world_share_shift_share.csv` |
| mechanism contributions | `results/ablation_effects.csv` |
| sensitivity | `results/sensitivity_coefficients.csv` |
| switching fit | `results/projection_report.json` (`switching_fit`), `results/switching_check_vs_pew.csv` |
| country changes | `results/dominant_change.csv` |

## Before submission

1. Re-run with the Pew 2010-2020 workbook prepared (`scripts/prepare_pew_panel.py`), so the start
   state is Pew's own data for both years and the 2010-2020 decade enters the tests. The committed
   run used the 2020-only fallback.
2. Verify every reference against the original, and the Pew 2010 median ages by religion in
   `config/assumptions.json` (`age_structure.pew_global_median_age_2010`, marked unverified).
3. Choose a licence, tag a release and archive it (Zenodo) for a DOI to cite in the data and code
   availability statement.
4. Check the target journal's policy on AI-assisted work and adapt the statement.
