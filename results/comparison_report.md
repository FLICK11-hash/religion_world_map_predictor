# Step 7 comparison report

Generated 2026-10-29 23:54 UTC from `data/validation/` and `data/projections/`.

## 1. Inputs used in this run

| input | status | detail |
|---|---|---|
| wpp_indicators | used | 237 countries, 1950-2100 |
| start_state | used | Pew 2010/2020 via Step 2 (201 countries in 2020, 201 in 2010) |
| wrp | used | 1730 usable country-years of 1995 |
| natural_earth | used | 242 map units |
| wpp_age | used | 200 of 200 countries, 1950-2100 (5-year points) |
| bilateral_stock | used | undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx: 68941 country pairs x years, years [np.int64(1990), np.int64(1995), np.int64(2000), np.int64(2005), np.int64(2010), np.int64(2015), np.int64(2020), np.int64(2024)] (cached parse) |
| migrant_religion | missing | no country-level Pew migrant file; religion of migrants from the affinity model calibrated to Pew published aggregates (inputs/migrant_religion_published.csv) |
| switching_survey | used | 67 verified cells, 33 countries |
| religion_fertility | used | 8 world, 5 regional (2 regions), 10 country figures (4 countries); 7 rows held back |
| unhcr | used | 138893 rows 1951-2025 |
| pew_2015_projection | missing | no external benchmark comparison |

Start state: data/processed/pew_harmonized.csv (Pew 2010 and 2020; Folk/Other split by WRP proxy). Runs per scenario: 40, seed 2026.

## 2. History tests (forward chaining; lower is better)

Population-weighted total-variation error in percentage points; negative change = better than persistence. Switching and residual weights were chosen on earlier windows only.

| scope | model | windows | popw_tv_pp | change_vs_persistence_pp | dominant_accuracy | changed_true | changed_hit | false_alarm |
|---|---|---|---|---|---|---|---|---|
| test windows 1990-2010 (WRP) | demography | 2 | 4.579 | -0.044 | 0.972 | 9 | 1 | 0 |
| test windows 1990-2010 (WRP) | demography_migration | 2 | 4.580 | -0.043 | 0.969 | 9 | 1 | 1 |
| test windows 1990-2010 (WRP) | demography_migration_momentum | 2 | 6.829 | 2.205 | 0.956 | 9 | 0 | 4 |
| test windows 1990-2010 (WRP) | demography_migration_switching | 2 | 4.580 | -0.043 | 0.969 | 9 | 1 | 1 |
| test windows 1990-2010 (WRP) | demography_migration_switching_residual | 2 | 4.580 | -0.043 | 0.969 | 9 | 1 | 1 |
| test windows 1990-2010 (WRP) | persistence | 2 | 4.623 | 0.000 | 0.969 | 9 | 0 | 0 |
| test windows 1990-2010 (WRP) | switching_strength_0.5 | 2 | 4.489 | -0.135 | 0.969 | 9 | 1 | 1 |
| test windows 1990-2010 (WRP) | switching_strength_1 | 2 | 4.487 | -0.136 | 0.969 | 9 | 1 | 1 |
| all WRP windows 1970-2010 | demography | 4 | 4.378 | -0.028 | 0.963 | 21 | 2 | 1 |
| all WRP windows 1970-2010 | demography_migration | 4 | 4.381 | -0.025 | 0.961 | 21 | 2 | 2 |
| all WRP windows 1970-2010 | demography_migration_momentum | 4 | 5.854 | 1.447 | 0.963 | 21 | 6 | 6 |
| all WRP windows 1970-2010 | demography_migration_switching | 4 | 4.570 | 0.163 | 0.963 | 21 | 3 | 2 |
| all WRP windows 1970-2010 | demography_migration_switching_residual | 4 | 4.639 | 0.233 | 0.963 | 21 | 3 | 2 |
| all WRP windows 1970-2010 | persistence | 4 | 4.406 | 0.000 | 0.961 | 21 | 0 | 0 |
| all WRP windows 1970-2010 | switching_strength_0.5 | 4 | 4.503 | 0.097 | 0.961 | 21 | 2 | 2 |
| all WRP windows 1970-2010 | switching_strength_1 | 4 | 4.797 | 0.390 | 0.963 | 21 | 3 | 2 |
| Pew 2010-2020 | demography | 1 | 3.442 | 0.002 | 0.990 | 2 | 0 | 0 |
| Pew 2010-2020 | demography_migration | 1 | 3.447 | 0.007 | 0.990 | 2 | 0 | 0 |
| Pew 2010-2020 | demography_migration_momentum | 1 | 4.501 | 1.061 | 0.985 | 2 | 1 | 2 |
| Pew 2010-2020 | demography_migration_switching | 1 | 3.447 | 0.007 | 0.990 | 2 | 0 | 0 |
| Pew 2010-2020 | demography_migration_switching_residual | 1 | 3.447 | 0.007 | 0.990 | 2 | 0 | 0 |
| Pew 2010-2020 | persistence | 1 | 3.440 | 0.000 | 0.990 | 2 | 0 | 0 |
| Pew 2010-2020 | switching_strength_0.5 | 1 | 3.325 | -0.115 | 0.990 | 2 | 0 | 0 |
| Pew 2010-2020 | switching_strength_1 | 1 | 3.255 | -0.185 | 0.985 | 2 | 0 | 1 |

