# Run report

Generated 2026-11-24 00:17 UTC from `data/validation/`, `data/projections/` and `data/experiments/`. Shares are in percent; differences in percentage points (pp).

## 1. Inputs

| input | status | detail |
|---|---|---|
| wpp_indicators | used | 237 countries, 1950-2100 |
| start_state | used | Pew 2010/2020 via scripts/prepare_pew_panel.py (201 countries in 2020, 201 in 2010) |
| wrp | used | 1730 usable country-years of 1995 |
| natural_earth | used | 242 map units |
| wpp_age | used | 200 of 200 countries, 1950-2100 (5-year points) |
| bilateral_stock | used | undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx: 68941 country pairs x years, years [np.int64(1990), np.int64(1995), np.int64(2000), np.int64(2005), np.int64(2010), np.int64(2015), np.int64(2020), np.int64(2024)] (cached parse) |
| migrant_religion | missing | no country-level Pew migrant file; religion of migrants from the affinity model calibrated to Pew published aggregates (inputs/migrant_religion_published.csv) |
| switching_survey | used | 67 verified cells, 33 countries |
| religion_fertility | used | 8 world, 5 regional (2 regions), 10 country figures (4 countries); 7 rows held back |
| unhcr | used | 138893 rows 1951-2025 |
| pew_2015_projection | used | 5 years, 234 countries |

Start state: data/processed/pew_harmonized.csv (Pew 2010 and 2020; Folk/Other split by WRP proxy). Runs per scenario: 40, seed 2026, reference scenario `stabilising`.

## 2. History tests

Ten-year forecasts of every test decade, fitted only on earlier decades. Population-weighted total-variation (TV) error of country shares, in pp; the change is against persistence.

| scope | model | windows | popw_tv_pp | change_vs_persistence_pp | change_vs_persistence_percent | dominant_accuracy | changed_true | changed_hit | false_alarm |
|---|---|---|---|---|---|---|---|---|---|
| WRP 1970-2010 | persistence | 4 | 4.406 | 0.000 | 0.000 | 0.961 | 21 | 0 | 0 |
| WRP 1970-2010 | trend | 4 | 5.974 | 1.568 | 35.578 | 0.959 | 21 | 6 | 8 |
| WRP 1970-2010 | trend_residual | 4 | 5.858 | 1.452 | 32.941 | 0.963 | 21 | 6 | 6 |
| WRP 1970-2010 | demography | 4 | 4.380 | -0.026 | -0.597 | 0.963 | 21 | 2 | 1 |
| WRP 1970-2010 | demography_migration | 4 | 4.373 | -0.033 | -0.749 | 0.961 | 21 | 2 | 2 |
| WRP 1970-2010 | switching_0.5 | 4 | 4.571 | 0.164 | 3.729 | 0.963 | 21 | 3 | 2 |
| WRP 1970-2010 | switching_1 | 4 | 4.920 | 0.514 | 11.666 | 0.962 | 21 | 3 | 3 |
| WRP 1970-2010 | switching_selected | 4 | 4.601 | 0.194 | 4.410 | 0.963 | 21 | 3 | 2 |
| WRP 1990-2010 | persistence | 2 | 4.623 | 0.000 | 0.000 | 0.969 | 9 | 0 | 0 |
| WRP 1990-2010 | trend | 2 | 7.054 | 2.431 | 52.574 | 0.953 | 9 | 0 | 5 |
| WRP 1990-2010 | trend_residual | 2 | 6.836 | 2.213 | 47.862 | 0.956 | 9 | 0 | 4 |
| WRP 1990-2010 | demography | 2 | 4.583 | -0.041 | -0.880 | 0.972 | 9 | 1 | 0 |
| WRP 1990-2010 | demography_migration | 2 | 4.573 | -0.050 | -1.085 | 0.969 | 9 | 1 | 1 |
| WRP 1990-2010 | switching_0.5 | 2 | 4.563 | -0.060 | -1.308 | 0.969 | 9 | 1 | 1 |
| WRP 1990-2010 | switching_1 | 2 | 4.625 | 0.002 | 0.047 | 0.969 | 9 | 1 | 1 |
| WRP 1990-2010 | switching_selected | 2 | 4.573 | -0.050 | -1.085 | 0.969 | 9 | 1 | 1 |
| Pew 2010-2020 | persistence | 1 | 3.440 | 0.000 | 0.000 | 0.990 | 2 | 0 | 0 |
| Pew 2010-2020 | trend | 1 | 4.451 | 1.011 | 29.383 | 0.985 | 2 | 1 | 2 |
| Pew 2010-2020 | trend_residual | 1 | 4.469 | 1.029 | 29.904 | 0.985 | 2 | 1 | 2 |
| Pew 2010-2020 | demography | 1 | 3.433 | -0.007 | -0.203 | 0.990 | 2 | 0 | 0 |
| Pew 2010-2020 | demography_migration | 1 | 3.408 | -0.032 | -0.927 | 0.990 | 2 | 0 | 0 |
| Pew 2010-2020 | switching_0.5 | 1 | 3.283 | -0.157 | -4.558 | 0.990 | 2 | 0 | 0 |
| Pew 2010-2020 | switching_1 | 1 | 3.201 | -0.240 | -6.964 | 0.985 | 2 | 0 | 1 |
| Pew 2010-2020 | switching_selected | 1 | 3.408 | -0.032 | -0.927 | 0.990 | 2 | 0 | 0 |
| all windows | persistence | 5 | 4.213 | 0.000 | 0.000 | 0.967 | 23 | 0 | 0 |
| all windows | trend | 5 | 5.669 | 1.456 | 34.566 | 0.964 | 23 | 7 | 10 |
| all windows | trend_residual | 5 | 5.580 | 1.367 | 32.445 | 0.967 | 23 | 7 | 8 |
| all windows | demography | 5 | 4.191 | -0.022 | -0.533 | 0.968 | 23 | 2 | 1 |
| all windows | demography_migration | 5 | 4.180 | -0.033 | -0.778 | 0.967 | 23 | 2 | 2 |
| all windows | switching_0.5 | 5 | 4.313 | 0.100 | 2.375 | 0.969 | 23 | 3 | 2 |
| all windows | switching_1 | 5 | 4.576 | 0.363 | 8.624 | 0.966 | 23 | 3 | 4 |
| all windows | switching_selected | 5 | 4.362 | 0.149 | 3.538 | 0.969 | 23 | 3 | 2 |

