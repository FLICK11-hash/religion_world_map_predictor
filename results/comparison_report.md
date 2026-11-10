# Run report

Generated 2026-11-10 11:18 UTC from `data/validation/`, `data/projections/` and `data/experiments/`. Shares are in percent; differences in percentage points (pp).

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
| WRP 1970-2010 | trend | 4 | 5.854 | 1.448 | 32.855 | 0.963 | 21 | 6 | 6 |
| WRP 1970-2010 | demography | 4 | 4.378 | -0.028 | -0.644 | 0.963 | 21 | 2 | 1 |
| WRP 1970-2010 | demography_migration | 4 | 4.381 | -0.025 | -0.574 | 0.961 | 21 | 2 | 2 |
| WRP 1970-2010 | switching_0 | 4 | 4.381 | -0.025 | -0.574 | 0.961 | 21 | 2 | 2 |
| WRP 1970-2010 | switching_0.5 | 4 | 4.557 | 0.151 | 3.427 | 0.961 | 21 | 2 | 2 |
| WRP 1970-2010 | switching_1 | 4 | 4.903 | 0.497 | 11.279 | 0.960 | 21 | 3 | 4 |
| WRP 1970-2010 | switching_selected | 4 | 4.521 | 0.114 | 2.590 | 0.963 | 21 | 3 | 2 |
| WRP 1990-2010 | persistence | 2 | 4.623 | 0.000 | 0.000 | 0.969 | 9 | 0 | 0 |
| WRP 1990-2010 | trend | 2 | 6.829 | 2.206 | 47.705 | 0.956 | 9 | 0 | 4 |
| WRP 1990-2010 | demography | 2 | 4.580 | -0.043 | -0.940 | 0.972 | 9 | 1 | 0 |
| WRP 1990-2010 | demography_migration | 2 | 4.581 | -0.043 | -0.923 | 0.969 | 9 | 1 | 1 |
| WRP 1990-2010 | switching_0 | 2 | 4.581 | -0.043 | -0.923 | 0.969 | 9 | 1 | 1 |
| WRP 1990-2010 | switching_0.5 | 2 | 4.689 | 0.065 | 1.411 | 0.969 | 9 | 1 | 1 |
| WRP 1990-2010 | switching_1 | 2 | 4.888 | 0.265 | 5.727 | 0.962 | 9 | 1 | 3 |
| WRP 1990-2010 | switching_selected | 2 | 4.581 | -0.043 | -0.923 | 0.969 | 9 | 1 | 1 |

### Country-level comparison with persistence

Population-weighted mean difference in TV error over every country-decade (negative = better), with a 95% interval from a bootstrap over countries, and the exact decade-level sign-flip test.

| scope | model | country_windows | mean_difference_pp | ci95_low_pp | ci95_high_pp | p_bootstrap | share_better | windows_better | windows | p_window |
|---|---|---|---|---|---|---|---|---|---|---|
| WRP 1970-2010 | trend | 558 | 1.710 | 1.034 | 2.254 | 0.000 | 0.380 | 0 | 4 | 0.125 |
| WRP 1970-2010 | demography | 558 | -0.023 | -0.104 | 0.064 | 0.701 | 0.459 | 2 | 4 | 0.750 |
| WRP 1970-2010 | demography_migration | 558 | -0.019 | -0.082 | 0.059 | 0.700 | 0.475 | 2 | 4 | 0.750 |
| WRP 1970-2010 | switching_0 | 558 | -0.019 | -0.082 | 0.059 | 0.700 | 0.475 | 2 | 4 | 0.750 |
| WRP 1970-2010 | switching_0.5 | 558 | 0.160 | -0.179 | 0.450 | 0.667 | 0.581 | 1 | 4 | 0.625 |
| WRP 1970-2010 | switching_1 | 558 | 0.484 | -0.191 | 1.153 | 0.490 | 0.554 | 1 | 4 | 0.375 |
| WRP 1970-2010 | switching_selected | 558 | 0.115 | -0.082 | 0.302 | 0.606 | 0.509 | 2 | 4 | 0.875 |

## 3. Forecast errors and predictive intervals

Error model e = (h/10)^beta (s(1-s) + eps)^b u, fitted on the history record: b = 0.850, beta = 0.342. Mean |standardised error| by horizon: 10 years 0.486, 20 years 0.585, 30 years 0.753, 40 years 0.767. Resampling blocks: WRP 1970-1980, WRP 1980-1990, WRP 1990-2000, WRP 2000-2010.

Leave-one-origin-out: coverage of held-out country x religion shares and interval score (lower is better), parameter-only against error-calibrated intervals.