### Does each new dataset improve the history tests?

| scope | data_variant | model | popw_tv_pp | change_vs_persistence_pp |
|---|---|---|---|---|
| WRP 1970-1990 | WPP indicators only (as Step 5D/5E) | demography | 4.172 | -0.017 |
| WRP 1990-2010 | WPP indicators only (as Step 5D/5E) | demography | 4.579 | -0.045 |
| Pew 2010-2020 | WPP indicators only (as Step 5D/5E) | demography | 3.450 | 0.010 |
| WRP 1970-1990 | WPP indicators only (as Step 5D/5E) | demography_migration | 4.150 | -0.040 |
| WRP 1990-2010 | WPP indicators only (as Step 5D/5E) | demography_migration | 4.606 | -0.018 |
| Pew 2010-2020 | WPP indicators only (as Step 5D/5E) | demography_migration | 3.437 | -0.003 |
| WRP 1970-1990 | + WPP age structure by sex | demography | 4.179 | -0.011 |
| WRP 1990-2010 | + WPP age structure by sex | demography | 4.582 | -0.041 |
| Pew 2010-2020 | + WPP age structure by sex | demography | 3.446 | 0.006 |
| WRP 1970-1990 | + WPP age structure by sex | demography_migration | 4.157 | -0.033 |
| WRP 1990-2010 | + WPP age structure by sex | demography_migration | 4.608 | -0.015 |
| Pew 2010-2020 | + WPP age structure by sex | demography_migration | 3.432 | -0.008 |
| WRP 1970-1990 | + UN bilateral migrant stocks | demography | 4.179 | -0.011 |
| WRP 1990-2010 | + UN bilateral migrant stocks | demography | 4.579 | -0.045 |
| Pew 2010-2020 | + UN bilateral migrant stocks | demography | 3.450 | 0.010 |
| WRP 1970-1990 | + UN bilateral migrant stocks | demography_migration | 4.157 | -0.033 |
| WRP 1990-2010 | + UN bilateral migrant stocks | demography_migration | 4.562 | -0.062 |
| Pew 2010-2020 | + UN bilateral migrant stocks | demography_migration | 3.409 | -0.031 |
| WRP 1970-1990 | + religion of migrants calibrated to Pew | demography | 4.177 | -0.013 |
| WRP 1990-2010 | + religion of migrants calibrated to Pew | demography | 4.579 | -0.044 |
| Pew 2010-2020 | + religion of migrants calibrated to Pew | demography | 3.442 | 0.002 |
| WRP 1970-1990 | + religion of migrants calibrated to Pew | demography_migration | 4.182 | -0.007 |
| WRP 1990-2010 | + religion of migrants calibrated to Pew | demography_migration | 4.580 | -0.043 |
| Pew 2010-2020 | + religion of migrants calibrated to Pew | demography_migration | 3.447 | 0.007 |

The calibrated religion of migrants uses Pew 2020 migrant data, so its effect on the 1970-2010 windows contains information from after those windows (labelled, not hidden).


Residual learner weight chosen out of sample: {'alpha': 100.0, 'weight': 0.0}.

Switching strength (multiplier on fitted rates), mean error: all four windows {'0.0': 4.194, '0.5': 4.267, '1.0': 4.488}; 1990-2010 {'0.0': 4.202, '0.5': 4.101, '1.0': 4.076}.

Forecast: switching strength fixed at 1 (config/assumptions.json, switching.strength_range), not taken from the history tests. Over all four windows no switching scores best, because the two earliest folds were fitted on only two or three noisy WRP decades (see switching_fit_by_fold.csv); on 1990-2010, where the fit had four or five decades, full strength scores best; and surveys observe switching directly. The level of switching is uncertain and enters each run through survey_level_weight.