### Country-level comparison with persistence

Population-weighted mean difference in TV error over every country-decade (negative = better), with a 95% interval from a bootstrap over countries, and the exact decade-level sign-flip test.

| scope | model | country_windows | mean_difference_pp | ci95_low_pp | ci95_high_pp | p_bootstrap | share_better | windows_better | windows | p_window |
|---|---|---|---|---|---|---|---|---|---|---|
| WRP 1970-2010 | trend | 558 | 1.859 | 1.214 | 2.408 | 0.000 | 0.342 | 0 | 4 | 0.125 |
| WRP 1970-2010 | trend_residual | 558 | 1.715 | 1.043 | 2.266 | 0.000 | 0.366 | 0 | 4 | 0.125 |
| WRP 1970-2010 | demography | 558 | -0.020 | -0.083 | 0.049 | 0.606 | 0.462 | 2 | 4 | 0.750 |
| WRP 1970-2010 | demography_migration | 558 | -0.027 | -0.074 | 0.032 | 0.350 | 0.504 | 3 | 4 | 0.625 |
| WRP 1970-2010 | switching_0.5 | 558 | 0.153 | -0.186 | 0.446 | 0.685 | 0.591 | 2 | 4 | 0.875 |
| WRP 1970-2010 | switching_1 | 558 | 0.462 | -0.195 | 1.101 | 0.480 | 0.584 | 2 | 4 | 0.750 |
| WRP 1970-2010 | switching_selected | 558 | 0.177 | -0.112 | 0.476 | 0.701 | 0.539 | 2 | 4 | 0.875 |
| Pew 2010-2020 | trend | 200 | 1.011 | -0.485 | 2.653 | 0.408 | 0.300 | 0 | 1 |  |
| Pew 2010-2020 | trend_residual | 200 | 1.029 | -0.477 | 2.657 | 0.370 | 0.315 | 0 | 1 |  |
| Pew 2010-2020 | demography | 200 | -0.007 | -0.176 | 0.148 | 0.993 | 0.405 | 1 | 1 |  |
| Pew 2010-2020 | demography_migration | 200 | -0.032 | -0.190 | 0.134 | 0.786 | 0.375 | 1 | 1 |  |
| Pew 2010-2020 | switching_0.5 | 200 | -0.157 | -0.417 | 0.082 | 0.210 | 0.465 | 1 | 1 |  |
| Pew 2010-2020 | switching_1 | 200 | -0.240 | -0.704 | 0.159 | 0.249 | 0.445 | 1 | 1 |  |
| Pew 2010-2020 | switching_selected | 200 | -0.032 | -0.190 | 0.134 | 0.786 | 0.375 | 1 | 1 |  |
| all windows | trend | 758 | 1.613 | 0.797 | 2.343 | 0.000 | 0.331 | 0 | 5 | 0.062 |
| all windows | trend_residual | 758 | 1.516 | 0.687 | 2.266 | 0.000 | 0.352 | 0 | 5 | 0.062 |
| all windows | demography | 758 | -0.016 | -0.061 | 0.060 | 0.615 | 0.447 | 3 | 5 | 0.625 |
| all windows | demography_migration | 758 | -0.028 | -0.072 | 0.047 | 0.384 | 0.470 | 4 | 5 | 0.562 |
| all windows | switching_0.5 | 758 | 0.063 | -0.221 | 0.332 | 0.757 | 0.558 | 3 | 5 | 0.938 |
| all windows | switching_1 | 758 | 0.259 | -0.300 | 0.815 | 0.701 | 0.547 | 3 | 5 | 0.875 |
| all windows | switching_selected | 758 | 0.117 | -0.101 | 0.347 | 0.608 | 0.496 | 3 | 5 | 0.875 |

## 3. Forecast errors and predictive intervals

Error model e = (h/10)^beta (s(1-s) + eps)^b u, fitted on the history record: b = 0.834, beta = 0.381. Mean |standardised error| by horizon: 10 years 0.328, 20 years 0.426, 30 years 0.510, 40 years 0.534. Resampling blocks: WRP 1970-1980, WRP 1980-1990, WRP 1990-2000, WRP 2000-2010, Pew 2010-2020.

Out-of-sample coverage of country x religion shares and interval score (lower is better). Main scheme "non-overlapping": the error model is refitted, for each forecast, on history entries that share no calendar years with it; "real-time" uses only entries that ended by the forecast origin; the overlapping leave-one-origin-out design is shown for comparison. Coverage over all cells, over cells observed above zero, and by forecast share.