| method | horizon | nominal | coverage | coverage_popw | interval_score_pp | median_width_pp |
|---|---|---|---|---|---|---|
| error-calibrated | 10 | 0.500 | 0.530 | 0.568 | 4.370 | 0.363 |
| error-calibrated | 10 | 0.800 | 0.801 | 0.863 | 7.500 | 1.008 |
| error-calibrated | 10 | 0.900 | 0.890 | 0.922 | 10.779 | 1.955 |
| error-calibrated | 10 | 0.950 | 0.939 | 0.966 | 15.262 | 3.442 |
| error-calibrated | 20 | 0.500 | 0.505 | 0.540 | 6.360 | 0.483 |
| error-calibrated | 20 | 0.800 | 0.815 | 0.844 | 10.172 | 1.287 |
| error-calibrated | 20 | 0.900 | 0.913 | 0.929 | 13.778 | 2.641 |
| error-calibrated | 20 | 0.950 | 0.957 | 0.969 | 17.818 | 4.698 |
| error-calibrated | 30 | 0.500 | 0.509 | 0.492 | 8.050 | 0.608 |
| error-calibrated | 30 | 0.800 | 0.822 | 0.838 | 12.874 | 1.608 |
| error-calibrated | 30 | 0.900 | 0.910 | 0.945 | 17.595 | 3.192 |
| error-calibrated | 30 | 0.950 | 0.951 | 0.964 | 21.919 | 5.275 |
| error-calibrated | 40 | 0.500 | 0.564 | 0.559 | 9.349 | 0.760 |
| error-calibrated | 40 | 0.800 | 0.842 | 0.841 | 14.260 | 1.956 |
| error-calibrated | 40 | 0.900 | 0.923 | 0.932 | 18.922 | 3.936 |
| error-calibrated | 40 | 0.950 | 0.960 | 0.952 | 22.923 | 6.598 |
| error-calibrated, centred | 10 | 0.500 | 0.491 | 0.466 | 5.490 | 0.180 |
| error-calibrated, centred | 10 | 0.800 | 0.800 | 0.815 | 8.452 | 0.836 |
| error-calibrated, centred | 10 | 0.900 | 0.898 | 0.919 | 11.535 | 1.858 |
| error-calibrated, centred | 10 | 0.950 | 0.947 | 0.953 | 15.780 | 3.405 |
| error-calibrated, centred | 20 | 0.500 | 0.455 | 0.479 | 7.326 | 0.193 |
| error-calibrated, centred | 20 | 0.800 | 0.778 | 0.813 | 10.977 | 1.102 |
| error-calibrated, centred | 20 | 0.900 | 0.896 | 0.908 | 14.414 | 2.441 |
| error-calibrated, centred | 20 | 0.950 | 0.950 | 0.951 | 18.615 | 4.476 |
| error-calibrated, centred | 30 | 0.500 | 0.453 | 0.466 | 8.645 | 0.211 |
| error-calibrated, centred | 30 | 0.800 | 0.782 | 0.803 | 13.273 | 1.227 |
| error-calibrated, centred | 30 | 0.900 | 0.896 | 0.904 | 17.648 | 2.908 |
| error-calibrated, centred | 30 | 0.950 | 0.945 | 0.943 | 21.550 | 5.167 |
| error-calibrated, centred | 40 | 0.500 | 0.487 | 0.503 | 9.996 | 0.287 |
| error-calibrated, centred | 40 | 0.800 | 0.802 | 0.802 | 14.511 | 1.463 |
| error-calibrated, centred | 40 | 0.900 | 0.908 | 0.894 | 19.063 | 3.432 |
| error-calibrated, centred | 40 | 0.950 | 0.952 | 0.918 | 23.296 | 6.229 |
| model draws (parameter uncertainty) | 10 | 0.500 | 0.090 | 0.093 | 5.078 | 0.040 |
| model draws (parameter uncertainty) | 10 | 0.800 | 0.157 | 0.153 | 11.578 | 0.075 |
| model draws (parameter uncertainty) | 10 | 0.900 | 0.187 | 0.181 | 21.779 | 0.094 |
| model draws (parameter uncertainty) | 10 | 0.950 | 0.205 | 0.209 | 41.653 | 0.109 |
| model draws (parameter uncertainty) | 20 | 0.500 | 0.096 | 0.062 | 8.157 | 0.079 |
| model draws (parameter uncertainty) | 20 | 0.800 | 0.166 | 0.144 | 18.269 | 0.144 |
| model draws (parameter uncertainty) | 20 | 0.900 | 0.199 | 0.197 | 33.719 | 0.186 |
| model draws (parameter uncertainty) | 20 | 0.950 | 0.217 | 0.214 | 63.479 | 0.217 |
| model draws (parameter uncertainty) | 30 | 0.500 | 0.085 | 0.078 | 10.714 | 0.113 |
| model draws (parameter uncertainty) | 30 | 0.800 | 0.152 | 0.117 | 23.743 | 0.213 |
| model draws (parameter uncertainty) | 30 | 0.900 | 0.188 | 0.137 | 43.440 | 0.274 |
| model draws (parameter uncertainty) | 30 | 0.950 | 0.212 | 0.168 | 81.091 | 0.313 |
| model draws (parameter uncertainty) | 40 | 0.500 | 0.088 | 0.051 | 12.508 | 0.145 |
| model draws (parameter uncertainty) | 40 | 0.800 | 0.162 | 0.090 | 27.142 | 0.280 |
| model draws (parameter uncertainty) | 40 | 0.900 | 0.194 | 0.118 | 48.947 | 0.369 |
| model draws (parameter uncertainty) | 40 | 0.950 | 0.213 | 0.160 | 90.910 | 0.409 |