### 2b. Are the intervals honest?

The same Monte Carlo run on historical decades: how often the observed country x religion share fell inside the model interval. A 90% interval should contain the truth 90% of the time.

| window | nominal | coverage | coverage_with_measurement_error | median_interval_width_pp |
|---|---|---|---|---|
| WRP 1980-1990 | 0.500 | 0.087 | 0.669 | 0.043 |
| WRP 1980-1990 | 0.800 | 0.162 | 0.698 | 0.080 |
| WRP 1980-1990 | 0.900 | 0.194 | 0.711 | 0.101 |
| WRP 1990-2000 | 0.500 | 0.054 | 0.671 | 0.036 |
| WRP 1990-2000 | 0.800 | 0.106 | 0.690 | 0.070 |
| WRP 1990-2000 | 0.900 | 0.134 | 0.706 | 0.087 |
| WRP 2000-2010 | 0.500 | 0.082 | 0.730 | 0.039 |
| WRP 2000-2010 | 0.800 | 0.144 | 0.755 | 0.077 |
| WRP 2000-2010 | 0.900 | 0.171 | 0.767 | 0.095 |

Out-of-sample error at a ten-year horizon, against the width the model claims. The last column is how much wider the intervals would have to be.

| religion | abs_error_median_pp | abs_error_q90_pp | model_half_width_q90_pp | widening_needed |
|---|---|---|---|---|
| Buddhism | 0.02 | 0.51 | 0.12 | 4.21 |
| Christianity | 1.71 | 7.27 | 1.88 | 3.94 |
| Folk_Traditional | 0.23 | 5.48 | 0.70 | 7.81 |
| Hinduism | 0.02 | 0.66 | 0.11 | 5.90 |
| Islam | 0.49 | 3.73 | 0.67 | 5.57 |
| Judaism | 0.01 | 0.09 | 0.03 | 3.47 |
| Other | 0.51 | 3.74 | 0.20 | 18.71 |
| Unaffiliated | 0.59 | 5.39 | 2.03 | 2.71 |

**The published 5-95%% bands are the spread of model outputs under parameter uncertainty, not forecast intervals.** Most of the forecast error is measurement variation in the sources and country-level change the model has no mechanism for. For a near-term error bar use the out-of-sample numbers above.

## 3. Religious switching

Empirical Bayes fit: delta = -0.5, beta_d (development effect, logit per unit) = 1.2, tau_u (country spread) = 0.8; median posterior effective sample size 212 of 256 (closer to the maximum = data say less about that country).

Lifetime switching levels against Pew 2025 (adults 18-54, 117 countries; left per 100 raised). Each run mixes the two model levels with a random weight.

| religion | pew_left_per_100_raised_18_54 | history_level_model | survey_level_model | logit_shift | countries_with_own_survey_cells |
|---|---|---|---|---|---|
| Christianity | 17.10 | 11.64 | 17.10 | 0.59 | 27 |
| Islam | 1.00 | 1.32 | 1.00 | -0.29 | 2 |
| Hinduism | 1.00 | 1.13 | 1.00 | -0.12 | 4 |
| Buddhism | 22.10 | 13.01 | 22.10 | 0.97 | 5 |
| Judaism |  | 11.36 | 11.36 | 0.00 | 2 |
| Folk_Traditional |  | 12.65 | 12.65 | 0.00 | 0 |
| Other |  | 8.57 | 8.57 | 0.00 | 0 |
| Unaffiliated | 7.50 | 5.98 | 7.50 | 0.27 | 4 |

Highest fitted lifetime disaffiliation of people raised Christian (history level, 2020 development):

| country_id | mean | q05 | q95 | evidence |
|---|---|---|---|---|
| NZL | 0.579 | 0.372 | 0.694 | net change + hierarchical prior |
| KOR | 0.523 | 0.523 | 0.523 | survey + net change |
| BEL | 0.516 | 0.403 | 0.598 | net change + hierarchical prior |
| NLD | 0.493 | 0.436 | 0.569 | survey + net change |
| CAN | 0.414 | 0.302 | 0.507 | survey + net change |
| SVN | 0.408 | 0.100 | 0.566 | net change + hierarchical prior |
| GBR | 0.406 | 0.303 | 0.506 | survey + net change |
| FIN | 0.404 | 0.305 | 0.485 | net change + hierarchical prior |
| AUT | 0.403 | 0.323 | 0.496 | net change + hierarchical prior |
| FRA | 0.400 | 0.296 | 0.512 | survey + net change |