| scheme | method | horizon | nominal | coverage | coverage_popw | interval_score_pp | median_width_pp | coverage_above_zero | coverage_share_5_20 | coverage_share_20_plus | interval_score_above_zero_pp |
|---|---|---|---|---|---|---|---|---|---|---|---|
| leave-one-origin-out (overlapping) | error-calibrated | 10 | 0.800 | 0.819 | 0.861 | 6.666 | 0.908 | 0.789 | 0.779 | 0.807 | 8.697 |
| leave-one-origin-out (overlapping) | error-calibrated | 10 | 0.900 | 0.900 | 0.929 | 9.349 | 1.579 | 0.884 | 0.878 | 0.900 | 12.182 |
| leave-one-origin-out (overlapping) | error-calibrated | 20 | 0.800 | 0.828 | 0.846 | 10.007 | 1.367 | 0.792 | 0.759 | 0.789 | 13.156 |
| leave-one-origin-out (overlapping) | error-calibrated | 20 | 0.900 | 0.920 | 0.940 | 13.341 | 2.403 | 0.900 | 0.896 | 0.895 | 17.511 |
| leave-one-origin-out (overlapping) | error-calibrated | 30 | 0.800 | 0.831 | 0.795 | 12.917 | 1.875 | 0.793 | 0.809 | 0.752 | 17.125 |
| leave-one-origin-out (overlapping) | error-calibrated | 30 | 0.900 | 0.920 | 0.929 | 17.210 | 3.428 | 0.894 | 0.908 | 0.887 | 22.754 |
| leave-one-origin-out (overlapping) | error-calibrated | 40 | 0.800 | 0.854 | 0.824 | 14.913 | 2.300 | 0.818 | 0.889 | 0.720 | 19.965 |
| leave-one-origin-out (overlapping) | error-calibrated | 40 | 0.900 | 0.934 | 0.936 | 18.926 | 4.340 | 0.912 | 0.949 | 0.866 | 25.276 |
| non-overlapping | error-calibrated | 10 | 0.800 | 0.819 | 0.861 | 6.666 | 0.908 | 0.789 | 0.779 | 0.807 | 8.697 |
| non-overlapping | error-calibrated | 10 | 0.900 | 0.900 | 0.929 | 9.349 | 1.579 | 0.884 | 0.878 | 0.900 | 12.182 |
| non-overlapping | error-calibrated | 20 | 0.800 | 0.792 | 0.830 | 10.526 | 1.290 | 0.752 | 0.723 | 0.727 | 13.839 |
| non-overlapping | error-calibrated | 20 | 0.900 | 0.890 | 0.910 | 14.356 | 2.271 | 0.866 | 0.852 | 0.860 | 18.825 |
| non-overlapping | error-calibrated | 30 | 0.800 | 0.791 | 0.759 | 13.985 | 1.732 | 0.745 | 0.762 | 0.722 | 18.575 |
| non-overlapping | error-calibrated | 30 | 0.900 | 0.881 | 0.845 | 19.894 | 2.995 | 0.847 | 0.881 | 0.840 | 26.295 |
| non-overlapping | error-calibrated | 40 | 0.800 | 0.725 | 0.642 | 17.756 | 1.570 | 0.677 | 0.708 | 0.616 | 23.785 |
| non-overlapping | error-calibrated | 40 | 0.900 | 0.821 | 0.728 | 24.861 | 2.886 | 0.781 | 0.823 | 0.732 | 33.240 |
| non-overlapping | error-calibrated, central path | 10 | 0.800 | 0.786 | 0.836 | 6.700 | 0.827 | 0.760 | 0.756 | 0.792 | 8.741 |
| non-overlapping | error-calibrated, central path | 10 | 0.900 | 0.886 | 0.922 | 9.418 | 1.501 | 0.871 | 0.869 | 0.889 | 12.271 |
| non-overlapping | error-calibrated, central path | 20 | 0.800 | 0.751 | 0.814 | 10.689 | 1.202 | 0.714 | 0.702 | 0.688 | 14.051 |
| non-overlapping | error-calibrated, central path | 20 | 0.900 | 0.865 | 0.912 | 14.620 | 2.133 | 0.843 | 0.838 | 0.842 | 19.167 |
| non-overlapping | error-calibrated, central path | 30 | 0.800 | 0.764 | 0.706 | 14.233 | 1.525 | 0.717 | 0.743 | 0.707 | 18.918 |
| non-overlapping | error-calibrated, central path | 30 | 0.900 | 0.868 | 0.824 | 20.187 | 2.734 | 0.833 | 0.877 | 0.835 | 26.686 |
| non-overlapping | error-calibrated, central path | 40 | 0.800 | 0.686 | 0.591 | 18.048 | 1.441 | 0.638 | 0.674 | 0.555 | 24.187 |
| non-overlapping | error-calibrated, central path | 40 | 0.900 | 0.825 | 0.732 | 24.768 | 3.000 | 0.789 | 0.853 | 0.738 | 33.119 |
| non-overlapping | error-calibrated, centred | 10 | 0.800 | 0.814 | 0.835 | 6.706 | 0.817 | 0.795 | 0.801 | 0.818 | 8.742 |
| non-overlapping | error-calibrated, centred | 10 | 0.900 | 0.907 | 0.944 | 9.278 | 1.535 | 0.896 | 0.910 | 0.913 | 12.079 |
| non-overlapping | error-calibrated, centred | 20 | 0.800 | 0.749 | 0.764 | 10.622 | 1.167 | 0.740 | 0.777 | 0.743 | 13.975 |
| non-overlapping | error-calibrated, centred | 20 | 0.900 | 0.872 | 0.897 | 14.232 | 2.145 | 0.866 | 0.874 | 0.874 | 18.666 |
| non-overlapping | error-calibrated, centred | 30 | 0.800 | 0.729 | 0.736 | 14.277 | 1.420 | 0.730 | 0.796 | 0.724 | 18.974 |
| non-overlapping | error-calibrated, centred | 30 | 0.900 | 0.839 | 0.843 | 20.143 | 2.833 | 0.826 | 0.855 | 0.836 | 26.615 |
| non-overlapping | error-calibrated, centred | 40 | 0.800 | 0.611 | 0.501 | 18.118 | 1.326 | 0.622 | 0.744 | 0.569 | 24.200 |
| non-overlapping | error-calibrated, centred | 40 | 0.900 | 0.769 | 0.718 | 25.636 | 2.749 | 0.774 | 0.872 | 0.695 | 34.210 |
| non-overlapping | model draws (parameter uncertainty) | 10 | 0.800 | 0.149 | 0.141 | 10.560 | 0.084 | 0.194 | 0.172 | 0.208 | 13.764 |
| non-overlapping | model draws (parameter uncertainty) | 10 | 0.900 | 0.178 | 0.180 | 19.672 | 0.107 | 0.232 | 0.225 | 0.238 | 25.673 |
| non-overlapping | model draws (parameter uncertainty) | 20 | 0.800 | 0.155 | 0.146 | 18.077 | 0.175 | 0.205 | 0.194 | 0.190 | 23.592 |
| non-overlapping | model draws (parameter uncertainty) | 20 | 0.900 | 0.184 | 0.170 | 33.343 | 0.231 | 0.244 | 0.218 | 0.238 | 43.512 |
| non-overlapping | model draws (parameter uncertainty) | 30 | 0.800 | 0.158 | 0.123 | 23.734 | 0.268 | 0.212 | 0.192 | 0.178 | 31.106 |
| non-overlapping | model draws (parameter uncertainty) | 30 | 0.900 | 0.184 | 0.156 | 43.274 | 0.352 | 0.247 | 0.243 | 0.199 | 56.699 |
| non-overlapping | model draws (parameter uncertainty) | 40 | 0.800 | 0.157 | 0.125 | 27.764 | 0.343 | 0.213 | 0.264 | 0.194 | 36.783 |
| non-overlapping | model draws (parameter uncertainty) | 40 | 0.900 | 0.186 | 0.140 | 49.718 | 0.418 | 0.252 | 0.319 | 0.236 | 65.831 |
| real-time | error-calibrated | 10 | 0.800 | 0.824 | 0.846 | 7.113 | 1.041 | 0.790 | 0.750 | 0.775 | 9.234 |
| real-time | error-calibrated | 10 | 0.900 | 0.907 | 0.938 | 10.246 | 1.964 | 0.889 | 0.865 | 0.889 | 13.253 |
| real-time | error-calibrated | 20 | 0.800 | 0.769 | 0.831 | 11.850 | 1.571 | 0.726 | 0.668 | 0.664 | 15.715 |
| real-time | error-calibrated | 20 | 0.900 | 0.873 | 0.901 | 16.406 | 3.077 | 0.850 | 0.792 | 0.809 | 21.568 |
| real-time | error-calibrated | 30 | 0.800 | 0.830 | 0.805 | 14.772 | 2.464 | 0.795 | 0.742 | 0.724 | 19.577 |
| real-time | error-calibrated | 30 | 0.900 | 0.908 | 0.906 | 21.760 | 4.529 | 0.887 | 0.868 | 0.856 | 28.454 |