World shares of the observed countries (8 religions per held-out origin and horizon): share inside the interval, by nominal level.

| method | horizon | 0.5 | 0.8 | 0.9 | 0.95 |
|---|---|---|---|---|---|
| error-calibrated | 10 | 0.59 | 0.81 | 0.91 | 0.97 |
| error-calibrated | 20 | 0.46 | 0.75 | 0.88 | 1.00 |
| error-calibrated | 30 | 0.25 | 0.81 | 0.88 | 1.00 |
| error-calibrated | 40 | 0.38 | 0.88 | 1.00 | 1.00 |
| error-calibrated, centred | 10 | 0.44 | 0.81 | 0.94 | 0.94 |
| error-calibrated, centred | 20 | 0.42 | 0.75 | 0.88 | 0.92 |
| error-calibrated, centred | 30 | 0.44 | 0.75 | 0.88 | 0.94 |
| error-calibrated, centred | 40 | 0.62 | 0.88 | 1.00 | 1.00 |
| model draws (parameter uncertainty) | 10 | 0.09 | 0.22 | 0.22 | 0.22 |
| model draws (parameter uncertainty) | 20 | 0.08 | 0.08 | 0.08 | 0.08 |
| model draws (parameter uncertainty) | 30 | 0.06 | 0.06 | 0.06 | 0.06 |
| model draws (parameter uncertainty) | 40 | 0.00 | 0.12 | 0.12 | 0.12 |

## 4. Religious switching

Empirical Bayes fit, mean of 3 replicate fits: delta = -0.053, beta_d = 1.158, tau_u = 1.610; replicate standard deviations delta 0.164, beta_d 0.005, tau_u 0.339. Median posterior effective sample size 308 of 512 draws.

Lifetime switching levels against Pew (2025), adults 18-54 in 117 countries, left per 100 raised. Each run weights the history level and the survey level at random.

| religion | pew_left_per_100_raised_18_54 | history_level_model | survey_level_model | logit_shift | countries_with_own_survey_cells |
|---|---|---|---|---|---|
| Christianity | 17.10 | 13.02 | 17.10 | 0.42 | 27.00 |
| Islam | 1.00 | 1.84 | 1.00 | -0.66 | 2.00 |
| Hinduism | 1.00 | 1.35 | 1.00 | -0.30 | 4.00 |
| Buddhism | 22.10 | 14.05 | 22.10 | 0.86 | 5.00 |
| Judaism |  | 10.94 | 10.94 | 0.00 | 2.00 |
| Folk_Traditional |  | 14.42 | 14.42 | 0.00 | 0.00 |
| Other |  | 10.57 | 10.57 | 0.00 | 0.00 |
| Unaffiliated | 7.50 | 8.46 | 7.50 | -0.15 | 4.00 |

Highest fitted lifetime disaffiliation of people raised Christian (2020 development):

| country_id | mean | q05 | q95 | evidence |
|---|---|---|---|---|
| MNG | 0.946 | 0.850 | 0.985 | net change + hierarchical prior |
| ALB | 0.793 | 0.343 | 0.999 | net change + hierarchical prior |
| SVN | 0.748 | 0.205 | 0.976 | net change + hierarchical prior |
| MDA | 0.715 | 0.349 | 0.892 | net change + hierarchical prior |
| BLZ | 0.617 | 0.358 | 0.742 | net change + hierarchical prior |
| NZL | 0.578 | 0.429 | 0.690 | net change + hierarchical prior |
| NLD | 0.536 | 0.444 | 0.627 | survey + net change |
| GEO | 0.504 | 0.099 | 0.737 | net change + hierarchical prior |
| BEL | 0.503 | 0.415 | 0.582 | net change + hierarchical prior |
| KOR | 0.502 | 0.387 | 0.570 | survey + net change |

## 5. Migration

Religion of migrants calibrated to Pew's published composition of migrants: destination affinity kappa = 0.5, minority effect lambda = 0.65; error 2.21 pp against 5.93 pp if migrants mirrored their origin.

Foreign-born share of each country in 2020, simulated from the UN 1990 stocks (no switching), against the UN 2020 stocks:

| model | popw_mae_pp | country_mae_pp | corr_with_un | world_foreign_born_millions | un_world_foreign_born_millions |
|---|---|---|---|---|---|
| migration model, circulation 0.0000/year | 1.031 | 3.569 | 0.904 | 199.895 | 252.118 |
| migration model, circulation 0.0002/year | 0.905 | 3.024 | 0.914 | 240.239 | 252.118 |
| migration model, circulation 0.0004/year | 0.978 | 3.199 | 0.914 | 273.375 | 252.118 |
| persistence (1990 foreign-born share) | 1.758 | 4.112 | 0.890 | 211.316 | 252.118 |