## 4. Migration

Religion of migrants calibrated to Pew's published composition of migrants (19 targets): destination affinity kappa = 0.5, minority effect lambda = 0.65; error 2.21 pp versus 5.93 pp if migrants mirrored their origin.

Migration volumes against data: start from the UN 1990 foreign-born stocks, simulate 1990-2020 (WPP demography, the migration model, no switching) and compare each country's 2020 foreign-born share with the UN 2020 stocks. The circulation range in config/assumptions.json is calibrated on this test.

| model | popw_mae_pp | country_mae_pp | corr_with_un | world_foreign_born_millions | un_world_foreign_born_millions |
|---|---|---|---|---|---|
| migration model, circulation 0.0000/year | 1.044 | 3.606 | 0.903 | 198.632 | 252.118 |
| migration model, circulation 0.0002/year | 0.905 | 3.045 | 0.913 | 239.022 | 252.118 |
| migration model, circulation 0.0004/year | 0.975 | 3.205 | 0.913 | 272.197 | 252.118 |
| persistence (1990 foreign-born share) | 1.758 | 4.112 | 0.890 | 211.316 | 252.118 |

Corridors 1990-2020 by margin softness (margin_rho; 1 = WPP margins exact): origin mix of simulated inflows into the 25 largest destinations against the growth of UN bilateral stocks. The forecast draws margin_rho per run (range in config/assumptions.json).

| margin_rho | destination_origin_mix_corr | destination_origin_mix_tv | simulated_moves_millions | stock_growth_millions |
|---|---|---|---|---|
| 1.000 | 0.652 | 0.507 | 227.411 | 143.455 |
| 0.750 | 0.662 | 0.490 | 191.871 | 143.455 |
| 0.500 | 0.588 | 0.517 | 174.956 | 143.455 |

Largest simulated corridors 2020-2050 (reference scenario, persons over the period):

| origin | destination | persons |
|---|---|---|
| MEX | USA | 5570102 |
| IND | USA | 4666498 |
| PAK | GBR | 2721366 |
| PAK | USA | 2422018 |
| CHN | USA | 2406982 |
| PHL | USA | 2145293 |
| UKR | RUS | 1842197 |
| VEN | COL | 1734340 |
| BGD | IND | 1701573 |
| PAK | SAU | 1641583 |
| ZWE | ZAF | 1567721 |
| TUR | DEU | 1499792 |

## 5. World shares by scenario (%)


**2050**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 27.9 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |
| combined_dispersal | 27.7 | 31.9 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.7 |
| continued_secularization | 27.8 | 31.7 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.8 |
| high_retention | 29.1 | 31.9 | 14.6 | 3.3 | 0.2 | 1.4 | 0.7 | 18.9 |
| low_migration | 28.0 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |
| persistent_fertility_gaps | 27.9 | 31.9 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.4 |
| rising_migration | 27.9 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |
| stabilising | 27.9 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |

**2100**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 26.8 | 39.0 | 12.1 | 1.8 | 0.3 | 1.1 | 0.6 | 18.4 |
| combined_dispersal | 25.2 | 40.3 | 11.7 | 1.6 | 0.2 | 1.0 | 0.5 | 19.4 |
| continued_secularization | 25.6 | 38.7 | 12.0 | 1.7 | 0.2 | 1.1 | 0.6 | 20.1 |
| high_retention | 29.8 | 39.6 | 12.3 | 2.1 | 0.3 | 1.3 | 0.6 | 13.9 |
| low_migration | 26.8 | 39.0 | 12.1 | 1.8 | 0.3 | 1.1 | 0.6 | 18.4 |
| persistent_fertility_gaps | 26.4 | 40.5 | 11.8 | 1.7 | 0.3 | 1.1 | 0.5 | 17.7 |
| rising_migration | 26.7 | 39.1 | 12.1 | 1.8 | 0.3 | 1.1 | 0.6 | 18.3 |
| stabilising | 26.8 | 39.1 | 12.1 | 1.8 | 0.3 | 1.1 | 0.6 | 18.4 |

