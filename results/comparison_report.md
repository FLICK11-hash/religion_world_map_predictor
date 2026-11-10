# Run report

Generated 2026-11-10 22:37 UTC from `data/validation/`, `data/projections/` and `data/experiments/`. Shares are in percent; differences in percentage points (pp).

## 1. Inputs

| input | status | detail |
|---|---|---|
| wpp_indicators | used | 237 countries, 1950-2100 |
| start_state | fallback | committed Pew 2020 start state (201 countries); Pew 2010 unavailable |
| wrp | used | 1730 usable country-years of 1995 |
| natural_earth | used | 242 map units |
| wpp_age | used | 200 of 200 countries, 1950-2100 (5-year points) |
| bilateral_stock | used | undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx: 68941 country pairs x years, years [np.int64(1990), np.int64(1995), np.int64(2000), np.int64(2005), np.int64(2010), np.int64(2015), np.int64(2020), np.int64(2024)] (cached parse) |
| migrant_religion | missing | no country-level Pew migrant file; religion of migrants from the affinity model calibrated to Pew published aggregates (inputs/migrant_religion_published.csv) |
| switching_survey | used | 67 verified cells, 33 countries |
| religion_fertility | used | 8 world, 5 regional (2 regions), 10 country figures (4 countries); 7 rows held back |
| unhcr | used | 64809 rows 2010-2022 |
| pew_2015_projection | used | 5 years, 234 countries |

Start state: inputs/pew2020_start_state.csv (Pew 2020; no 2010, so no Pew 2010-2020 test window). Runs per scenario: 40, seed 2026, reference scenario `stabilising`.

## 2. History tests

Ten-year forecasts of every test decade, fitted only on earlier decades. Population-weighted total-variation (TV) error of country shares, in pp; the change is against persistence.

| scope | model | windows | popw_tv_pp | change_vs_persistence_pp | change_vs_persistence_percent | dominant_accuracy | changed_true | changed_hit | false_alarm |
|---|---|---|---|---|---|---|---|---|---|
| WRP 1970-2010 | persistence | 4 | 4.406 | 0.000 | 0.000 | 0.961 | 21 | 0 | 0 |
| WRP 1970-2010 | trend | 4 | 5.974 | 1.568 | 35.578 | 0.959 | 21 | 6 | 8 |
| WRP 1970-2010 | trend_residual | 4 | 5.853 | 1.446 | 32.827 | 0.963 | 21 | 6 | 6 |
| WRP 1970-2010 | demography | 4 | 4.377 | -0.029 | -0.666 | 0.963 | 21 | 2 | 1 |
| WRP 1970-2010 | demography_migration | 4 | 4.371 | -0.036 | -0.813 | 0.961 | 21 | 2 | 2 |
| WRP 1970-2010 | switching_0.5 | 4 | 4.680 | 0.274 | 6.218 | 0.961 | 21 | 2 | 2 |
| WRP 1970-2010 | switching_1 | 4 | 5.156 | 0.749 | 17.009 | 0.958 | 21 | 3 | 5 |
| WRP 1970-2010 | switching_selected | 4 | 4.592 | 0.185 | 4.209 | 0.963 | 21 | 3 | 2 |
| WRP 1990-2010 | persistence | 2 | 4.623 | 0.000 | 0.000 | 0.969 | 9 | 0 | 0 |
| WRP 1990-2010 | trend | 2 | 7.054 | 2.431 | 52.574 | 0.953 | 9 | 0 | 5 |
| WRP 1990-2010 | trend_residual | 2 | 6.834 | 2.211 | 47.818 | 0.956 | 9 | 0 | 4 |
| WRP 1990-2010 | demography | 2 | 4.572 | -0.052 | -1.120 | 0.972 | 9 | 1 | 0 |
| WRP 1990-2010 | demography_migration | 2 | 4.562 | -0.061 | -1.329 | 0.969 | 9 | 1 | 1 |
| WRP 1990-2010 | switching_0.5 | 2 | 4.787 | 0.164 | 3.542 | 0.969 | 9 | 1 | 1 |
| WRP 1990-2010 | switching_1 | 2 | 5.087 | 0.464 | 10.033 | 0.962 | 9 | 1 | 3 |
| WRP 1990-2010 | switching_selected | 2 | 4.562 | -0.061 | -1.329 | 0.969 | 9 | 1 | 1 |

### Country-level comparison with persistence

Population-weighted mean difference in TV error over every country-decade (negative = better), with a 95% interval from a bootstrap over countries, and the exact decade-level sign-flip test.

| scope | model | country_windows | mean_difference_pp | ci95_low_pp | ci95_high_pp | p_bootstrap | share_better | windows_better | windows | p_window |
|---|---|---|---|---|---|---|---|---|---|---|
| WRP 1970-2010 | trend | 558 | 1.859 | 1.214 | 2.408 | 0.000 | 0.342 | 0 | 4 | 0.125 |
| WRP 1970-2010 | trend_residual | 558 | 1.711 | 1.046 | 2.256 | 0.000 | 0.366 | 0 | 4 | 0.125 |
| WRP 1970-2010 | demography | 558 | -0.026 | -0.102 | 0.056 | 0.639 | 0.457 | 2 | 4 | 0.750 |
| WRP 1970-2010 | demography_migration | 558 | -0.033 | -0.090 | 0.039 | 0.421 | 0.500 | 2 | 4 | 0.750 |
| WRP 1970-2010 | switching_0.5 | 558 | 0.276 | -0.176 | 0.719 | 0.670 | 0.588 | 1 | 4 | 0.500 |
| WRP 1970-2010 | switching_1 | 558 | 0.722 | -0.187 | 1.701 | 0.463 | 0.575 | 1 | 4 | 0.375 |
| WRP 1970-2010 | switching_selected | 558 | 0.169 | -0.103 | 0.448 | 0.676 | 0.527 | 2 | 4 | 0.875 |

## 3. Forecast errors and predictive intervals

Error model e = (h/10)^beta (s(1-s) + eps)^b u, fitted on the history record: b = 0.804, beta = 0.274. Mean |standardised error| by horizon: 10 years 0.316, 20 years 0.369, 30 years 0.442, 40 years 0.465. Resampling blocks: WRP 1970-1980, WRP 1980-1990, WRP 1990-2000, WRP 2000-2010.