Corridors 1990-2020: origin mix of simulated inflows into the 25 largest destinations against the growth of UN bilateral stocks, by margin softness and corridor cap (none = the model as used).

| margin_rho | corridor_cap | destination_origin_mix_corr | destination_origin_mix_tv | largest_origin_share_simulated | largest_origin_share_observed | simulated_moves_millions | stock_growth_millions |
|---|---|---|---|---|---|---|---|
| 1.000 | none | 0.652 | 0.507 | 0.341 | 0.412 | 227.415 | 143.455 |
| 1.000 | 3.0 | 0.568 | 0.559 | 0.277 | 0.412 | 227.339 | 143.455 |
| 1.000 | 2.0 | 0.532 | 0.568 | 0.295 | 0.412 | 225.462 | 143.455 |
| 0.750 | none | 0.662 | 0.490 | 0.308 | 0.412 | 191.871 | 143.455 |
| 0.750 | 3.0 | 0.574 | 0.534 | 0.300 | 0.412 | 191.265 | 143.455 |
| 0.750 | 2.0 | 0.565 | 0.540 | 0.306 | 0.412 | 190.666 | 143.455 |
| 0.500 | none | 0.588 | 0.517 | 0.296 | 0.412 | 174.954 | 143.455 |
| 0.500 | 3.0 | 0.555 | 0.541 | 0.301 | 0.412 | 174.741 | 143.455 |
| 0.500 | 2.0 | 0.544 | 0.545 | 0.307 | 0.412 | 174.621 | 143.455 |

Largest single origin of each main destination's simulated arrivals, 2020-2050 (reference), against that origin's share of the destination's 2020 migrant stock:

| scenario | destination | arrivals_2020_2050_millions | largest_origin | origin_share_of_arrivals | origin_share_of_2020_stock | ratio |
|---|---|---|---|---|---|---|
| stabilising | USA | 33.33 | MEX | 0.17 | 0.25 | 0.68 |
| stabilising | GBR | 8.40 | PAK | 0.33 | 0.08 | 3.94 |
| stabilising | CAN | 7.73 | IND | 0.16 | 0.11 | 1.51 |
| stabilising | RUS | 6.58 | UKR | 0.28 | 0.25 | 1.12 |
| stabilising | DEU | 6.06 | TUR | 0.25 | 0.12 | 2.08 |
| stabilising | SAU | 5.39 | PAK | 0.30 | 0.14 | 2.11 |
| stabilising | AUS | 4.74 | IND | 0.16 | 0.09 | 1.77 |
| stabilising | ZAF | 4.47 | ZWE | 0.35 | 0.38 | 0.91 |
| stabilising | MYS | 4.30 | IDN | 0.29 | 0.49 | 0.60 |
| stabilising | FRA | 4.06 | DZA | 0.19 | 0.18 | 1.03 |
| stabilising | ARE | 3.38 | IND | 0.31 | 0.41 | 0.76 |
| stabilising | JPN | 3.20 | CHN | 0.30 | 0.28 | 1.08 |
| stabilising | ESP | 3.11 | MAR | 0.15 | 0.13 | 1.13 |
| stabilising | SYR | 3.07 | PSE | 0.19 | 0.74 | 0.25 |
| stabilising | IND | 3.06 | BGD | 0.56 | 0.54 | 1.03 |

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
| 2050 | Buddhism | 3.1 | 2.9 | 3.2 | 2.7 | 5.0 |
| 2050 | Christianity | 27.7 | 27.2 | 28.3 | 25.4 | 29.9 |
| 2050 | Folk_Traditional | 1.3 | 1.3 | 1.4 | 0.7 | 4.2 |
| 2050 | Hinduism | 14.5 | 14.3 | 14.6 | 10.2 | 17.0 |
| 2050 | Islam | 31.6 | 31.4 | 31.9 | 29.5 | 34.1 |
| 2050 | Judaism | 0.2 | 0.2 | 0.2 | 0.1 | 0.2 |
| 2050 | Other | 0.7 | 0.7 | 0.8 | 0.6 | 3.6 |
| 2050 | Unaffiliated | 20.8 | 20.1 | 21.3 | 16.4 | 21.6 |
| 2100 | Buddhism | 1.8 | 1.5 | 2.0 | 1.5 | 3.6 |
| 2100 | Christianity | 25.8 | 24.0 | 27.2 | 22.3 | 29.3 |
| 2100 | Folk_Traditional | 1.1 | 1.0 | 1.2 | 0.6 | 6.8 |
| 2100 | Hinduism | 12.1 | 11.3 | 12.5 | 8.1 | 13.4 |
| 2100 | Islam | 38.7 | 37.7 | 39.6 | 36.5 | 42.5 |
| 2100 | Judaism | 0.3 | 0.3 | 0.3 | 0.2 | 0.4 |
| 2100 | Other | 0.6 | 0.5 | 0.6 | 0.6 | 3.8 |
| 2100 | Unaffiliated | 19.6 | 18.3 | 21.7 | 12.5 | 21.1 |