**2500** (speculative)

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 21.8 | 43.4 | 6.3 | 0.5 | 0.4 | 1.2 | 0.5 | 25.9 |
| combined_dispersal | 3.4 | 51.5 | 2.3 | 0.1 | 0.3 | 0.2 | 0.1 | 42.0 |
| continued_secularization | 4.3 | 27.6 | 3.9 | 0.2 | 0.5 | 0.5 | 0.3 | 62.8 |
| high_retention | 32.4 | 45.7 | 6.9 | 0.9 | 0.4 | 1.6 | 0.6 | 11.7 |
| low_migration | 21.9 | 43.7 | 6.3 | 0.5 | 0.4 | 1.2 | 0.5 | 25.5 |
| persistent_fertility_gaps | 14.7 | 70.8 | 2.8 | 0.1 | 0.3 | 0.4 | 0.1 | 10.8 |
| rising_migration | 21.7 | 41.8 | 6.2 | 0.5 | 0.4 | 1.2 | 0.4 | 27.8 |
| stabilising | 21.8 | 43.1 | 6.2 | 0.5 | 0.4 | 1.2 | 0.5 | 26.3 |

**3026** (speculative)

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 20.6 | 42.3 | 5.1 | 0.4 | 0.5 | 1.5 | 0.5 | 29.1 |
| combined_dispersal | 0.7 | 53.9 | 2.1 | 0.1 | 0.6 | 0.1 | 0.1 | 42.4 |
| continued_secularization | 0.8 | 23.7 | 4.7 | 0.2 | 1.1 | 0.3 | 0.3 | 68.8 |
| high_retention | 34.5 | 44.0 | 5.3 | 0.7 | 0.4 | 1.9 | 0.6 | 12.5 |
| low_migration | 20.7 | 43.4 | 4.9 | 0.4 | 0.5 | 1.4 | 0.6 | 28.1 |
| persistent_fertility_gaps | 7.4 | 84.9 | 1.1 | 0.1 | 0.4 | 0.2 | 0.1 | 6.0 |
| rising_migration | 20.2 | 38.2 | 4.8 | 0.4 | 0.5 | 1.5 | 0.5 | 33.9 |
| stabilising | 20.6 | 41.7 | 4.8 | 0.4 | 0.5 | 1.4 | 0.5 | 30.1 |

### Model uncertainty versus scenario uncertainty (world shares, pp)

Within = mean 5-95% band inside a scenario (parameters, switching evidence, country noise). Between = range of scenario means (assumptions).

| year | religion | within_scenario_band_pp_mean | between_scenario_range_pp | lowest_scenario | highest_scenario |
|---|---|---|---|---|---|
| 2050 | Buddhism | 0.16 | 0.24 | combined_dispersal | high_retention |
| 2050 | Christianity | 0.93 | 1.36 | combined_dispersal | high_retention |
| 2050 | Folk_Traditional | 0.17 | 0.11 | combined_dispersal | high_retention |
| 2050 | Hinduism | 0.20 | 0.11 | combined_dispersal | high_retention |
| 2050 | Islam | 0.56 | 0.23 | continued_secularization | persistent_fertility_gaps |
| 2050 | Judaism | 0.02 | 0.01 | continued_secularization | high_retention |
| 2050 | Other | 0.06 | 0.03 | combined_dispersal | high_retention |
| 2050 | Unaffiliated | 1.04 | 1.92 | high_retention | continued_secularization |
| 2100 | Buddhism | 0.27 | 0.48 | combined_dispersal | high_retention |
| 2100 | Christianity | 2.70 | 4.59 | combined_dispersal | high_retention |
| 2100 | Folk_Traditional | 0.31 | 0.28 | combined_dispersal | high_retention |
| 2100 | Hinduism | 0.66 | 0.57 | combined_dispersal | high_retention |
| 2100 | Islam | 1.62 | 1.81 | continued_secularization | persistent_fertility_gaps |
| 2100 | Judaism | 0.04 | 0.02 | combined_dispersal | high_retention |
| 2100 | Other | 0.13 | 0.12 | combined_dispersal | high_retention |
| 2100 | Unaffiliated | 2.72 | 6.20 | high_retention | continued_secularization |
| 3026 | Buddhism | 0.24 | 0.64 | persistent_fertility_gaps | high_retention |
| 3026 | Christianity | 12.88 | 33.81 | combined_dispersal | high_retention |
| 3026 | Folk_Traditional | 0.90 | 1.80 | combined_dispersal | high_retention |
| 3026 | Hinduism | 4.17 | 4.26 | persistent_fertility_gaps | high_retention |
| 3026 | Islam | 14.71 | 61.14 | continued_secularization | persistent_fertility_gaps |
| 3026 | Judaism | 0.46 | 0.71 | persistent_fertility_gaps | continued_secularization |
| 3026 | Other | 0.25 | 0.56 | persistent_fertility_gaps | high_retention |
| 3026 | Unaffiliated | 14.16 | 62.85 | persistent_fertility_gaps | continued_secularization |