Out-of-sample coverage of country x religion shares and interval score (lower is better). Main scheme "non-overlapping": the error model is refitted, for each forecast, on history entries that share no calendar years with it; "real-time" uses only entries that ended by the forecast origin; the overlapping leave-one-origin-out design is shown for comparison. Coverage over all cells, over cells observed above zero, and by forecast share.

| scheme | method | horizon | nominal | coverage | coverage_popw | interval_score_pp | median_width_pp | coverage_above_zero | coverage_share_5_20 | coverage_share_20_plus | interval_score_above_zero_pp |
|---|---|---|---|---|---|---|---|---|---|---|---|
| leave-one-origin-out (overlapping) | error-calibrated | 10 | 0.800 | 0.813 | 0.860 | 7.298 | 1.061 | 0.779 | 0.774 | 0.806 | 9.706 |
| leave-one-origin-out (overlapping) | error-calibrated | 10 | 0.900 | 0.897 | 0.928 | 10.265 | 1.863 | 0.876 | 0.868 | 0.883 | 13.615 |
| leave-one-origin-out (overlapping) | error-calibrated | 20 | 0.800 | 0.821 | 0.859 | 10.038 | 1.436 | 0.790 | 0.766 | 0.758 | 13.193 |
| leave-one-origin-out (overlapping) | error-calibrated | 20 | 0.900 | 0.907 | 0.921 | 13.354 | 2.761 | 0.888 | 0.860 | 0.869 | 17.506 |
| leave-one-origin-out (overlapping) | error-calibrated | 30 | 0.800 | 0.810 | 0.802 | 13.038 | 1.920 | 0.782 | 0.786 | 0.706 | 17.255 |
| leave-one-origin-out (overlapping) | error-calibrated | 30 | 0.900 | 0.901 | 0.921 | 17.420 | 3.550 | 0.877 | 0.885 | 0.840 | 22.978 |
| leave-one-origin-out (overlapping) | error-calibrated | 40 | 0.800 | 0.808 | 0.769 | 15.178 | 2.282 | 0.770 | 0.800 | 0.606 | 20.302 |
| leave-one-origin-out (overlapping) | error-calibrated | 40 | 0.900 | 0.905 | 0.926 | 19.034 | 4.009 | 0.881 | 0.904 | 0.812 | 25.390 |
| non-overlapping | error-calibrated | 10 | 0.800 | 0.813 | 0.860 | 7.298 | 1.061 | 0.779 | 0.774 | 0.806 | 9.706 |
| non-overlapping | error-calibrated | 10 | 0.900 | 0.897 | 0.928 | 10.265 | 1.863 | 0.876 | 0.868 | 0.883 | 13.615 |
| non-overlapping | error-calibrated | 20 | 0.800 | 0.778 | 0.845 | 10.711 | 1.368 | 0.744 | 0.738 | 0.711 | 14.071 |
| non-overlapping | error-calibrated | 20 | 0.900 | 0.876 | 0.905 | 14.723 | 2.623 | 0.856 | 0.833 | 0.838 | 19.238 |
| non-overlapping | error-calibrated | 30 | 0.800 | 0.813 | 0.781 | 14.329 | 2.029 | 0.772 | 0.779 | 0.741 | 18.889 |
| non-overlapping | error-calibrated | 30 | 0.900 | 0.901 | 0.899 | 20.627 | 3.949 | 0.876 | 0.891 | 0.890 | 26.925 |
| non-overlapping | error-calibrated, central path | 10 | 0.800 | 0.779 | 0.851 | 7.383 | 0.986 | 0.751 | 0.763 | 0.791 | 9.817 |
| non-overlapping | error-calibrated, central path | 10 | 0.900 | 0.874 | 0.921 | 10.365 | 1.759 | 0.855 | 0.851 | 0.879 | 13.745 |
| non-overlapping | error-calibrated, central path | 20 | 0.800 | 0.719 | 0.787 | 11.034 | 1.209 | 0.692 | 0.691 | 0.676 | 14.495 |
| non-overlapping | error-calibrated, central path | 20 | 0.900 | 0.840 | 0.892 | 15.166 | 2.429 | 0.821 | 0.810 | 0.804 | 19.813 |
| non-overlapping | error-calibrated, central path | 30 | 0.800 | 0.772 | 0.757 | 14.595 | 1.771 | 0.727 | 0.769 | 0.717 | 19.265 |
| non-overlapping | error-calibrated, central path | 30 | 0.900 | 0.893 | 0.895 | 20.948 | 3.925 | 0.869 | 0.897 | 0.896 | 27.338 |
| non-overlapping | error-calibrated, centred | 10 | 0.800 | 0.811 | 0.848 | 7.335 | 0.949 | 0.786 | 0.802 | 0.818 | 9.767 |
| non-overlapping | error-calibrated, centred | 10 | 0.900 | 0.904 | 0.925 | 10.183 | 1.800 | 0.890 | 0.918 | 0.912 | 13.511 |
| non-overlapping | error-calibrated, centred | 20 | 0.800 | 0.754 | 0.802 | 10.827 | 1.210 | 0.738 | 0.758 | 0.737 | 14.257 |
| non-overlapping | error-calibrated, centred | 20 | 0.900 | 0.873 | 0.905 | 14.616 | 2.479 | 0.864 | 0.851 | 0.860 | 19.128 |
| non-overlapping | error-calibrated, centred | 30 | 0.800 | 0.750 | 0.751 | 15.575 | 1.598 | 0.731 | 0.805 | 0.718 | 20.616 |
| non-overlapping | error-calibrated, centred | 30 | 0.900 | 0.867 | 0.869 | 21.913 | 3.744 | 0.852 | 0.901 | 0.875 | 28.719 |
| non-overlapping | model draws (parameter uncertainty) | 10 | 0.800 | 0.144 | 0.142 | 11.745 | 0.089 | 0.194 | 0.165 | 0.193 | 15.550 |
| non-overlapping | model draws (parameter uncertainty) | 10 | 0.900 | 0.175 | 0.160 | 22.037 | 0.115 | 0.234 | 0.199 | 0.230 | 29.179 |
| non-overlapping | model draws (parameter uncertainty) | 20 | 0.800 | 0.153 | 0.141 | 18.375 | 0.176 | 0.202 | 0.180 | 0.183 | 23.991 |
| non-overlapping | model draws (parameter uncertainty) | 20 | 0.900 | 0.188 | 0.167 | 33.807 | 0.234 | 0.249 | 0.218 | 0.233 | 44.135 |
| non-overlapping | model draws (parameter uncertainty) | 30 | 0.800 | 0.154 | 0.128 | 24.057 | 0.268 | 0.207 | 0.189 | 0.172 | 31.533 |
| non-overlapping | model draws (parameter uncertainty) | 30 | 0.900 | 0.187 | 0.158 | 43.687 | 0.350 | 0.251 | 0.218 | 0.214 | 57.241 |
| real-time | error-calibrated | 10 | 0.800 | 0.794 | 0.830 | 7.989 | 1.171 | 0.753 | 0.707 | 0.746 | 10.604 |
| real-time | error-calibrated | 10 | 0.900 | 0.889 | 0.933 | 11.600 | 2.121 | 0.866 | 0.838 | 0.864 | 15.324 |
| real-time | error-calibrated | 20 | 0.800 | 0.769 | 0.818 | 12.040 | 1.651 | 0.726 | 0.669 | 0.659 | 15.976 |
| real-time | error-calibrated | 20 | 0.900 | 0.872 | 0.901 | 16.637 | 3.142 | 0.847 | 0.796 | 0.801 | 21.899 |
| real-time | error-calibrated | 30 | 0.800 | 0.826 | 0.804 | 14.855 | 2.543 | 0.790 | 0.753 | 0.707 | 19.662 |
| real-time | error-calibrated | 30 | 0.900 | 0.909 | 0.902 | 21.594 | 4.481 | 0.889 | 0.867 | 0.851 | 28.258 |