World shares of the observed countries (8 religions per held-out origin and horizon): share inside the interval, by nominal level.

| scheme | method | horizon | 0.5 | 0.8 | 0.9 | 0.95 |
|---|---|---|---|---|---|---|
| leave-one-origin-out (overlapping) | error-calibrated | 10 | 0.45 | 0.78 | 0.85 | 0.93 |
| leave-one-origin-out (overlapping) | error-calibrated | 20 | 0.42 | 0.71 | 0.96 | 0.96 |
| leave-one-origin-out (overlapping) | error-calibrated | 30 | 0.31 | 0.62 | 0.94 | 1.00 |
| leave-one-origin-out (overlapping) | error-calibrated | 40 | 0.38 | 0.62 | 1.00 | 1.00 |
| non-overlapping | error-calibrated | 10 | 0.45 | 0.78 | 0.85 | 0.93 |
| non-overlapping | error-calibrated | 20 | 0.33 | 0.67 | 0.83 | 0.96 |
| non-overlapping | error-calibrated | 30 | 0.31 | 0.50 | 0.56 | 0.94 |
| non-overlapping | error-calibrated | 40 | 0.12 | 0.62 | 0.75 | 0.75 |
| non-overlapping | error-calibrated, central path | 10 | 0.45 | 0.78 | 0.85 | 0.93 |
| non-overlapping | error-calibrated, central path | 20 | 0.33 | 0.62 | 0.83 | 0.96 |
| non-overlapping | error-calibrated, central path | 30 | 0.31 | 0.50 | 0.56 | 0.94 |
| non-overlapping | error-calibrated, central path | 40 | 0.12 | 0.62 | 0.62 | 0.75 |
| non-overlapping | error-calibrated, centred | 10 | 0.50 | 0.80 | 0.88 | 0.90 |
| non-overlapping | error-calibrated, centred | 20 | 0.25 | 0.67 | 0.83 | 0.96 |
| non-overlapping | error-calibrated, centred | 30 | 0.31 | 0.44 | 0.69 | 0.94 |
| non-overlapping | error-calibrated, centred | 40 | 0.12 | 0.38 | 0.62 | 0.62 |
| non-overlapping | model draws (parameter uncertainty) | 10 | 0.10 | 0.12 | 0.23 | 0.30 |
| non-overlapping | model draws (parameter uncertainty) | 20 | 0.04 | 0.12 | 0.12 | 0.17 |
| non-overlapping | model draws (parameter uncertainty) | 30 | 0.06 | 0.12 | 0.12 | 0.19 |
| non-overlapping | model draws (parameter uncertainty) | 40 | 0.12 | 0.25 | 0.25 | 0.25 |
| real-time | error-calibrated | 10 | 0.44 | 0.69 | 0.84 | 0.94 |
| real-time | error-calibrated | 20 | 0.31 | 0.62 | 0.69 | 0.88 |
| real-time | error-calibrated | 30 | 0.25 | 0.25 | 0.62 | 0.75 |

## 4. Religious switching

Empirical Bayes fit, mean of 3 replicate fits: delta = -0.224, beta_d = 1.350, tau_u = 1.014; replicate standard deviations delta 0.012, beta_d 0.006, tau_u 0.025. Median posterior effective sample size 316 of 512 draws. Hyperparameter uncertainty: laplace.

| delta | beta_d | tau_u | se_delta | se_beta_d | se_log_tau_u | log_marginal | min_posterior_ess |
|---|---|---|---|---|---|---|---|
| -0.231 | 1.347 | 0.986 | 0.151 | 0.111 | 0.149 | 8734.387 | 145.363 |
| -0.210 | 1.347 | 1.033 | 0.150 | 0.113 | 0.177 | 8733.923 | 65.042 |
| -0.232 | 1.357 | 1.022 | 0.146 | 0.110 | 0.150 | 8734.220 | 88.560 |

Parametric simulation study of the estimator under the real design (run.py recovery): evidence simulated from the fitted hyperparameters, refitted; bias, RMSE, the mean Laplace standard error against the spread of the estimates, and the coverage of the 90% Laplace intervals.

| parameter | true_value | replications | bias | bias_se | rmse | sd_of_estimates | mean_laplace_se | coverage_90 |
|---|---|---|---|---|---|---|---|---|
| delta | -0.224 | 20 | -0.050 | 0.027 | 0.129 | 0.122 | 0.126 | 0.900 |
| beta_d | 1.350 | 20 | -0.015 | 0.012 | 0.053 | 0.053 | 0.070 | 1.000 |
| log_tau_u | 0.014 | 20 | -0.111 | 0.028 | 0.165 | 0.126 | 0.107 | 0.650 |
Lifetime switching levels against Pew (2025), adults 18-54 in 117 countries, left per 100 raised. Each run weights the history level and the survey level at random.