## 6. What changes world shares, 2020-2100 (stabilising; percentage points)

From the simulation's sequential sub-steps (they add up exactly to the total). Migration cancels worldwide.

| religion | survival | births | switching | emigration | immigration | residual | calibration | total |
|---|---|---|---|---|---|---|---|---|
| Christianity | -0.48 | 3.36 | -4.90 | -0.12 | 0.12 | 0.00 | -0.00 | -2.01 |
| Islam | 6.38 | 8.83 | -0.36 | -0.03 | 0.03 | 0.00 | -1.46 | 13.40 |
| Hinduism | 0.27 | -2.18 | -0.27 | 0.39 | -0.39 | 0.00 | -0.68 | -2.86 |
| Buddhism | -1.07 | -1.18 | -0.35 | -0.01 | 0.01 | 0.00 | 0.27 | -2.34 |
| Judaism | 0.01 | -0.01 | 0.04 | -0.03 | 0.03 | 0.00 | 0.03 | 0.07 |
| Folk_Traditional | -0.13 | -0.19 | 0.03 | -0.03 | 0.03 | 0.00 | 0.03 | -0.25 |
| Other | -0.07 | -0.15 | 0.01 | -0.05 | 0.05 | 0.00 | 0.00 | -0.21 |
| Unaffiliated | -4.91 | -8.49 | 5.79 | -0.10 | 0.10 | 0.00 | 1.81 | -5.80 |

## 7. Countries whose dominant religion changes (most runs)

| scenario | changed_by_2050 | changed_by_2100 | changed_by_2200 | changed_by_2500 | changed_by_3026 |
|---|---|---|---|---|---|
| changing_migration | 6 | 30 | 62 | 93 | 109 |
| combined_dispersal | 6 | 36 | 94 | 137 | 142 |
| continued_secularization | 6 | 37 | 105 | 174 | 189 |
| high_retention | 4 | 17 | 31 | 45 | 65 |
| low_migration | 6 | 30 | 65 | 94 | 108 |
| persistent_fertility_gaps | 6 | 29 | 62 | 103 | 124 |
| rising_migration | 6 | 29 | 64 | 94 | 101 |
| stabilising | 6 | 30 | 64 | 95 | 108 |

## 8. Religious diversity within countries (population-weighted Gini-Simpson)

| scenario | 2020 | 2050 | 2100 | 2200 | 2500 | 3026 |
|---|---|---|---|---|---|---|
| changing_migration | 0.288 | 0.311 | 0.350 | 0.389 | 0.429 | 0.456 |
| combined_dispersal | 0.288 | 0.311 | 0.356 | 0.415 | 0.447 | 0.442 |
| continued_secularization | 0.288 | 0.312 | 0.358 | 0.429 | 0.420 | 0.391 |
| high_retention | 0.288 | 0.303 | 0.330 | 0.353 | 0.374 | 0.398 |
| low_migration | 0.288 | 0.311 | 0.350 | 0.390 | 0.430 | 0.453 |
| persistent_fertility_gaps | 0.288 | 0.311 | 0.349 | 0.372 | 0.291 | 0.173 |
| rising_migration | 0.288 | 0.311 | 0.350 | 0.391 | 0.435 | 0.460 |
| stabilising | 0.288 | 0.311 | 0.350 | 0.390 | 0.430 | 0.456 |

## 9. Against the earlier cohort model (Step 5D `demography_only`, from `data\forecasts_step5d\global_share_uncertainty.csv`)

The earlier model had no religious switching, so the gap between the two is almost entirely what switching adds.

| year | religion | earlier_model_demography_only | this_model | difference_pp |
|---|---|---|---|---|
| 2050 | Christianity | 30.65 | 27.95 | -2.70 |
| 2050 | Islam | 31.23 | 31.71 | 0.48 |
| 2050 | Hinduism | 14.68 | 14.51 | -0.17 |
| 2050 | Buddhism | 3.31 | 3.07 | -0.23 |
| 2050 | Judaism | 0.18 | 0.20 | 0.03 |
| 2050 | Folk_Traditional | 1.25 | 1.32 | 0.07 |
| 2050 | Other | 0.71 | 0.72 | 0.01 |
| 2050 | Unaffiliated | 17.99 | 20.50 | 2.51 |
| 2100 | Christianity | 34.81 | 26.76 | -8.05 |
| 2100 | Islam | 38.30 | 39.05 | 0.75 |
| 2100 | Hinduism | 12.63 | 12.08 | -0.55 |
| 2100 | Buddhism | 2.30 | 1.77 | -0.52 |
| 2100 | Judaism | 0.18 | 0.25 | 0.07 |
| 2100 | Folk_Traditional | 1.04 | 1.15 | 0.11 |
| 2100 | Other | 0.55 | 0.58 | 0.03 |
| 2100 | Unaffiliated | 10.20 | 18.36 | 8.16 |