World shares of the observed countries (8 religions per held-out origin and horizon): share inside the interval, by nominal level.

| scheme | method | horizon | 0.5 | 0.8 | 0.9 | 0.95 |
|---|---|---|---|---|---|---|
| leave-one-origin-out (overlapping) | error-calibrated | 10 | 0.47 | 0.81 | 0.88 | 0.94 |
| leave-one-origin-out (overlapping) | error-calibrated | 20 | 0.46 | 0.75 | 0.88 | 1.00 |
| leave-one-origin-out (overlapping) | error-calibrated | 30 | 0.31 | 0.62 | 0.94 | 1.00 |
| leave-one-origin-out (overlapping) | error-calibrated | 40 | 0.25 | 0.62 | 1.00 | 1.00 |
| non-overlapping | error-calibrated | 10 | 0.47 | 0.81 | 0.88 | 0.94 |
| non-overlapping | error-calibrated | 20 | 0.42 | 0.75 | 0.88 | 0.96 |
| non-overlapping | error-calibrated | 30 | 0.38 | 0.44 | 0.75 | 0.88 |
| non-overlapping | error-calibrated, central path | 10 | 0.47 | 0.81 | 0.88 | 0.94 |
| non-overlapping | error-calibrated, central path | 20 | 0.33 | 0.75 | 0.88 | 0.96 |
| non-overlapping | error-calibrated, central path | 30 | 0.38 | 0.44 | 0.75 | 0.88 |
| non-overlapping | error-calibrated, centred | 10 | 0.50 | 0.88 | 0.94 | 0.94 |
| non-overlapping | error-calibrated, centred | 20 | 0.25 | 0.71 | 0.79 | 1.00 |
| non-overlapping | error-calibrated, centred | 30 | 0.31 | 0.56 | 0.81 | 0.88 |
| non-overlapping | model draws (parameter uncertainty) | 10 | 0.09 | 0.16 | 0.22 | 0.25 |
| non-overlapping | model draws (parameter uncertainty) | 20 | 0.08 | 0.08 | 0.12 | 0.12 |
| non-overlapping | model draws (parameter uncertainty) | 30 | 0.06 | 0.06 | 0.12 | 0.19 |
| real-time | error-calibrated | 10 | 0.38 | 0.71 | 0.83 | 0.96 |
| real-time | error-calibrated | 20 | 0.31 | 0.56 | 0.69 | 0.88 |
| real-time | error-calibrated | 30 | 0.25 | 0.25 | 0.62 | 0.75 |

## 4. Religious switching

Empirical Bayes fit, mean of 3 replicate fits: delta = -0.062, beta_d = 1.269, tau_u = 1.458; replicate standard deviations delta 0.026, beta_d 0.009, tau_u 0.024. Median posterior effective sample size 314 of 512 draws. Hyperparameter uncertainty: laplace.

| delta | beta_d | tau_u | se_delta | se_beta_d | se_log_tau_u | log_marginal | min_posterior_ess |
|---|---|---|---|---|---|---|---|
| -0.046 | 1.267 | 1.431 | 0.174 | 0.095 | 0.109 | 5700.259 | 163.808 |
| -0.048 | 1.279 | 1.475 | 0.179 | 0.109 | 0.114 | 5699.367 | 79.021 |
| -0.091 | 1.260 | 1.469 | 0.191 | 0.099 | 0.121 | 5699.696 | 105.046 |

Parametric simulation study of the estimator under the real design (run.py recovery): evidence simulated from the fitted hyperparameters, refitted; bias, RMSE, the mean Laplace standard error against the spread of the estimates, and the coverage of the 90% Laplace intervals.

| parameter | true_value | replications | bias | bias_se | rmse | sd_of_estimates | mean_laplace_se | coverage_90 |
|---|---|---|---|---|---|---|---|---|
| delta | -0.062 | 20 | -0.081 | 0.041 | 0.195 | 0.182 | 0.228 | 0.850 |
| beta_d | 1.269 | 20 | 0.007 | 0.010 | 0.046 | 0.046 | 0.068 | 0.950 |
| log_tau_u | 0.377 | 20 | -0.031 | 0.024 | 0.109 | 0.107 | 0.100 | 0.850 |
Lifetime switching levels against Pew (2025), adults 18-54 in 117 countries, left per 100 raised. Each run weights the history level and the survey level at random.