| religion | pew_left_per_100_raised_18_54 | history_level_model | survey_level_model | logit_shift | countries_with_own_survey_cells |
|---|---|---|---|---|---|
| Christianity | 17.10 | 13.31 | 17.10 | 0.39 | 27.00 |
| Islam | 1.00 | 1.53 | 1.00 | -0.44 | 2.00 |
| Hinduism | 1.00 | 1.44 | 1.00 | -0.37 | 4.00 |
| Buddhism | 22.10 | 13.30 | 22.10 | 0.98 | 5.00 |
| Judaism |  | 11.18 | 11.18 | 0.00 | 2.00 |
| Folk_Traditional |  | 12.95 | 12.95 | 0.00 | 0.00 |
| Other |  | 10.37 | 10.37 | 0.00 | 0.00 |
| Unaffiliated | 7.50 | 7.50 | 7.50 | 0.00 | 4.00 |

Highest fitted lifetime disaffiliation of people raised Christian (2020 development):

| country_id | mean | q05 | q95 | evidence |
|---|---|---|---|---|
| SVN | 0.763 | 0.447 | 0.933 | net change + hierarchical prior |
| NZL | 0.603 | 0.485 | 0.702 | net change + hierarchical prior |
| NLD | 0.544 | 0.454 | 0.643 | survey + net change |
| BEL | 0.543 | 0.446 | 0.622 | net change + hierarchical prior |
| HKG | 0.511 | 0.120 | 0.875 | net change + hierarchical prior |
| KOR | 0.458 | 0.354 | 0.554 | survey + net change |
| FIN | 0.444 | 0.335 | 0.540 | net change + hierarchical prior |
| CAN | 0.440 | 0.312 | 0.574 | survey + net change |
| AUT | 0.430 | 0.324 | 0.529 | net change + hierarchical prior |
| GBR | 0.430 | 0.336 | 0.529 | survey + net change |

## 5. Migration

Religion of migrants calibrated to Pew's published composition of migrants: destination affinity kappa = 0.4, minority effect lambda = 0.55 (bounded at 4.5 times the origin mean in the calibration; each run draws its own bound); error 2.98 pp against 5.93 pp if migrants mirrored their origin.

Realised net migration against WPP's, 2020-2100: mean relative gap 0.266 (0 with exact margins); emigrants that could not leave because a religion's cells were full: 0.20 million per run over 2020-3030.

Foreign-born share of each country in 2020, simulated from the UN 1990 stocks (no switching), against the UN 2020 stocks:

| model | popw_mae_pp | country_mae_pp | corr_with_un | world_foreign_born_millions | un_world_foreign_born_millions |
|---|---|---|---|---|---|
| migration model, circulation 0.0000/year | 1.037 | 3.270 | 0.895 | 253.919 | 252.118 |
| migration model, circulation 0.0001/year | 0.965 | 2.987 | 0.909 | 276.070 | 252.118 |
| migration model, circulation 0.0003/year | 1.056 | 3.300 | 0.910 | 299.304 | 252.118 |
| persistence (1990 foreign-born share) | 1.758 | 4.112 | 0.890 | 211.316 | 252.118 |

Corridors 1990-2020: origin mix of simulated inflows into the 25 largest destinations against the growth of UN bilateral stocks, by margin softness and corridor cap (none = the model as used).

| margin_rho | corridor_cap | destination_origin_mix_corr | destination_origin_mix_tv | largest_origin_share_simulated | largest_origin_share_observed | simulated_moves_millions | stock_growth_millions |
|---|---|---|---|---|---|---|---|
| 1.000 | none | 0.644 | 0.511 | 0.346 | 0.412 | 229.052 | 143.455 |
| 1.000 | 4.0 | 0.566 | 0.567 | 0.297 | 0.412 | 228.260 | 143.455 |
| 1.000 | 3.0 | 0.575 | 0.563 | 0.282 | 0.412 | 228.284 | 143.455 |
| 1.000 | 2.0 | 0.540 | 0.575 | 0.288 | 0.412 | 227.673 | 143.455 |
| 1.000 | 1.5 | 0.517 | 0.583 | 0.283 | 0.412 | 228.269 | 143.455 |
| 0.750 | none | 0.672 | 0.488 | 0.312 | 0.412 | 229.222 | 143.455 |
| 0.750 | 4.0 | 0.588 | 0.530 | 0.304 | 0.412 | 228.946 | 143.455 |
| 0.750 | 3.0 | 0.580 | 0.538 | 0.297 | 0.412 | 228.815 | 143.455 |
| 0.750 | 2.0 | 0.551 | 0.548 | 0.305 | 0.412 | 228.666 | 143.455 |
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
| 2050 | Buddhism | 3.1 | 2.9 | 3.2 | 2.6 | 4.7 |
| 2050 | Christianity | 27.8 | 27.5 | 28.3 | 25.7 | 29.9 |
| 2050 | Folk_Traditional | 1.3 | 1.2 | 1.3 | 0.7 | 3.9 |
| 2050 | Hinduism | 14.5 | 14.3 | 14.6 | 12.0 | 16.2 |
| 2050 | Islam | 31.7 | 31.4 | 32.1 | 29.7 | 34.2 |
| 2050 | Judaism | 0.2 | 0.2 | 0.2 | 0.1 | 0.2 |
| 2050 | Other | 0.7 | 0.7 | 0.7 | 0.6 | 3.0 |
| 2050 | Unaffiliated | 20.7 | 20.0 | 21.3 | 15.9 | 23.0 |
| 2100 | Buddhism | 1.7 | 1.5 | 1.9 | 1.4 | 3.2 |
| 2100 | Christianity | 26.1 | 25.2 | 27.4 | 22.8 | 29.3 |
| 2100 | Folk_Traditional | 1.0 | 0.9 | 1.2 | 0.5 | 4.2 |
| 2100 | Hinduism | 12.0 | 11.5 | 12.4 | 8.4 | 13.4 |
| 2100 | Islam | 39.2 | 38.1 | 40.0 | 36.6 | 43.2 |
| 2100 | Judaism | 0.2 | 0.2 | 0.3 | 0.1 | 0.3 |
| 2100 | Other | 0.5 | 0.5 | 0.6 | 0.6 | 3.2 |
| 2100 | Unaffiliated | 19.1 | 17.4 | 20.4 | 13.1 | 22.6 |

**2050, every scenario (means)**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 27.8 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.7 |
| combined_dispersal | 27.6 | 31.9 | 14.5 | 3.0 | 0.2 | 1.2 | 0.7 | 21.0 |
| continued_secularization | 27.6 | 31.7 | 14.5 | 3.0 | 0.2 | 1.2 | 0.7 | 21.0 |
| high_retention | 29.0 | 31.9 | 14.6 | 3.2 | 0.2 | 1.3 | 0.7 | 19.1 |
| low_migration | 27.8 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.7 |
| persistent_fertility_gaps | 27.8 | 31.9 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.7 |
| rising_migration | 27.8 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.7 |
| stabilising | 27.8 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.7 |