## 10. Where world-share change comes from, 2020-2100

An exact split of each religion's change in WORLD share into countries' own shares changing and country populations growing at different rates. This is a different question from the mechanism accounting above, and for several groups the two parts point in opposite directions.

| religion | change_pp | within_country_pp | population_weighting_pp | interaction_pp |
|---|---|---|---|---|
| Christianity | -2.01 | -8.36 | 6.45 | -0.10 |
| Islam | 13.40 | 2.82 | 10.42 | 0.17 |
| Hinduism | -2.86 | -0.59 | -2.36 | 0.09 |
| Buddhism | -2.34 | -1.08 | -1.69 | 0.43 |
| Judaism | 0.07 | 0.03 | 0.05 | -0.01 |
| Folk_Traditional | -0.25 | 0.08 | -0.24 | -0.09 |
| Other | -0.21 | -0.11 | -0.11 | 0.01 |
| Unaffiliated | -5.80 | 7.20 | -12.51 | -0.49 |

## 11. What each mechanism contributes

The full model minus the same run with one mechanism switched off, paired run by run on identical draws. Percentage points of world population.

| outcome | year | demography only | fertility differences | migration | religious switching |
|---|---|---|---|---|---|
| dominant_changed_countries | 2050 | 6.83 | -0.42 | 0.00 | 6.75 |
| dominant_changed_countries | 2100 | 34.92 | -0.83 | -1.33 | 32.33 |
| world_Christianity | 2050 | -2.64 | -0.17 | -0.04 | -2.41 |
| world_Christianity | 2100 | -7.99 | -0.67 | -0.12 | -7.09 |
| world_Hinduism | 2050 | -0.23 | -0.14 | 0.03 | -0.11 |
| world_Hinduism | 2100 | -0.67 | -0.38 | 0.10 | -0.36 |
| world_Islam | 2050 | 0.65 | 0.65 | 0.04 | -0.02 |
| world_Islam | 2100 | 1.75 | 1.98 | 0.21 | -0.43 |
| world_Unaffiliated | 2050 | 2.43 | -0.24 | -0.03 | 2.66 |
| world_Unaffiliated | 2100 | 7.55 | -0.69 | -0.21 | 8.24 |

(`dominant_changed_countries` is a count, not a percentage.)


## 12. Which assumptions move the results

Standardised rank regression coefficients from a separate Monte Carlo design: how many standard deviations an outcome moves when one parameter moves by one. Top five per outcome.


**2100**

| outcome | parameter | coefficient | model_r2 |
|---|---|---|---|
| world_Christianity | survey_weight | -0.853 | 0.726 |
| world_Unaffiliated | survey_weight | 0.591 | 0.555 |
| diversity_within_pop_weighted | survey_weight | 0.517 | 0.371 |
| world_Islam | Hf | 0.504 | 0.713 |
| world_Islam | psi | 0.405 | 0.713 |
| world_Islam | survey_weight | 0.333 | 0.713 |
| world_Islam | phi_region | 0.286 | 0.713 |
| world_Unaffiliated | psi | -0.283 | 0.555 |
| diversity_within_pop_weighted | theta | -0.245 | 0.371 |
| world_Islam | margin_rho | 0.231 | 0.713 |
| diversity_within_pop_weighted | margin_rho | -0.189 | 0.371 |
| world_Christianity | theta | 0.176 | 0.726 |
| world_Christianity | e0_cap | -0.159 | 0.726 |
| world_Unaffiliated | margin_rho | -0.156 | 0.555 |
| world_Unaffiliated | lam_sel | 0.155 | 0.555 |
| diversity_within_pop_weighted | tfr_lr | 0.152 | 0.371 |
| diversity_within_pop_weighted | e0_cap | 0.144 | 0.371 |
| world_Christianity | tfr_dev_half_life | -0.140 | 0.726 |
| world_Unaffiliated | e0_cap | 0.138 | 0.555 |
| world_Christianity | Hf | -0.129 | 0.726 |

**3026**