**2050, every scenario (means)**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 27.7 | 31.6 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.8 |
| combined_dispersal | 27.5 | 31.8 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 21.0 |
| continued_secularization | 27.5 | 31.6 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 21.1 |
| high_retention | 29.0 | 31.8 | 14.6 | 3.3 | 0.2 | 1.4 | 0.7 | 19.0 |
| low_migration | 27.7 | 31.6 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.8 |
| persistent_fertility_gaps | 27.7 | 31.8 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.7 |
| rising_migration | 27.7 | 31.6 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.8 |
| stabilising | 27.7 | 31.6 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.8 |

**2100, every scenario (means)**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 25.8 | 38.7 | 12.1 | 1.8 | 0.3 | 1.1 | 0.6 | 19.6 |
| combined_dispersal | 24.4 | 39.9 | 11.7 | 1.6 | 0.3 | 1.0 | 0.5 | 20.6 |
| continued_secularization | 24.7 | 38.3 | 12.0 | 1.7 | 0.3 | 1.0 | 0.6 | 21.5 |
| high_retention | 29.2 | 39.5 | 12.3 | 2.1 | 0.3 | 1.3 | 0.6 | 14.8 |
| low_migration | 25.8 | 38.6 | 12.1 | 1.8 | 0.3 | 1.1 | 0.6 | 19.7 |
| persistent_fertility_gaps | 25.5 | 40.2 | 11.8 | 1.7 | 0.3 | 1.1 | 0.5 | 18.9 |
| rising_migration | 25.8 | 38.8 | 12.1 | 1.8 | 0.3 | 1.1 | 0.6 | 19.6 |
| stabilising | 25.8 | 38.7 | 12.1 | 1.8 | 0.3 | 1.1 | 0.6 | 19.6 |

**Exploratory horizons (stated long-run assumptions; not forecasts), reference scenario**

| year | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| 2200 | 22.3 | 42.2 | 9.0 | 0.9 | 0.3 | 1.0 | 0.4 | 23.9 |
| 2500 | 19.6 | 42.1 | 6.3 | 0.5 | 0.4 | 1.0 | 0.4 | 29.6 |
| 3026 | 18.2 | 40.8 | 5.0 | 0.4 | 0.5 | 1.2 | 0.5 | 33.5 |

**Predictive medians, and the effect of centring the errors.** The intervals use the record's errors as they were; centring them (subtracting the pooled mean standardised error) is shown for comparison.

| year | religion | model_mean | pi05 | median | pi95 | centred_pi05 | centred_median | centred_pi95 |
|---|---|---|---|---|---|---|---|---|
| 2050 | Christianity | 27.7 | 25.4 | 27.6 | 29.9 | 27.2 | 29.7 | 32.2 |
| 2050 | Islam | 31.6 | 29.5 | 31.8 | 34.1 | 28.4 | 30.4 | 32.9 |
| 2050 | Hinduism | 14.5 | 10.2 | 14.3 | 17.0 | 10.8 | 15.5 | 17.4 |
| 2050 | Buddhism | 3.1 | 2.7 | 3.4 | 5.0 | 2.7 | 3.6 | 5.3 |
| 2050 | Judaism | 0.2 | 0.1 | 0.2 | 0.2 | 0.2 | 0.2 | 0.3 |
| 2050 | Folk_Traditional | 1.3 | 0.7 | 1.3 | 4.2 | 0.2 | 0.6 | 3.7 |
| 2050 | Other | 0.7 | 0.6 | 1.3 | 3.6 | 0.2 | 0.6 | 2.8 |
| 2050 | Unaffiliated | 20.8 | 16.4 | 19.5 | 21.6 | 15.4 | 18.8 | 21.0 |
| 2100 | Christianity | 25.8 | 22.3 | 25.9 | 29.3 | 24.5 | 28.9 | 32.7 |
| 2100 | Islam | 38.7 | 36.5 | 39.2 | 42.5 | 34.3 | 37.3 | 41.0 |
| 2100 | Hinduism | 12.1 | 8.1 | 11.8 | 13.4 | 8.6 | 13.1 | 15.0 |
| 2100 | Buddhism | 1.8 | 1.5 | 2.1 | 3.6 | 1.6 | 2.3 | 4.0 |
| 2100 | Judaism | 0.3 | 0.2 | 0.2 | 0.4 | 0.2 | 0.3 | 0.5 |
| 2100 | Folk_Traditional | 1.1 | 0.6 | 1.2 | 6.8 | 0.1 | 0.5 | 6.5 |
| 2100 | Other | 0.6 | 0.6 | 1.4 | 3.8 | 0.3 | 0.9 | 3.4 |
| 2100 | Unaffiliated | 19.6 | 12.5 | 17.1 | 21.1 | 10.6 | 15.5 | 20.1 |