**2100, every scenario (means)**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 26.1 | 39.2 | 12.0 | 1.7 | 0.2 | 1.0 | 0.5 | 19.1 |
| combined_dispersal | 24.7 | 40.1 | 11.7 | 1.6 | 0.2 | 0.9 | 0.5 | 20.2 |
| continued_secularization | 25.0 | 38.8 | 11.8 | 1.6 | 0.2 | 1.0 | 0.5 | 20.9 |
| high_retention | 29.3 | 39.9 | 12.3 | 2.0 | 0.3 | 1.2 | 0.6 | 14.5 |
| low_migration | 26.2 | 39.1 | 12.0 | 1.7 | 0.3 | 1.0 | 0.5 | 19.2 |
| persistent_fertility_gaps | 25.8 | 40.4 | 11.8 | 1.7 | 0.3 | 1.0 | 0.5 | 18.6 |
| rising_migration | 26.1 | 39.3 | 12.0 | 1.7 | 0.2 | 1.0 | 0.5 | 19.1 |
| stabilising | 26.1 | 39.2 | 12.0 | 1.7 | 0.2 | 1.0 | 0.5 | 19.1 |

**Exploratory horizons (stated long-run assumptions; not forecasts), reference scenario**

| year | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| 2200 | 22.9 | 43.7 | 8.5 | 0.8 | 0.3 | 0.9 | 0.4 | 22.6 |
| 2500 | 21.1 | 44.1 | 5.2 | 0.4 | 0.3 | 1.0 | 0.3 | 27.6 |
| 3026 | 19.8 | 42.0 | 3.9 | 0.3 | 0.4 | 1.1 | 0.4 | 32.2 |

**Predictive medians, and the effect of centring the errors.** The intervals use the record's errors as they were; centring them (subtracting the pooled mean standardised error) is shown for comparison.

| year | religion | model_mean | pi05 | median | pi95 | centred_pi05 | centred_median | centred_pi95 |
|---|---|---|---|---|---|---|---|---|
| 2050 | Christianity | 27.8 | 25.7 | 27.5 | 29.9 | 26.3 | 28.1 | 30.6 |
| 2050 | Islam | 31.7 | 29.7 | 31.7 | 34.2 | 29.4 | 31.5 | 33.9 |
| 2050 | Hinduism | 14.5 | 12.0 | 14.3 | 16.2 | 12.3 | 14.8 | 16.8 |
| 2050 | Buddhism | 3.1 | 2.6 | 3.1 | 4.7 | 2.7 | 3.3 | 4.8 |
| 2050 | Judaism | 0.2 | 0.1 | 0.2 | 0.2 | 0.2 | 0.2 | 0.3 |
| 2050 | Folk_Traditional | 1.3 | 0.7 | 1.1 | 3.9 | 0.5 | 0.9 | 3.7 |
| 2050 | Other | 0.7 | 0.6 | 1.1 | 3.0 | 0.2 | 0.6 | 2.4 |
| 2050 | Unaffiliated | 20.7 | 15.9 | 19.9 | 23.0 | 15.4 | 19.6 | 22.8 |
| 2100 | Christianity | 26.1 | 22.8 | 25.9 | 29.3 | 23.5 | 26.8 | 30.4 |
| 2100 | Islam | 39.2 | 36.6 | 39.3 | 43.2 | 36.2 | 39.0 | 43.1 |
| 2100 | Hinduism | 12.0 | 8.4 | 11.7 | 13.4 | 8.9 | 12.3 | 14.3 |
| 2100 | Buddhism | 1.7 | 1.4 | 1.9 | 3.2 | 1.5 | 2.0 | 3.4 |
| 2100 | Judaism | 0.2 | 0.1 | 0.2 | 0.3 | 0.2 | 0.3 | 0.4 |
| 2100 | Folk_Traditional | 1.0 | 0.5 | 1.0 | 4.2 | 0.3 | 0.7 | 4.1 |
| 2100 | Other | 0.5 | 0.6 | 1.2 | 3.2 | 0.2 | 0.8 | 2.6 |
| 2100 | Unaffiliated | 19.1 | 13.1 | 17.8 | 22.6 | 12.4 | 17.2 | 22.4 |

### Three kinds of uncertainty (world shares, pp)

Run spread = mean 5-95% band inside a scenario; predictive = mean 90% predictive band (to 2100); between = range of scenario means.

| year | religion | within_scenario_band_pp_mean | predictive_band_pp_mean | between_scenario_range_pp | lowest_scenario | highest_scenario |
|---|---|---|---|---|---|---|
| 2050 | Buddhism | 0.24 | 2.08 | 0.21 | combined_dispersal | high_retention |
| 2050 | Christianity | 0.80 | 4.08 | 1.39 | combined_dispersal | high_retention |
| 2050 | Folk_Traditional | 0.11 | 3.17 | 0.10 | combined_dispersal | high_retention |
| 2050 | Hinduism | 0.30 | 4.08 | 0.11 | combined_dispersal | high_retention |
| 2050 | Islam | 0.66 | 4.48 | 0.19 | continued_secularization | high_retention |
| 2050 | Judaism | 0.02 | 0.09 | 0.01 | combined_dispersal | high_retention |
| 2050 | Other | 0.06 | 2.37 | 0.03 | combined_dispersal | high_retention |
| 2050 | Unaffiliated | 1.22 | 6.95 | 1.96 | high_retention | continued_secularization |
| 2100 | Buddhism | 0.42 | 1.80 | 0.43 | combined_dispersal | high_retention |
| 2100 | Christianity | 2.18 | 6.39 | 4.56 | combined_dispersal | high_retention |
| 2100 | Folk_Traditional | 0.21 | 3.78 | 0.24 | combined_dispersal | high_retention |
| 2100 | Hinduism | 0.89 | 5.23 | 0.57 | combined_dispersal | high_retention |
| 2100 | Islam | 1.81 | 6.72 | 1.55 | continued_secularization | persistent_fertility_gaps |
| 2100 | Judaism | 0.04 | 0.19 | 0.03 | combined_dispersal | high_retention |
| 2100 | Other | 0.15 | 2.53 | 0.11 | combined_dispersal | high_retention |
| 2100 | Unaffiliated | 2.88 | 9.58 | 6.41 | high_retention | continued_secularization |