| outcome | parameter | coefficient | model_r2 |
|---|---|---|---|
| world_Islam | survey_weight | 0.498 | 0.450 |
| world_Christianity | survey_weight | -0.395 | 0.342 |
| world_Christianity | tfr_hl | 0.263 | 0.342 |
| world_Islam | turnover | -0.261 | 0.450 |
| world_Islam | tfr_dev_half_life | 0.250 | 0.450 |
| world_Unaffiliated | theta | -0.240 | 0.246 |
| world_Christianity | theta | 0.209 | 0.342 |
| world_Unaffiliated | h2 | 0.204 | 0.246 |
| diversity_within_pop_weighted | m_g1 | 0.197 | 0.258 |
| diversity_within_pop_weighted | tfr_hl | 0.183 | 0.258 |
| world_Islam | margin_rho | -0.181 | 0.450 |
| world_Unaffiliated | psi | -0.176 | 0.246 |
| diversity_within_pop_weighted | Hf | -0.170 | 0.258 |
| world_Islam | e0_gain | 0.168 | 0.450 |
| world_Unaffiliated | tfr_hl | -0.167 | 0.246 |
| world_Unaffiliated | margin_rho | 0.150 | 0.246 |
| diversity_within_pop_weighted | phi | -0.141 | 0.258 |
| diversity_within_pop_weighted | w_add | 0.133 | 0.258 |
| world_Christianity | tfr_dev_half_life | -0.122 | 0.342 |
| world_Christianity | turnover | 0.111 | 0.342 |

## 13. Does more migration make countries more mixed?

Rising minus low migration, paired by run, under three assumptions about where migrants go. Positive means more migration leaves countries more religiously mixed.

| year | variant | median | q05 | q95 | runs_more_diverse | runs |
|---|---|---|---|---|---|---|
| 2050 | calibrated | -0.0001 | -0.0003 | 0.0000 | 3 | 12 |
| 2050 | migrants mirror origin | 0.0022 | 0.0017 | 0.0028 | 12 | 12 |
| 2050 | no destination affinity | 0.0005 | 0.0004 | 0.0007 | 12 | 12 |
| 2100 | calibrated | -0.0008 | -0.0019 | 0.0002 | 1 | 12 |
| 2100 | migrants mirror origin | 0.0126 | 0.0095 | 0.0156 | 12 | 12 |
| 2100 | no destination affinity | 0.0024 | 0.0020 | 0.0034 | 12 | 12 |
| 2200 | calibrated | 0.0020 | -0.0024 | 0.0055 | 7 | 12 |
| 2200 | migrants mirror origin | 0.0412 | 0.0324 | 0.0538 | 12 | 12 |
| 2200 | no destination affinity | 0.0125 | 0.0083 | 0.0174 | 12 | 12 |
| 2500 | calibrated | 0.0075 | -0.0060 | 0.0197 | 9 | 12 |
| 2500 | migrants mirror origin | 0.0784 | 0.0666 | 0.1060 | 12 | 12 |
| 2500 | no destination affinity | 0.0369 | 0.0200 | 0.0533 | 12 | 12 |
| 3026 | calibrated | 0.0053 | -0.0082 | 0.0347 | 8 | 12 |
| 3026 | migrants mirror origin | 0.0944 | 0.0820 | 0.1163 | 12 | 12 |
| 3026 | no destination affinity | 0.0655 | 0.0273 | 0.0905 | 12 | 12 |

## 14. How much of the fertility input is measured

Share of 2020 world population whose religion-specific fertility comes from each evidence tier.

| evidence_tier | percent_of_world_population |
|---|---|
| country | 23.7 |
| region | 20.7 |
| world | 55.5 |

## 15. What remains uncertain

- Switching levels: rates fitted to net share changes are lower than Pew 2025 survey levels for Christians and Buddhists; runs span both. History tests at decade scale cannot settle which is right.
- The religion of migrants is calibrated to aggregate Pew figures; corridor-level religion (Pew dataset, free account) would replace the calibration. Destination affinity (kappa) decides whether more migration makes countries more diverse (section 8b).
- Circulation is calibrated to foreign-born stocks, so gross churn is understated (returning emigrants count as foreign-born). UN stocks also carry legacy corridors (for example India-Pakistan from 1947) into the network.
- Group fertility gaps are damped Pew global ratios except where religion_fertility_observed.csv is supplied.
- After 2100 all demography is assumption; 2500 and 3026 are speculative scenarios, not forecasts.
- Folk/Traditional versus Other in Pew data is a WRP proxy; WRP and Pew classify much of China differently.