### Three kinds of uncertainty (world shares, pp)

Run spread = mean 5-95% band inside a scenario; predictive = mean 90% predictive band (to 2100); between = range of scenario means.

| year | religion | within_scenario_band_pp_mean | predictive_band_pp_mean | between_scenario_range_pp | lowest_scenario | highest_scenario |
|---|---|---|---|---|---|---|
| 2050 | Buddhism | 0.30 | 2.39 | 0.24 | combined_dispersal | high_retention |
| 2050 | Christianity | 1.10 | 4.42 | 1.46 | combined_dispersal | high_retention |
| 2050 | Folk_Traditional | 0.14 | 3.54 | 0.12 | combined_dispersal | high_retention |
| 2050 | Hinduism | 0.37 | 6.79 | 0.11 | combined_dispersal | high_retention |
| 2050 | Islam | 0.53 | 4.60 | 0.24 | continued_secularization | persistent_fertility_gaps |
| 2050 | Judaism | 0.02 | 0.11 | 0.01 | combined_dispersal | high_retention |
| 2050 | Other | 0.08 | 3.01 | 0.04 | combined_dispersal | high_retention |
| 2050 | Unaffiliated | 1.21 | 5.38 | 2.09 | high_retention | continued_secularization |
| 2100 | Buddhism | 0.51 | 2.10 | 0.49 | combined_dispersal | high_retention |
| 2100 | Christianity | 3.10 | 7.04 | 4.78 | combined_dispersal | high_retention |
| 2100 | Folk_Traditional | 0.23 | 5.53 | 0.28 | combined_dispersal | high_retention |
| 2100 | Hinduism | 1.16 | 5.45 | 0.55 | combined_dispersal | high_retention |
| 2100 | Islam | 1.79 | 6.14 | 1.89 | continued_secularization | persistent_fertility_gaps |
| 2100 | Judaism | 0.04 | 0.22 | 0.02 | combined_dispersal | high_retention |
| 2100 | Other | 0.17 | 3.06 | 0.12 | combined_dispersal | high_retention |
| 2100 | Unaffiliated | 3.29 | 8.56 | 6.72 | high_retention | continued_secularization |

## 7. What changes world shares, 2020-2100 (`stabilising`, pp)

The simulation's own sub-step accounting; the parts add up exactly to the total. Migration cancels worldwide.

| religion | survival | births | switching | emigration | immigration | calibration | total |
|---|---|---|---|---|---|---|---|
| Christianity | -0.79 | 3.08 | -5.37 | -0.12 | 0.12 | 0.14 | -2.94 |
| Islam | 5.97 | 8.84 | -0.58 | -0.04 | 0.04 | -1.19 | 13.04 |
| Hinduism | 0.27 | -2.18 | -0.28 | 0.38 | -0.38 | -0.67 | -2.86 |
| Buddhism | -1.02 | -1.21 | -0.32 | -0.01 | 0.01 | 0.24 | -2.31 |
| Judaism | 0.02 | -0.02 | 0.05 | -0.03 | 0.03 | 0.03 | 0.09 |
| Folk_Traditional | -0.12 | -0.21 | 0.02 | -0.03 | 0.03 | 0.03 | -0.28 |
| Other | -0.07 | -0.15 | 0.01 | -0.05 | 0.05 | 0.00 | -0.21 |
| Unaffiliated | -4.26 | -8.15 | 6.47 | -0.09 | 0.09 | 1.42 | -4.52 |

## 8. Where world-share change comes from, 2020-2100

An exact split of each religion's change in world share into countries' own shares changing and country populations growing at different rates.

| religion | change_pp | within_country_pp | population_weighting_pp | interaction_pp |
|---|---|---|---|---|
| Christianity | -2.94 | -8.46 | 6.45 | -0.92 |
| Islam | 13.03 | 2.66 | 10.42 | -0.04 |
| Hinduism | -2.86 | -0.59 | -2.36 | 0.08 |
| Buddhism | -2.31 | -0.93 | -1.69 | 0.30 |
| Judaism | 0.09 | 0.05 | 0.05 | -0.02 |
| Folk_Traditional | -0.28 | 0.14 | -0.24 | -0.17 |
| Other | -0.21 | -0.11 | -0.11 | 0.01 |
| Unaffiliated | -4.52 | 7.23 | -12.51 | 0.76 |

## 9. What each mechanism contributes

The full model minus the same run with one mechanism switched off, paired run by run on identical draws. Percentage points of world population (dominant_changed_countries is a count).