| religion | pew_left_per_100_raised_18_54 | history_level_model | survey_level_model | logit_shift | countries_with_own_survey_cells |
|---|---|---|---|---|---|
| Christianity | 17.10 | 12.81 | 17.10 | 0.45 | 27.00 |
| Islam | 1.00 | 1.75 | 1.00 | -0.60 | 2.00 |
| Hinduism | 1.00 | 1.36 | 1.00 | -0.32 | 4.00 |
| Buddhism | 22.10 | 14.09 | 22.10 | 0.86 | 5.00 |
| Judaism |  | 11.05 | 11.05 | 0.00 | 2.00 |
| Folk_Traditional |  | 14.30 | 14.30 | 0.00 | 0.00 |
| Other |  | 10.54 | 10.54 | 0.00 | 0.00 |
| Unaffiliated | 7.50 | 8.29 | 7.50 | -0.13 | 4.00 |

Highest fitted lifetime disaffiliation of people raised Christian (2020 development):

| country_id | mean | q05 | q95 | evidence |
|---|---|---|---|---|
| MNG | 0.935 | 0.854 | 0.985 | net change + hierarchical prior |
| ALB | 0.716 | 0.292 | 0.918 | net change + hierarchical prior |
| SVN | 0.678 | 0.144 | 0.959 | net change + hierarchical prior |
| MDA | 0.662 | 0.219 | 0.844 | net change + hierarchical prior |
| BLZ | 0.584 | 0.313 | 0.708 | net change + hierarchical prior |
| NZL | 0.580 | 0.451 | 0.679 | net change + hierarchical prior |
| NLD | 0.531 | 0.444 | 0.633 | survey + net change |
| BEL | 0.526 | 0.425 | 0.605 | net change + hierarchical prior |
| GEO | 0.449 | 0.071 | 0.670 | net change + hierarchical prior |
| KOR | 0.446 | 0.327 | 0.549 | survey + net change |

## 5. Migration

Religion of migrants calibrated to Pew's published composition of migrants: destination affinity kappa = 0.4, minority effect lambda = 0.55 (bounded at 4.5 times the origin mean in the calibration; each run draws its own bound); error 2.98 pp against 5.93 pp if migrants mirrored their origin.

Realised net migration against WPP's, 2020-2100: mean relative gap 0.266 (0 with exact margins); emigrants that could not leave because a religion's cells were full: 0.20 million per run over 2020-3030.

Foreign-born share of each country in 2020, simulated from the UN 1990 stocks (no switching), against the UN 2020 stocks:

| model | popw_mae_pp | country_mae_pp | corr_with_un | world_foreign_born_millions | un_world_foreign_born_millions |
|---|---|---|---|---|---|
| migration model, circulation 0.0000/year | 1.037 | 3.271 | 0.895 | 253.890 | 252.118 |
| migration model, circulation 0.0001/year | 0.965 | 2.987 | 0.909 | 276.040 | 252.118 |
| migration model, circulation 0.0003/year | 1.056 | 3.299 | 0.910 | 299.272 | 252.118 |
| persistence (1990 foreign-born share) | 1.758 | 4.112 | 0.890 | 211.316 | 252.118 |

Corridors 1990-2020: origin mix of simulated inflows into the 25 largest destinations against the growth of UN bilateral stocks, by margin softness and corridor cap (none = the model as used).

| margin_rho | corridor_cap | destination_origin_mix_corr | destination_origin_mix_tv | largest_origin_share_simulated | largest_origin_share_observed | simulated_moves_millions | stock_growth_millions |
|---|---|---|---|---|---|---|---|
| 1.000 | none | 0.644 | 0.511 | 0.346 | 0.412 | 229.052 | 143.455 |
| 1.000 | 4.0 | 0.566 | 0.567 | 0.297 | 0.412 | 228.260 | 143.455 |
| 1.000 | 3.0 | 0.575 | 0.563 | 0.282 | 0.412 | 228.284 | 143.455 |
| 1.000 | 2.0 | 0.540 | 0.575 | 0.288 | 0.412 | 227.674 | 143.455 |
| 1.000 | 1.5 | 0.517 | 0.583 | 0.283 | 0.412 | 228.269 | 143.455 |
| 0.750 | none | 0.672 | 0.488 | 0.312 | 0.412 | 229.222 | 143.455 |
| 0.750 | 4.0 | 0.588 | 0.530 | 0.304 | 0.412 | 228.946 | 143.455 |
| 0.750 | 3.0 | 0.580 | 0.538 | 0.297 | 0.412 | 228.815 | 143.455 |
| 0.750 | 2.0 | 0.551 | 0.548 | 0.305 | 0.412 | 228.667 | 143.455 |
| 0.750 | 1.5 | 0.555 | 0.560 | 0.277 | 0.412 | 228.976 | 143.455 |
| 0.500 | none | 0.601 | 0.513 | 0.298 | 0.412 | 229.119 | 143.455 |
| 0.500 | 4.0 | 0.571 | 0.537 | 0.300 | 0.412 | 229.105 | 143.455 |
| 0.500 | 3.0 | 0.564 | 0.540 | 0.303 | 0.412 | 229.106 | 143.455 |
| 0.500 | 2.0 | 0.545 | 0.548 | 0.310 | 0.412 | 229.102 | 143.455 |
| 0.500 | 1.5 | 0.527 | 0.559 | 0.309 | 0.412 | 229.110 | 143.455 |

Largest single origin of each main destination's simulated arrivals, 2020-2050 (reference), against that origin's share of the destination's 2020 migrant stock:

