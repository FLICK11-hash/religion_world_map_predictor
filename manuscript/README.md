# Manuscript

`manuscript.md` is the working draft of the paper (revision 11, for Demographic Research), converted
from the version in the team's Google Drive folder; it omits the authors' email addresses. Every
number in it comes from the committed run in `../results/`, and every figure is a PNG in `figures/`
rendered from the SVG files in `../results/figures/`, which the code regenerates (`python run.py all`).
If the run changes, the numbers change with it.

Classification: arXiv `stat.AP` (Statistics: Applications); MSC 2020 62P25, 91D20, 62M20; JEL C53,
J11, Z12. Keywords: cohort-component projection, religious switching, international migration,
empirical Bayes, forecast evaluation, predictive intervals, interval score, shift-share
decomposition.

| Figure | File | Shows |
|---|---|---|
| 1 | `results/figures/validation_skill.svg` | history-test skill relative to persistence, country-level intervals |
| 2 | `results/figures/interval_calibration.svg` | coverage, interval score and error growth of the intervals |
| 3 | `results/figures/world_projection_2100.svg` | world shares 2020-2100 with parameter and predictive intervals |
| 4 | `results/figures/shift_share.svg` | change in world share within countries against population weighting |
| 5 | `results/figures/mechanism_ablation.svg` | what switching, fertility differences and migration contribute |
| 6 | `results/figures/prob_dominant_change_2100.svg` | predictive probability that a country's largest religion changes by 2100 |
| 7 | `results/figures/dominant_2100.svg` | largest religion by country in 2100 |
| A1-A4 | `results/figures/dominant_2050.svg`, `dominant_2200.svg`, `dominant_2500.svg`, `dominant_3026.svg` | largest religion in 2050 and the exploratory years |
| A5 | `results/figures/sensitivity.svg` | which parameters move the results |

| Number | Source file |
|---|---|
| history-test errors | `results/validation/validation_summary.csv`, `results/validation/validation_by_window.csv` |
| country-level differences from persistence | `results/validation/inference.csv` |
| error model (b, beta) and its record | `results/validation/forecast_error_model.json`, `results/validation/forecast_error_record.csv` |
| interval coverage and scores | `results/validation/predictive_calibration.csv`, `results/validation/predictive_calibration_world.csv` |
| world shares and intervals | `results/projection/global_share_by_scenario.csv` |
| shift-share | `results/projection/world_share_shift_share.csv` |
| mechanism contributions | `results/experiments/ablation_effects.csv` |
| sensitivity | `results/experiments/sensitivity_coefficients.csv` |
| switching fit | `results/projection/projection_report.json` (`switching_fit`), `results/projection/switching_check_vs_pew.csv` |
| estimator simulation study | `results/validation/estimator_recovery.csv`, `results/validation/estimator_recovery_runs.csv` |
| country changes | `results/projection/dominant_change.csv` |

## Before submission

Done: the committed run includes Pew's 2010-2020 decade (Global Religious Futures dataset, via
`scripts/prepare_pew_panel.py`) and the corrected Pew (2012) median ages by religion.

1. Decide what to do about the failed estimator check (9c: the country spread τ_u is estimated about
   10% too low, 65% coverage). The draft reports it; improving the estimator would need a new run.
2. Choose a licence, tag a release and archive it (Zenodo) for a DOI to cite in the data and code
   availability statement.
3. Check the target journal's policy on AI-assisted work and adapt the statement.
4. Decide whether to report a calibrated correction of the predictive intervals. They are a few
   points too narrow out of sample (more at 40 years); any correction estimated on the five decades
   would have to be validated on the same decades, so the draft reports the shortfall instead.