| outcome | year | demography only | fertility differences | migration | religious switching |
|---|---|---|---|---|---|
| dominant_changed_countries | 2050 | 6.42 | -0.42 | -0.17 | 6.33 |
| dominant_changed_countries | 2100 | 43.75 | -0.67 | -1.67 | 41.17 |
| world_Christianity | 2050 | -2.89 | -0.17 | -0.04 | -2.65 |
| world_Christianity | 2100 | -9.01 | -0.62 | -0.11 | -8.10 |
| world_Hinduism | 2050 | -0.22 | -0.14 | 0.03 | -0.10 |
| world_Hinduism | 2100 | -0.61 | -0.37 | 0.10 | -0.31 |
| world_Islam | 2050 | 0.60 | 0.65 | 0.04 | -0.07 |
| world_Islam | 2100 | 1.47 | 1.97 | 0.23 | -0.69 |
| world_Unaffiliated | 2050 | 2.71 | -0.25 | -0.03 | 2.93 |
| world_Unaffiliated | 2100 | 8.79 | -0.76 | -0.22 | 9.47 |

## 10. Which assumptions move the results

Standardised rank regression coefficients (top five per outcome) from a separate Monte Carlo design.


**2050**

| outcome | parameter | coefficient | model_r2 |
|---|---|---|---|
| world_Christianity | survey_weight | -0.781 | 0.662 |
| world_Islam | psi | 0.705 | 0.722 |
| diversity_within_pop_weighted | survey_weight | 0.503 | 0.402 |
| world_Unaffiliated | survey_weight | 0.407 | 0.377 |
| world_Unaffiliated | psi | -0.345 | 0.377 |
| world_Islam | survey_weight | 0.339 | 0.722 |
| diversity_within_pop_weighted | phi | -0.284 | 0.402 |
| diversity_within_pop_weighted | h2 | -0.206 | 0.402 |
| world_Islam | phi | 0.172 | 0.722 |
| diversity_within_pop_weighted | tfr_lr | 0.150 | 0.402 |
| world_Unaffiliated | phi | -0.149 | 0.377 |
| world_Christianity | phi | 0.140 | 0.662 |
| world_Christianity | tfr_dev_half_life | -0.135 | 0.662 |
| world_Unaffiliated | e0_cap | 0.127 | 0.377 |
| diversity_within_pop_weighted | tfr_hl | -0.126 | 0.402 |
| world_Christianity | w_add | 0.124 | 0.662 |
| world_Christianity | m_g2 | 0.116 | 0.662 |
| world_Islam | Hf | 0.114 | 0.722 |
| world_Unaffiliated | lam_sel | -0.106 | 0.377 |
| world_Islam | phi_region | 0.099 | 0.722 |

**2100**

| outcome | parameter | coefficient | model_r2 |
|---|---|---|---|
| world_Christianity | survey_weight | -0.605 | 0.424 |
| world_Islam | survey_weight | 0.400 | 0.580 |
| world_Islam | Hf | 0.354 | 0.580 |
| world_Islam | psi | 0.333 | 0.580 |
| world_Unaffiliated | survey_weight | 0.287 | 0.211 |
| diversity_within_pop_weighted | phi | -0.252 | 0.261 |
| world_Unaffiliated | phi | -0.218 | 0.211 |
| diversity_within_pop_weighted | survey_weight | 0.212 | 0.261 |
| diversity_within_pop_weighted | h2 | -0.202 | 0.261 |
| diversity_within_pop_weighted | phi_region | 0.172 | 0.261 |
| diversity_within_pop_weighted | tfr_lr | 0.168 | 0.261 |
| world_Unaffiliated | psi | -0.163 | 0.211 |
| world_Islam | phi | 0.158 | 0.580 |
| world_Unaffiliated | w_add | -0.154 | 0.211 |
| world_Christianity | phi | 0.150 | 0.424 |
| world_Christianity | phi_region | -0.142 | 0.424 |
| world_Unaffiliated | h2 | -0.140 | 0.211 |
| world_Christianity | tfr_dev_half_life | -0.135 | 0.424 |
| world_Islam | h2 | 0.134 | 0.580 |
| world_Christianity | w_add | 0.132 | 0.424 |

## 11. Countries whose largest religion changes

Countries where most runs change (parameter uncertainty only):

| scenario | most_runs_by_2050 | most_runs_by_2100 | most_runs_by_2200 | most_runs_by_2500 | most_runs_by_3026 |
|---|---|---|---|---|---|
| changing_migration | 7 | 31 | 75 | 107 | 115 |
| combined_dispersal | 7 | 36 | 102 | 137 | 142 |
| continued_secularization | 7 | 40 | 113 | 176 | 188 |
| high_retention | 5 | 24 | 36 | 52 | 76 |
| low_migration | 7 | 30 | 76 | 104 | 118 |
| persistent_fertility_gaps | 7 | 33 | 76 | 110 | 124 |
| rising_migration | 7 | 31 | 75 | 102 | 114 |
| stabilising | 7 | 30 | 76 | 102 | 116 |

Predictive probability of a change by 2050 and 2100 (`stabilising`), the 25 highest at 2100. 27 countries exceed 50% by 2100.