| scenario | destination | arrivals_2020_2050_millions | largest_origin | origin_share_of_arrivals | origin_share_of_2020_stock | ratio |
|---|---|---|---|---|---|---|
| stabilising | USA | 35.92 | MEX | 0.16 | 0.25 | 0.66 |
| stabilising | GBR | 9.28 | PAK | 0.36 | 0.08 | 4.32 |
| stabilising | CAN | 8.43 | IND | 0.16 | 0.11 | 1.52 |
| stabilising | RUS | 6.99 | UKR | 0.28 | 0.25 | 1.10 |
| stabilising | DEU | 6.50 | TUR | 0.27 | 0.12 | 2.23 |
| stabilising | SAU | 5.55 | PAK | 0.31 | 0.14 | 2.13 |
| stabilising | AUS | 5.05 | IND | 0.17 | 0.09 | 1.83 |
| stabilising | ZAF | 4.89 | ZWE | 0.35 | 0.38 | 0.91 |
| stabilising | MYS | 4.64 | IDN | 0.29 | 0.49 | 0.59 |
| stabilising | FRA | 4.41 | DZA | 0.18 | 0.18 | 1.00 |
| stabilising | ARE | 3.55 | IND | 0.31 | 0.41 | 0.76 |
| stabilising | JPN | 3.46 | CHN | 0.31 | 0.28 | 1.10 |
| stabilising | ESP | 3.42 | MAR | 0.19 | 0.13 | 1.42 |
| stabilising | SYR | 3.16 | PSE | 0.19 | 0.74 | 0.25 |
| stabilising | ITA | 3.03 | PAK | 0.12 | 0.02 | 5.69 |

## 6. World shares

Reference scenario `stabilising`: mean, 5-95% of runs (parameter uncertainty) and 90% predictive interval.

| year | religion | mean | q05 | q95 | pi05 | pi95 |
|---|---|---|---|---|---|---|
| 2020 | Buddhism | 4.1 | 4.1 | 4.1 |  |  |
| 2020 | Christianity | 28.8 | 28.8 | 28.8 |  |  |
| 2020 | Folk_Traditional | 1.4 | 1.4 | 1.4 |  |  |
| 2020 | Hinduism | 14.9 | 14.9 | 14.9 |  |  |
| 2020 | Islam | 25.6 | 25.6 | 25.6 |  |  |
| 2020 | Judaism | 0.2 | 0.2 | 0.2 |  |  |
| 2020 | Other | 0.8 | 0.8 | 0.8 |  |  |
| 2020 | Unaffiliated | 24.2 | 24.2 | 24.2 |  |  |
| 2050 | Buddhism | 3.0 | 2.9 | 3.2 | 2.7 | 5.4 |
| 2050 | Christianity | 27.8 | 27.2 | 28.3 | 26.0 | 29.7 |
| 2050 | Folk_Traditional | 1.3 | 1.2 | 1.4 | 0.8 | 3.7 |
| 2050 | Hinduism | 14.5 | 14.3 | 14.6 | 11.4 | 16.5 |
| 2050 | Islam | 31.7 | 31.4 | 32.0 | 29.9 | 34.2 |
| 2050 | Judaism | 0.2 | 0.2 | 0.2 | 0.1 | 0.2 |
| 2050 | Other | 0.7 | 0.7 | 0.7 | 0.6 | 2.9 |
| 2050 | Unaffiliated | 20.7 | 20.0 | 21.5 | 16.2 | 21.4 |
| 2100 | Buddhism | 1.7 | 1.5 | 2.0 | 1.4 | 3.3 |
| 2100 | Christianity | 25.7 | 24.0 | 27.3 | 22.6 | 28.8 |
| 2100 | Folk_Traditional | 1.1 | 1.0 | 1.2 | 0.6 | 4.4 |
| 2100 | Hinduism | 12.0 | 11.4 | 12.4 | 9.1 | 14.1 |
| 2100 | Islam | 39.1 | 38.2 | 40.0 | 36.7 | 42.4 |
| 2100 | Judaism | 0.3 | 0.2 | 0.3 | 0.2 | 0.3 |
| 2100 | Other | 0.5 | 0.4 | 0.6 | 0.6 | 2.8 |
| 2100 | Unaffiliated | 19.5 | 17.4 | 21.8 | 13.9 | 21.8 |

**2050, every scenario (means)**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 27.8 | 31.7 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.7 |
| combined_dispersal | 27.5 | 31.8 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 21.0 |
| continued_secularization | 27.6 | 31.7 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 21.1 |
| high_retention | 28.9 | 31.9 | 14.6 | 3.2 | 0.2 | 1.4 | 0.7 | 19.0 |
| low_migration | 27.8 | 31.7 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.8 |
| persistent_fertility_gaps | 27.7 | 31.9 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.7 |
| rising_migration | 27.8 | 31.7 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.7 |
| stabilising | 27.8 | 31.7 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.7 |

**2100, every scenario (means)**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 25.7 | 39.1 | 12.0 | 1.7 | 0.3 | 1.1 | 0.5 | 19.5 |
| combined_dispersal | 24.3 | 40.0 | 11.8 | 1.6 | 0.2 | 1.0 | 0.5 | 20.6 |
| continued_secularization | 24.6 | 38.7 | 11.9 | 1.6 | 0.2 | 1.0 | 0.5 | 21.4 |
| high_retention | 29.0 | 39.9 | 12.3 | 2.0 | 0.3 | 1.2 | 0.6 | 14.7 |
| low_migration | 25.7 | 39.1 | 12.0 | 1.7 | 0.3 | 1.1 | 0.5 | 19.6 |
| persistent_fertility_gaps | 25.5 | 40.3 | 11.8 | 1.7 | 0.3 | 1.0 | 0.5 | 18.9 |
| rising_migration | 25.7 | 39.2 | 12.1 | 1.7 | 0.2 | 1.1 | 0.5 | 19.5 |
| stabilising | 25.7 | 39.1 | 12.0 | 1.7 | 0.3 | 1.1 | 0.5 | 19.5 |

**Exploratory horizons (stated long-run assumptions; not forecasts), reference scenario**

| year | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| 2200 | 21.9 | 43.5 | 8.6 | 0.8 | 0.3 | 0.9 | 0.4 | 23.7 |
| 2500 | 19.7 | 43.8 | 5.2 | 0.4 | 0.3 | 0.9 | 0.3 | 29.3 |
| 3026 | 17.9 | 42.2 | 3.9 | 0.3 | 0.4 | 1.1 | 0.4 | 33.8 |

**Predictive medians, and the effect of centring the errors.** The intervals use the record's errors as they were; centring them (subtracting the pooled mean standardised error) is shown for comparison.