## 7. What changes world shares, 2020-2100 (`stabilising`, pp)

The simulation's own sub-step accounting; the parts add up exactly to the total. Migration cancels worldwide.

| religion | survival | births | switching | emigration | immigration | calibration | total |
|---|---|---|---|---|---|---|---|
| Christianity | -0.73 | 3.25 | -5.26 | -0.10 | 0.10 | 0.09 | -2.64 |
| Islam | 6.12 | 9.12 | -0.53 | -0.32 | 0.32 | -1.15 | 13.56 |
| Hinduism | 0.26 | -2.22 | -0.33 | 0.38 | -0.38 | -0.66 | -2.95 |
| Buddhism | -1.04 | -1.19 | -0.38 | 0.01 | -0.01 | 0.23 | -2.39 |
| Judaism | 0.01 | -0.02 | 0.04 | 0.00 | -0.00 | 0.03 | 0.06 |
| Folk_Traditional | -0.19 | -0.21 | 0.01 | 0.00 | -0.00 | 0.03 | -0.36 |
| Other | -0.09 | -0.16 | -0.01 | -0.01 | 0.01 | -0.00 | -0.26 |
| Unaffiliated | -4.35 | -8.58 | 6.47 | 0.02 | -0.02 | 1.44 | -5.02 |

## 8. Where world-share change comes from, 2020-2100

An exact split of each religion's change in world share into countries' own shares changing and country populations growing at different rates.

| religion | change_pp | within_country_pp | population_weighting_pp | interaction_pp |
|---|---|---|---|---|
| Christianity | -2.64 | -8.89 | 6.53 | -0.28 |
| Islam | 13.56 | 3.25 | 10.29 | 0.01 |
| Hinduism | -2.95 | -0.70 | -2.37 | 0.12 |
| Buddhism | -2.39 | -1.19 | -1.69 | 0.49 |
| Judaism | 0.06 | 0.02 | 0.05 | -0.02 |
| Folk_Traditional | -0.36 | -0.06 | -0.24 | -0.06 |
| Other | -0.26 | -0.18 | -0.11 | 0.03 |
| Unaffiliated | -5.02 | 7.74 | -12.46 | -0.30 |

## 9. What each mechanism contributes

The full model minus the same run with one mechanism switched off, paired run by run on identical draws. Percentage points of world population (dominant_changed_countries is a count).

| outcome | year | demography only | fertility differences | migration | religious switching |
|---|---|---|---|---|---|
| dominant_changed_countries | 2050 | 6.92 | -0.58 | -0.42 | 6.83 |
| dominant_changed_countries | 2100 | 36.50 | -1.58 | -2.42 | 33.50 |
| world_Christianity | 2050 | -2.67 | -0.20 | -0.05 | -2.41 |
| world_Christianity | 2100 | -8.15 | -0.81 | -0.15 | -7.05 |
| world_Hinduism | 2050 | -0.25 | -0.15 | 0.03 | -0.12 |
| world_Hinduism | 2100 | -0.77 | -0.42 | 0.13 | -0.42 |
| world_Islam | 2050 | 0.66 | 0.71 | 0.06 | -0.08 |
| world_Islam | 2100 | 1.83 | 2.33 | 0.33 | -0.73 |
| world_Unaffiliated | 2050 | 2.58 | -0.27 | -0.04 | 2.82 |
| world_Unaffiliated | 2100 | 7.95 | -0.83 | -0.26 | 8.75 |

## 10. Which assumptions move the results

Standardised rank regression coefficients (top five per outcome) from a separate Monte Carlo design.


**2050**

| outcome | parameter | coefficient | model_r2 |
|---|---|---|---|
| world_Islam | psi | 0.726 | 0.766 |
| world_Christianity | survey_weight | -0.705 | 0.705 |
| world_Unaffiliated | survey_weight | 0.367 | 0.493 |
| world_Unaffiliated | delta | 0.319 | 0.493 |
| world_Islam | survey_weight | 0.299 | 0.766 |
| diversity_within_pop_weighted | survey_weight | 0.288 | 0.401 |
| world_Unaffiliated | beta_d | 0.255 | 0.493 |
| diversity_within_pop_weighted | margin_rho | 0.213 | 0.401 |
| diversity_within_pop_weighted | turnover | -0.207 | 0.401 |
| world_Christianity | beta_d | -0.201 | 0.705 |
| world_Islam | phi | 0.200 | 0.766 |
| world_Unaffiliated | psi | -0.198 | 0.493 |
| diversity_within_pop_weighted | selectivity_cap | -0.192 | 0.401 |
| diversity_within_pop_weighted | w_add | -0.177 | 0.401 |
| world_Islam | Hf | 0.168 | 0.766 |
| world_Unaffiliated | Hf | -0.161 | 0.493 |
| world_Christianity | phi_region | -0.159 | 0.705 |
| world_Christianity | w_add | 0.155 | 0.705 |
| world_Christianity | theta | -0.145 | 0.705 |
| world_Islam | phi_region | 0.144 | 0.766 |

**2100**

| outcome | parameter | coefficient | model_r2 |
|---|---|---|---|
| world_Christianity | survey_weight | -0.597 | 0.571 |
| world_Islam | Hf | 0.429 | 0.672 |
| world_Islam | survey_weight | 0.380 | 0.672 |
| world_Islam | psi | 0.344 | 0.672 |
| world_Unaffiliated | delta | 0.307 | 0.421 |
| world_Unaffiliated | beta_d | 0.290 | 0.421 |
| world_Unaffiliated | survey_weight | 0.246 | 0.421 |
| world_Unaffiliated | Hf | -0.224 | 0.421 |
| world_Islam | phi | 0.217 | 0.672 |
| diversity_within_pop_weighted | delta | 0.211 | 0.329 |
| world_Islam | margin_rho | 0.201 | 0.672 |
| diversity_within_pop_weighted | turnover | -0.200 | 0.329 |
| diversity_within_pop_weighted | phi | -0.183 | 0.329 |
| diversity_within_pop_weighted | theta | 0.176 | 0.329 |
| world_Unaffiliated | m_g1 | -0.175 | 0.421 |
| diversity_within_pop_weighted | beta_d | 0.167 | 0.329 |
| world_Christianity | phi_region | -0.155 | 0.571 |
| world_Christianity | beta_d | -0.149 | 0.571 |
| world_Christianity | delta | -0.146 | 0.571 |
| world_Christianity | w_add | 0.140 | 0.571 |