| country_id | dominant_2020 | most_likely_new_2100_predictive | prob_changed_by_2050_predictive | prob_changed_by_2100_predictive | prob_changed_by_2100 |
|---|---|---|---|---|---|
| MNG | Buddhism | Unaffiliated | 0.71 | 0.92 | 1.00 |
| SGP | Buddhism | Unaffiliated | 0.62 | 0.85 | 1.00 |
| TWN | Folk_Traditional | Unaffiliated | 0.37 | 0.80 | 0.85 |
| FRA | Christianity | Unaffiliated | 0.54 | 0.78 | 1.00 |
| AUS | Christianity | Unaffiliated | 0.62 | 0.78 | 1.00 |
| GBR | Christianity | Unaffiliated | 0.56 | 0.75 | 1.00 |
| SVN | Christianity | Unaffiliated | 0.20 | 0.74 | 0.93 |
| BLZ | Christianity | Unaffiliated | 0.22 | 0.72 | 0.97 |
| BEL | Christianity | Unaffiliated | 0.54 | 0.71 | 1.00 |
| DEU | Christianity | Unaffiliated | 0.36 | 0.69 | 1.00 |
| FIN | Christianity | Unaffiliated | 0.15 | 0.69 | 1.00 |
| MDA | Christianity | Unaffiliated | 0.00 | 0.69 | 1.00 |
| EST | Christianity | Unaffiliated | 0.54 | 0.69 | 0.72 |
| SLV | Christianity | Unaffiliated | 0.11 | 0.69 | 0.95 |
| CHL | Christianity | Unaffiliated | 0.16 | 0.67 | 0.93 |
| NIC | Christianity | Unaffiliated | 0.10 | 0.67 | 0.95 |
| SWE | Christianity | Unaffiliated | 0.20 | 0.67 | 1.00 |
| CAN | Christianity | Unaffiliated | 0.40 | 0.67 | 1.00 |
| MKD | Christianity | Islam | 0.06 | 0.66 | 0.93 |
| CHE | Christianity | Unaffiliated | 0.18 | 0.65 | 1.00 |
| ESP | Christianity | Unaffiliated | 0.12 | 0.63 | 1.00 |
| CRI | Christianity | Unaffiliated | 0.06 | 0.62 | 0.78 |
| AUT | Christianity | Unaffiliated | 0.09 | 0.61 | 1.00 |
| ARG | Christianity | Unaffiliated | 0.02 | 0.58 | 0.65 |
| GEO | Christianity | Unaffiliated | 0.02 | 0.58 | 0.90 |

## 12. Does more migration make countries more mixed?

Rising minus low migration, paired by run, under three assumptions about where migrants go.

| year | variant | median | q05 | q95 | runs_more_diverse | runs |
|---|---|---|---|---|---|---|
| 2050 | calibrated | -0.0001 | -0.0003 | 0.0001 | 3 | 12 |
| 2050 | migrants mirror origin | 0.0022 | 0.0016 | 0.0028 | 12 | 12 |
| 2050 | no destination affinity | 0.0005 | 0.0003 | 0.0007 | 12 | 12 |
| 2100 | calibrated | -0.0003 | -0.0017 | 0.0007 | 5 | 12 |
| 2100 | migrants mirror origin | 0.0125 | 0.0091 | 0.0153 | 12 | 12 |
| 2100 | no destination affinity | 0.0028 | 0.0018 | 0.0039 | 12 | 12 |
| 2200 | calibrated | 0.0047 | -0.0023 | 0.0079 | 10 | 12 |
| 2200 | migrants mirror origin | 0.0434 | 0.0310 | 0.0523 | 12 | 12 |
| 2200 | no destination affinity | 0.0144 | 0.0089 | 0.0193 | 12 | 12 |
| 2500 | calibrated | 0.0133 | -0.0059 | 0.0211 | 10 | 12 |
| 2500 | migrants mirror origin | 0.0957 | 0.0703 | 0.1098 | 12 | 12 |
| 2500 | no destination affinity | 0.0491 | 0.0227 | 0.0589 | 12 | 12 |
| 3026 | calibrated | 0.0184 | -0.0177 | 0.0333 | 9 | 12 |
| 3026 | migrants mirror origin | 0.1055 | 0.0845 | 0.1321 | 12 | 12 |
| 3026 | no destination affinity | 0.0804 | 0.0219 | 0.1007 | 12 | 12 |

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
| Christianity | -1.03 | 0.24 | -1.27 | -2.35 |
| Islam | 5.99 | 4.76 | 1.23 | 0.74 |
| Hinduism | -0.43 | -0.29 | -0.14 | -0.23 |
| Buddhism | -1.02 | -1.40 | 0.38 | -2.51 |
| Judaism | 0.02 | -0.02 | 0.04 | -0.00 |
| Folk_Traditional | -0.07 | -0.79 | 0.71 | -4.22 |
| Other | -0.07 | -0.14 | 0.07 | -0.01 |
| Unaffiliated | -3.40 | -2.37 | -1.03 | 8.57 |

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