| year | religion | model_mean | pi05 | median | pi95 | centred_pi05 | centred_median | centred_pi95 |
|---|---|---|---|---|---|---|---|---|
| 2050 | Christianity | 27.8 | 26.0 | 27.7 | 29.7 | 26.9 | 28.7 | 30.7 |
| 2050 | Islam | 31.7 | 29.9 | 32.0 | 34.2 | 29.5 | 31.6 | 33.9 |
| 2050 | Hinduism | 14.5 | 11.4 | 14.2 | 16.5 | 11.9 | 14.8 | 17.1 |
| 2050 | Buddhism | 3.0 | 2.7 | 3.3 | 5.4 | 2.7 | 3.4 | 5.6 |
| 2050 | Judaism | 0.2 | 0.1 | 0.2 | 0.2 | 0.2 | 0.2 | 0.3 |
| 2050 | Folk_Traditional | 1.3 | 0.8 | 1.3 | 3.7 | 0.5 | 1.0 | 3.5 |
| 2050 | Other | 0.7 | 0.6 | 1.2 | 2.9 | 0.2 | 0.7 | 2.2 |
| 2050 | Unaffiliated | 20.7 | 16.2 | 19.5 | 21.4 | 15.6 | 19.0 | 21.0 |
| 2100 | Christianity | 25.7 | 22.6 | 26.0 | 28.8 | 23.7 | 27.3 | 30.2 |
| 2100 | Islam | 39.1 | 36.7 | 39.4 | 42.4 | 36.4 | 39.2 | 42.2 |
| 2100 | Hinduism | 12.0 | 9.1 | 11.7 | 14.1 | 9.5 | 12.3 | 14.7 |
| 2100 | Buddhism | 1.7 | 1.4 | 2.0 | 3.3 | 1.5 | 2.1 | 3.5 |
| 2100 | Judaism | 0.3 | 0.2 | 0.2 | 0.3 | 0.2 | 0.3 | 0.4 |
| 2100 | Folk_Traditional | 1.1 | 0.6 | 1.0 | 4.4 | 0.4 | 0.8 | 4.2 |
| 2100 | Other | 0.5 | 0.6 | 1.2 | 2.8 | 0.3 | 0.7 | 2.2 |
| 2100 | Unaffiliated | 19.5 | 13.9 | 17.8 | 21.8 | 12.9 | 16.7 | 20.8 |

### Three kinds of uncertainty (world shares, pp)

Run spread = mean 5-95% band inside a scenario; predictive = mean 90% predictive band (to 2100); between = range of scenario means.

| year | religion | within_scenario_band_pp_mean | predictive_band_pp_mean | between_scenario_range_pp | lowest_scenario | highest_scenario |
|---|---|---|---|---|---|---|
| 2050 | Buddhism | 0.34 | 2.75 | 0.24 | combined_dispersal | high_retention |
| 2050 | Christianity | 1.05 | 3.68 | 1.41 | combined_dispersal | high_retention |
| 2050 | Folk_Traditional | 0.15 | 2.83 | 0.12 | combined_dispersal | high_retention |
| 2050 | Hinduism | 0.32 | 5.15 | 0.10 | combined_dispersal | high_retention |
| 2050 | Islam | 0.56 | 4.29 | 0.21 | continued_secularization | high_retention |
| 2050 | Judaism | 0.02 | 0.09 | 0.01 | combined_dispersal | high_retention |
| 2050 | Other | 0.07 | 2.28 | 0.03 | combined_dispersal | high_retention |
| 2050 | Unaffiliated | 1.48 | 5.13 | 2.03 | high_retention | continued_secularization |
| 2100 | Buddhism | 0.54 | 1.94 | 0.45 | combined_dispersal | high_retention |
| 2100 | Christianity | 3.29 | 6.01 | 4.68 | combined_dispersal | high_retention |
| 2100 | Folk_Traditional | 0.26 | 3.77 | 0.27 | combined_dispersal | high_retention |
| 2100 | Hinduism | 1.03 | 4.79 | 0.51 | combined_dispersal | high_retention |
| 2100 | Islam | 1.70 | 5.67 | 1.60 | continued_secularization | persistent_fertility_gaps |
| 2100 | Judaism | 0.04 | 0.17 | 0.02 | combined_dispersal | high_retention |
| 2100 | Other | 0.15 | 2.19 | 0.11 | combined_dispersal | high_retention |
| 2100 | Unaffiliated | 4.20 | 7.91 | 6.65 | high_retention | continued_secularization |

## 7. What changes world shares, 2020-2100 (`stabilising`, pp)

The simulation's own sub-step accounting; the parts add up exactly to the total. Migration cancels worldwide.

| religion | survival | births | switching | emigration | immigration | calibration | total |
|---|---|---|---|---|---|---|---|
| Christianity | -0.80 | 3.07 | -5.42 | -0.10 | 0.10 | 0.11 | -3.05 |
| Islam | 6.08 | 9.10 | -0.59 | -0.32 | 0.32 | -1.12 | 13.47 |
| Hinduism | 0.26 | -2.22 | -0.28 | 0.38 | -0.38 | -0.66 | -2.90 |
| Buddhism | -1.04 | -1.21 | -0.37 | 0.01 | -0.01 | 0.23 | -2.39 |
| Judaism | 0.02 | -0.02 | 0.04 | 0.00 | -0.00 | 0.03 | 0.07 |
| Folk_Traditional | -0.14 | -0.21 | -0.01 | 0.00 | -0.00 | 0.02 | -0.33 |
| Other | -0.08 | -0.16 | -0.01 | -0.01 | 0.01 | -0.00 | -0.24 |
| Unaffiliated | -4.31 | -8.35 | 6.64 | 0.03 | -0.03 | 1.39 | -4.63 |

## 8. Where world-share change comes from, 2020-2100

An exact split of each religion's change in world share into countries' own shares changing and country populations growing at different rates.