## 11. Countries whose largest religion changes

Countries where most runs change (parameter uncertainty only):

| scenario | most_runs_by_2050 | most_runs_by_2100 | most_runs_by_2200 | most_runs_by_2500 | most_runs_by_3026 |
|---|---|---|---|---|---|
| changing_migration | 7 | 32 | 66 | 109 | 124 |
| combined_dispersal | 7 | 36 | 105 | 139 | 142 |
| continued_secularization | 7 | 38 | 112 | 184 | 189 |
| high_retention | 5 | 19 | 38 | 62 | 86 |
| low_migration | 7 | 32 | 73 | 106 | 119 |
| persistent_fertility_gaps | 7 | 32 | 68 | 120 | 144 |
| rising_migration | 7 | 31 | 66 | 105 | 121 |
| stabilising | 7 | 32 | 70 | 106 | 117 |

Predictive probability of a change by 2050 and 2100 (`stabilising`), the 25 highest at 2100. 32 countries exceed 50% by 2100.

| country_id | dominant_2020 | most_likely_new_2100_predictive | prob_changed_by_2050_predictive | prob_changed_by_2100_predictive | prob_changed_by_2100 |
|---|---|---|---|---|---|
| MNG | Buddhism | Unaffiliated | 0.71 | 0.92 | 1.00 |
| SGP | Buddhism | Unaffiliated | 0.65 | 0.88 | 1.00 |
| FRA | Christianity | Unaffiliated | 0.59 | 0.86 | 1.00 |
| GBR | Christianity | Unaffiliated | 0.54 | 0.83 | 1.00 |
| TWN | Folk_Traditional | Unaffiliated | 0.41 | 0.82 | 0.82 |
| AUS | Christianity | Unaffiliated | 0.67 | 0.78 | 1.00 |
| SWE | Christianity | Unaffiliated | 0.35 | 0.76 | 1.00 |
| DEU | Christianity | Unaffiliated | 0.45 | 0.76 | 1.00 |
| BEL | Christianity | Unaffiliated | 0.59 | 0.75 | 1.00 |
| SVN | Christianity | Unaffiliated | 0.29 | 0.73 | 0.97 |
| EST | Christianity | Unaffiliated | 0.62 | 0.72 | 0.82 |
| CAN | Christianity | Unaffiliated | 0.49 | 0.71 | 1.00 |
| CHL | Christianity | Unaffiliated | 0.26 | 0.71 | 0.90 |
| FIN | Christianity | Unaffiliated | 0.22 | 0.69 | 1.00 |
| CPV | Christianity | Unaffiliated | 0.16 | 0.67 | 0.78 |
| MKD | Christianity | Islam | 0.07 | 0.67 | 0.88 |
| CHE | Christianity | Unaffiliated | 0.31 | 0.67 | 1.00 |
| LVA | Christianity | Unaffiliated | 0.13 | 0.66 | 0.82 |
| ESP | Christianity | Unaffiliated | 0.21 | 0.66 | 1.00 |
| AUT | Christianity | Unaffiliated | 0.15 | 0.63 | 1.00 |
| ECU | Christianity | Unaffiliated | 0.03 | 0.63 | 0.70 |
| DOM | Christianity | Unaffiliated | 0.12 | 0.63 | 0.70 |
| NOR | Christianity | Unaffiliated | 0.18 | 0.63 | 0.95 |
| CRI | Christianity | Unaffiliated | 0.03 | 0.61 | 0.65 |
| ARG | Christianity | Unaffiliated | 0.00 | 0.59 | 0.57 |

## 12. Does more migration make countries more mixed?

Rising minus low migration, paired by run, under three assumptions about where migrants go.

| year | variant | median | q05 | q95 | runs_more_diverse | runs |
|---|---|---|---|---|---|---|
| 2050 | calibrated | 0.0008 | 0.0007 | 0.0010 | 12 | 12 |
| 2050 | migrants mirror origin | 0.0022 | 0.0019 | 0.0027 | 12 | 12 |
| 2050 | no destination affinity | 0.0013 | 0.0011 | 0.0015 | 12 | 12 |
| 2100 | calibrated | 0.0042 | 0.0035 | 0.0049 | 12 | 12 |
| 2100 | migrants mirror origin | 0.0128 | 0.0102 | 0.0144 | 12 | 12 |
| 2100 | no destination affinity | 0.0069 | 0.0055 | 0.0074 | 12 | 12 |
| 2200 | calibrated | 0.0166 | 0.0119 | 0.0204 | 12 | 12 |
| 2200 | migrants mirror origin | 0.0433 | 0.0327 | 0.0499 | 12 | 12 |
| 2200 | no destination affinity | 0.0255 | 0.0188 | 0.0293 | 12 | 12 |
| 2500 | calibrated | 0.0363 | 0.0185 | 0.0481 | 12 | 12 |
| 2500 | migrants mirror origin | 0.0868 | 0.0630 | 0.1010 | 12 | 12 |
| 2500 | no destination affinity | 0.0571 | 0.0368 | 0.0719 | 12 | 12 |
| 3026 | calibrated | 0.0496 | 0.0175 | 0.0773 | 12 | 12 |
| 3026 | migrants mirror origin | 0.1036 | 0.0717 | 0.1257 | 12 | 12 |
| 3026 | no destination affinity | 0.0753 | 0.0437 | 0.1070 | 12 | 12 |

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
| Christianity | -0.95 | 0.24 | -1.18 | -2.35 |
| Islam | 6.08 | 4.76 | 1.32 | 0.74 |
| Hinduism | -0.44 | -0.29 | -0.14 | -0.23 |
| Buddhism | -1.06 | -1.40 | 0.34 | -2.51 |
| Judaism | 0.02 | -0.02 | 0.04 | -0.00 |
| Folk_Traditional | -0.13 | -0.79 | 0.66 | -4.22 |
| Other | -0.09 | -0.14 | 0.05 | -0.01 |
| Unaffiliated | -3.44 | -2.37 | -1.07 | 8.57 |

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