| religion | change_pp | within_country_pp | population_weighting_pp | interaction_pp |
|---|---|---|---|---|
| Christianity | -3.04 | -8.74 | 6.53 | -0.83 |
| Islam | 13.46 | 3.29 | 10.29 | -0.11 |
| Hinduism | -2.90 | -0.63 | -2.37 | 0.10 |
| Buddhism | -2.39 | -1.13 | -1.69 | 0.43 |
| Judaism | 0.07 | 0.03 | 0.05 | -0.02 |
| Folk_Traditional | -0.33 | 0.02 | -0.24 | -0.11 |
| Other | -0.24 | -0.15 | -0.11 | 0.02 |
| Unaffiliated | -4.63 | 7.32 | -12.46 | 0.51 |

## 9. What each mechanism contributes

The full model minus the same run with one mechanism switched off, paired run by run on identical draws. Percentage points of world population (dominant_changed_countries is a count).

| outcome | year | demography only | fertility differences | migration | religious switching |
|---|---|---|---|---|---|
| dominant_changed_countries | 2050 | 6.50 | 0.00 | -0.42 | 6.42 |
| dominant_changed_countries | 2100 | 45.00 | -1.00 | -2.00 | 42.00 |
| world_Christianity | 2050 | -2.87 | -0.19 | -0.05 | -2.60 |
| world_Christianity | 2100 | -9.07 | -0.74 | -0.15 | -7.97 |
| world_Hinduism | 2050 | -0.17 | -0.16 | 0.04 | -0.04 |
| world_Hinduism | 2100 | -0.50 | -0.45 | 0.13 | -0.16 |
| world_Islam | 2050 | 0.68 | 0.72 | 0.06 | -0.06 |
| world_Islam | 2100 | 1.86 | 2.37 | 0.34 | -0.71 |
| world_Unaffiliated | 2050 | 2.60 | -0.28 | -0.04 | 2.84 |
| world_Unaffiliated | 2100 | 8.45 | -0.91 | -0.27 | 9.25 |

## 10. Which assumptions move the results

Standardised rank regression coefficients (top five per outcome) from a separate Monte Carlo design.


**2050**

| outcome | parameter | coefficient | model_r2 |
|---|---|---|---|
| world_Christianity | survey_weight | -0.699 | 0.634 |
| world_Islam | psi | 0.687 | 0.729 |
| world_Unaffiliated | survey_weight | 0.451 | 0.542 |
| world_Unaffiliated | psi | -0.330 | 0.542 |
| world_Islam | survey_weight | 0.312 | 0.729 |
| diversity_within_pop_weighted | survey_weight | 0.261 | 0.213 |
| world_Islam | phi_region | 0.235 | 0.729 |
| world_Unaffiliated | delta | 0.217 | 0.542 |
| world_Christianity | omega | 0.204 | 0.634 |
| world_Islam | phi | 0.193 | 0.729 |
| diversity_within_pop_weighted | g2_ratio | 0.179 | 0.213 |
| world_Unaffiliated | omega | -0.176 | 0.542 |
| diversity_within_pop_weighted | selectivity_cap | -0.155 | 0.213 |
| world_Islam | tfr_hl | 0.153 | 0.729 |
| world_Unaffiliated | theta | 0.149 | 0.542 |
| diversity_within_pop_weighted | h2 | 0.131 | 0.213 |
| diversity_within_pop_weighted | Hf | -0.124 | 0.213 |
| world_Christianity | h2 | -0.123 | 0.634 |
| world_Christianity | theta | -0.122 | 0.634 |
| world_Christianity | tfr_dev_half_life | -0.122 | 0.634 |

**2100**

| outcome | parameter | coefficient | model_r2 |
|---|---|---|---|
| world_Christianity | survey_weight | -0.512 | 0.503 |
| world_Islam | Hf | 0.409 | 0.632 |
| world_Islam | survey_weight | 0.384 | 0.632 |
| world_Islam | psi | 0.337 | 0.632 |
| world_Islam | phi_region | 0.262 | 0.632 |
| world_Unaffiliated | survey_weight | 0.250 | 0.427 |
| world_Unaffiliated | delta | 0.240 | 0.427 |
| diversity_within_pop_weighted | g2_ratio | 0.238 | 0.185 |
| world_Christianity | omega | 0.230 | 0.503 |
| world_Islam | margin_rho | 0.222 | 0.632 |
| world_Unaffiliated | omega | -0.205 | 0.427 |
| world_Unaffiliated | beta_d | 0.202 | 0.427 |
| world_Unaffiliated | Hf | -0.190 | 0.427 |
| world_Christianity | theta | -0.177 | 0.503 |
| world_Christianity | tau_u | 0.168 | 0.503 |
| diversity_within_pop_weighted | tau_u | -0.167 | 0.185 |
| diversity_within_pop_weighted | selectivity_cap | -0.165 | 0.185 |
| world_Christianity | tfr_lr | -0.139 | 0.503 |
| diversity_within_pop_weighted | Hf | -0.138 | 0.185 |
| diversity_within_pop_weighted | m_g1 | -0.116 | 0.185 |

## 11. Countries whose largest religion changes

Countries where most runs change (parameter uncertainty only):

| scenario | most_runs_by_2050 | most_runs_by_2100 | most_runs_by_2200 | most_runs_by_2500 | most_runs_by_3026 |
|---|---|---|---|---|---|
| changing_migration | 6 | 31 | 77 | 113 | 126 |
| combined_dispersal | 6 | 38 | 103 | 139 | 144 |
| continued_secularization | 6 | 37 | 109 | 182 | 189 |
| high_retention | 4 | 21 | 38 | 66 | 89 |
| low_migration | 6 | 34 | 80 | 104 | 122 |
| persistent_fertility_gaps | 6 | 32 | 78 | 121 | 144 |
| rising_migration | 6 | 31 | 78 | 109 | 126 |
| stabilising | 6 | 31 | 82 | 108 | 120 |

Predictive probability of a change by 2050 and 2100 (`stabilising`), the 25 highest at 2100. 26 countries exceed 50% by 2100.

| country_id | dominant_2020 | most_likely_new_2100_predictive | prob_changed_by_2050_predictive | prob_changed_by_2100_predictive | prob_changed_by_2100 |
|---|---|---|---|---|---|
| MNG | Buddhism | Unaffiliated | 0.74 | 0.93 | 1.00 |
| SGP | Buddhism | Unaffiliated | 0.61 | 0.91 | 1.00 |
| FRA | Christianity | Unaffiliated | 0.55 | 0.89 | 1.00 |
| TWN | Folk_Traditional | Unaffiliated | 0.39 | 0.86 | 0.93 |
| GBR | Christianity | Unaffiliated | 0.42 | 0.85 | 1.00 |
| DEU | Christianity | Unaffiliated | 0.30 | 0.78 | 1.00 |
| MKD | Christianity | Islam | 0.06 | 0.77 | 0.95 |
| SWE | Christianity | Unaffiliated | 0.20 | 0.77 | 1.00 |
| BEL | Christianity | Unaffiliated | 0.46 | 0.74 | 1.00 |
| AUS | Christianity | Unaffiliated | 0.58 | 0.74 | 1.00 |
| BLZ | Christianity | Unaffiliated | 0.17 | 0.71 | 1.00 |
| CAN | Christianity | Unaffiliated | 0.32 | 0.69 | 1.00 |
| SLV | Christianity | Unaffiliated | 0.05 | 0.69 | 0.93 |
| SVN | Christianity | Unaffiliated | 0.14 | 0.67 | 0.95 |
| FIN | Christianity | Unaffiliated | 0.14 | 0.66 | 1.00 |
| CHL | Christianity | Unaffiliated | 0.16 | 0.65 | 0.88 |
| CHE | Christianity | Unaffiliated | 0.17 | 0.65 | 1.00 |
| NIC | Christianity | Unaffiliated | 0.10 | 0.65 | 0.88 |
| CRI | Christianity | Unaffiliated | 0.04 | 0.63 | 0.88 |
| MDA | Christianity | Unaffiliated | 0.00 | 0.62 | 0.95 |
| EST | Christianity | Unaffiliated | 0.45 | 0.61 | 0.65 |
| ESP | Christianity | Unaffiliated | 0.10 | 0.61 | 1.00 |
| AUT | Christianity | Unaffiliated | 0.07 | 0.59 | 1.00 |
| ARG | Christianity | Unaffiliated | 0.01 | 0.57 | 0.68 |
| GEO | Christianity | Unaffiliated | 0.02 | 0.56 | 0.93 |

## 12. Does more migration make countries more mixed?

Rising minus low migration, paired by run, under three assumptions about where migrants go.

| year | variant | median | q05 | q95 | runs_more_diverse | runs |
|---|---|---|---|---|---|---|
| 2050 | calibrated | 0.0008 | 0.0008 | 0.0010 | 12 | 12 |
| 2050 | migrants mirror origin | 0.0022 | 0.0019 | 0.0027 | 12 | 12 |
| 2050 | no destination affinity | 0.0013 | 0.0011 | 0.0015 | 12 | 12 |
| 2100 | calibrated | 0.0043 | 0.0039 | 0.0050 | 12 | 12 |
| 2100 | migrants mirror origin | 0.0128 | 0.0104 | 0.0144 | 12 | 12 |
| 2100 | no destination affinity | 0.0071 | 0.0057 | 0.0076 | 12 | 12 |
| 2200 | calibrated | 0.0174 | 0.0139 | 0.0196 | 12 | 12 |
| 2200 | migrants mirror origin | 0.0432 | 0.0345 | 0.0495 | 12 | 12 |
| 2200 | no destination affinity | 0.0267 | 0.0203 | 0.0296 | 12 | 12 |
| 2500 | calibrated | 0.0366 | 0.0235 | 0.0444 | 12 | 12 |
| 2500 | migrants mirror origin | 0.0827 | 0.0699 | 0.0983 | 12 | 12 |
| 2500 | no destination affinity | 0.0606 | 0.0421 | 0.0699 | 12 | 12 |
| 3026 | calibrated | 0.0535 | 0.0261 | 0.0636 | 12 | 12 |
| 3026 | migrants mirror origin | 0.0948 | 0.0772 | 0.1189 | 12 | 12 |
| 3026 | no destination affinity | 0.0782 | 0.0467 | 0.0918 | 12 | 12 |

## 13. How much of the fertility input is measured

| evidence_tier | percent_of_world_population |
|---|---|
| country | 23.7 |
| region | 20.7 |
| world | 55.5 |

## 14. Against Pew Research Center's 2015 projection

Change in world share 2020-2050 as each projects it, and the difference in 2020 levels.

| religion | this_model_change_pp | pew2015_change_pp | change_difference_pp | level_difference_2020_pp |
|---|---|---|---|---|
| Christianity | -1.01 | 0.24 | -1.25 | -2.35 |
| Islam | 6.07 | 4.76 | 1.31 | 0.74 |
| Hinduism | -0.43 | -0.29 | -0.13 | -0.23 |
| Buddhism | -1.06 | -1.40 | 0.33 | -2.51 |
| Judaism | 0.02 | -0.02 | 0.04 | -0.00 |
| Folk_Traditional | -0.09 | -0.79 | 0.69 | -4.22 |
| Other | -0.08 | -0.14 | 0.06 | -0.01 |
| Unaffiliated | -3.41 | -2.37 | -1.04 | 8.57 |

Pew's 2015 projection of 2020 scored against Pew's later measurement of 2020:

| source | countries | popw_tv_pp | mean_tv_pp | median_tv_pp | largest_contributors |
|---|---|---|---|---|---|
| Pew 2015 report, projected 2020 | 171 | 10.66 | 8.18 | 5.32 | CHN 69%, VNM 6%, BRA 2%, IND 1%, NGA 1% |
| Pew 2015 report, no change from 2010 | 171 | 10.95 | 8.78 | 5.82 | CHN 67%, VNM 6%, BRA 2%, NGA 2%, IND 2% |

## 15. Read with care

- All history tests and predictive intervals are conditional on national demography (WPP 2024 estimates inside each historical window, the WPP 2024 medium variant in the projection).
- The predictive intervals extrapolate the error growth measured at 10-40 years to 80 years.
- Beyond 2100 every demographic input is a stated assumption; 2200, 2500 and 3026 are exploratory.
- The religion of migrants is calibrated to aggregate Pew figures, not observed by corridor.
- Folk/Traditional versus Other in Pew data is a World Religion Project proxy, and the two sources classify much of China differently.
