# Step 7 comparison report

Generated 2026-10-25 00:35 UTC from `data/validation/` and `data/projections/`.

## 1. Inputs used in this run

| input | status | detail |
|---|---|---|
| wpp_indicators | used | 237 countries, 1950-2100 |
| start_state | fallback | results_step5 2020 start state (201 countries); Pew 2010 unavailable |
| wrp | used | 1730 usable country-years of 1995 |
| natural_earth | used | 242 map units |
| wpp_age | used | 200 of 200 countries, 1950-2100 (5-year points) |
| bilateral_stock | used | undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx: 68941 country pairs x years, years [np.int64(1990), np.int64(1995), np.int64(2000), np.int64(2005), np.int64(2010), np.int64(2015), np.int64(2020), np.int64(2024)] (cached parse) |
| migrant_religion | missing | no country-level Pew migrant file; religion of migrants from the affinity model calibrated to Pew published aggregates (inputs/migrant_religion_published.csv) |
| switching_survey | used | 67 verified cells, 33 countries |
| religion_fertility | used | 8 world, 5 regional (2 regions), 10 country figures (4 countries); 7 rows held back |
| unhcr | used | 64809 rows 2010-2022 |
| pew_2015_projection | used | 5 years, 234 countries |

Start state: results_step5/headline_country_shares.csv (Pew 2020 start state of Step 5D). Runs per scenario: 40, seed 2026.

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

### Does each new dataset improve the history tests?

| scope | data_variant | model | popw_tv_pp | change_vs_persistence_pp |
|---|---|---|---|---|
| WRP 1970-1990 | WPP indicators only (as Step 5D/5E) | demography | 4.172 | -0.017 |
| WRP 1990-2010 | WPP indicators only (as Step 5D/5E) | demography | 4.579 | -0.045 |
| WRP 1970-1990 | WPP indicators only (as Step 5D/5E) | demography_migration | 4.150 | -0.040 |
| WRP 1990-2010 | WPP indicators only (as Step 5D/5E) | demography_migration | 4.606 | -0.018 |
| WRP 1970-1990 | + WPP age structure by sex | demography | 4.179 | -0.011 |
| WRP 1990-2010 | + WPP age structure by sex | demography | 4.582 | -0.041 |
| WRP 1970-1990 | + WPP age structure by sex | demography_migration | 4.157 | -0.033 |
| WRP 1990-2010 | + WPP age structure by sex | demography_migration | 4.608 | -0.015 |
| WRP 1970-1990 | + UN bilateral migrant stocks | demography | 4.179 | -0.011 |
| WRP 1990-2010 | + UN bilateral migrant stocks | demography | 4.579 | -0.045 |
| WRP 1970-1990 | + UN bilateral migrant stocks | demography_migration | 4.157 | -0.033 |
| WRP 1990-2010 | + UN bilateral migrant stocks | demography_migration | 4.562 | -0.062 |
| WRP 1970-1990 | + religion of migrants calibrated to Pew | demography | 4.177 | -0.013 |
| WRP 1990-2010 | + religion of migrants calibrated to Pew | demography | 4.579 | -0.044 |
| WRP 1970-1990 | + religion of migrants calibrated to Pew | demography_migration | 4.182 | -0.007 |
| WRP 1990-2010 | + religion of migrants calibrated to Pew | demography_migration | 4.580 | -0.043 |

The calibrated religion of migrants uses Pew 2020 migrant data, so its effect on the 1970-2010 windows contains information from after those windows (labelled, not hidden).


Residual learner weight chosen out of sample: {'alpha': 100.0, 'weight': 0.0}.

Switching strength (multiplier on fitted rates), mean error: all four windows {'0.0': 4.381, '0.5': 4.503, '1.0': 4.797}; 1990-2010 {'0.0': 4.58, '0.5': 4.489, '1.0': 4.487}.

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


### 2c. An outside yardstick

Pew's 2015 report projected 2020; Pew's 2025 report measured it. Scoring one against the other shows how much of the apparent error in this field is data revision rather than forecasting.

| source | countries | popw_tv_pp | mean_tv_pp | median_tv_pp | largest_contributors |
|---|---|---|---|---|---|
| Pew 2015 report, projected 2020 | 171 | 10.66 | 8.18 | 5.32 | CHN 69%, VNM 6%, BRA 2%, IND 1%, NGA 1% |
| Pew 2015 report, no change from 2010 | 171 | 10.95 | 8.78 | 5.82 | CHN 67%, VNM 6%, BRA 2%, NGA 2%, IND 2% |
## 3. Religious switching

Empirical Bayes fit: delta = 0.0, beta_d (development effect, logit per unit) = 0.8, tau_u (country spread) = 0.8; median posterior effective sample size 223 of 256 (closer to the maximum = data say less about that country).

Lifetime switching levels against Pew 2025 (adults 18-54, 117 countries; left per 100 raised). Each run mixes the two model levels with a random weight.

| religion | pew_left_per_100_raised_18_54 | history_level_model | survey_level_model | logit_shift | countries_with_own_survey_cells |
|---|---|---|---|---|---|
| Christianity | 17.10 | 11.61 | 17.10 | 0.55 | 27 |
| Islam | 1.00 | 1.65 | 1.00 | -0.52 | 2 |
| Hinduism | 1.00 | 1.27 | 1.00 | -0.24 | 4 |
| Buddhism | 22.10 | 14.06 | 22.10 | 0.76 | 5 |
| Judaism |  | 11.57 | 11.57 | 0.00 | 2 |
| Folk_Traditional |  | 13.03 | 13.03 | 0.00 | 0 |
| Other |  | 9.48 | 9.48 | 0.00 | 0 |
| Unaffiliated | 7.50 | 8.09 | 7.50 | -0.09 | 4 |

Highest fitted lifetime disaffiliation of people raised Christian (history level, 2020 development):

| country_id | mean | q05 | q95 | evidence |
|---|---|---|---|---|
| ALB | 0.565 | 0.098 | 0.712 | net change + hierarchical prior |
| KOR | 0.489 | 0.489 | 0.489 | survey + net change |
| NLD | 0.484 | 0.432 | 0.526 | survey + net change |
| BLZ | 0.464 | 0.096 | 0.603 | net change + hierarchical prior |
| BEL | 0.425 | 0.318 | 0.499 | net change + hierarchical prior |
| NZL | 0.420 | 0.222 | 0.580 | net change + hierarchical prior |
| CAN | 0.414 | 0.306 | 0.498 | survey + net change |
| SWE | 0.391 | 0.339 | 0.436 | survey + net change |
| AUS | 0.364 | 0.286 | 0.426 | survey + net change |
| ESP | 0.362 | 0.308 | 0.426 | survey + net change |

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
| MEX | USA | 5570382 |
| IND | USA | 4666472 |
| PAK | GBR | 2730901 |
| PAK | USA | 2440736 |
| CHN | USA | 2406976 |
| PHL | USA | 2145916 |
| UKR | RUS | 1841712 |
| VEN | COL | 1734393 |
| BGD | IND | 1701467 |
| PAK | SAU | 1642287 |
| ZWE | ZAF | 1567410 |
| TUR | DEU | 1494846 |

## 5. World shares by scenario (%)


**2050**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 27.9 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |
| combined_dispersal | 27.7 | 31.9 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.7 |
| continued_secularization | 27.7 | 31.7 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.8 |
| high_retention | 29.1 | 31.9 | 14.6 | 3.3 | 0.2 | 1.4 | 0.7 | 18.8 |
| low_migration | 27.9 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |
| persistent_fertility_gaps | 27.9 | 31.9 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.4 |
| rising_migration | 27.9 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |
| stabilising | 27.9 | 31.7 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |

**2100**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 26.6 | 39.1 | 12.1 | 1.8 | 0.2 | 1.2 | 0.6 | 18.4 |
| combined_dispersal | 24.9 | 40.3 | 11.8 | 1.6 | 0.2 | 1.0 | 0.5 | 19.5 |
| continued_secularization | 25.3 | 38.8 | 12.1 | 1.7 | 0.2 | 1.1 | 0.6 | 20.3 |
| high_retention | 30.0 | 39.7 | 12.3 | 2.2 | 0.3 | 1.3 | 0.6 | 13.6 |
| low_migration | 26.6 | 39.0 | 12.1 | 1.8 | 0.3 | 1.2 | 0.6 | 18.4 |
| persistent_fertility_gaps | 26.2 | 40.6 | 11.9 | 1.8 | 0.3 | 1.1 | 0.5 | 17.7 |
| rising_migration | 26.5 | 39.2 | 12.2 | 1.8 | 0.2 | 1.2 | 0.6 | 18.3 |
| stabilising | 26.6 | 39.1 | 12.1 | 1.8 | 0.3 | 1.2 | 0.6 | 18.4 |

**2500** (speculative)

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 20.4 | 43.5 | 6.5 | 0.5 | 0.3 | 1.1 | 0.4 | 27.1 |
| combined_dispersal | 3.4 | 53.4 | 2.4 | 0.1 | 0.3 | 0.2 | 0.1 | 40.1 |
| continued_secularization | 4.3 | 28.3 | 4.1 | 0.2 | 0.4 | 0.4 | 0.3 | 62.0 |
| high_retention | 31.9 | 45.8 | 6.9 | 0.9 | 0.4 | 1.5 | 0.5 | 12.0 |
| low_migration | 20.5 | 43.8 | 6.4 | 0.5 | 0.3 | 1.1 | 0.4 | 26.9 |
| persistent_fertility_gaps | 14.5 | 71.4 | 2.8 | 0.1 | 0.3 | 0.3 | 0.1 | 10.4 |
| rising_migration | 20.4 | 42.1 | 6.4 | 0.5 | 0.3 | 1.1 | 0.4 | 28.7 |
| stabilising | 20.4 | 43.3 | 6.4 | 0.5 | 0.3 | 1.1 | 0.4 | 27.5 |

**3026** (speculative)

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 19.0 | 42.5 | 5.2 | 0.4 | 0.4 | 1.3 | 0.5 | 30.7 |
| combined_dispersal | 0.6 | 57.3 | 2.1 | 0.1 | 0.5 | 0.1 | 0.1 | 39.2 |
| continued_secularization | 1.0 | 24.5 | 4.5 | 0.1 | 0.9 | 0.3 | 0.3 | 68.4 |
| high_retention | 33.8 | 44.1 | 5.4 | 0.8 | 0.4 | 1.8 | 0.6 | 13.1 |
| low_migration | 18.9 | 43.5 | 5.0 | 0.4 | 0.4 | 1.3 | 0.5 | 30.0 |
| persistent_fertility_gaps | 7.2 | 85.6 | 1.0 | 0.1 | 0.4 | 0.1 | 0.1 | 5.6 |
| rising_migration | 18.9 | 38.7 | 5.0 | 0.4 | 0.5 | 1.4 | 0.5 | 34.7 |
| stabilising | 19.0 | 41.9 | 4.9 | 0.4 | 0.4 | 1.3 | 0.5 | 31.6 |

### Model uncertainty versus scenario uncertainty (world shares, pp)

Within = mean 5-95% band inside a scenario (parameters, switching evidence, country noise). Between = range of scenario means (assumptions).

| year | religion | within_scenario_band_pp_mean | between_scenario_range_pp | lowest_scenario | highest_scenario |
|---|---|---|---|---|---|
| 2050 | Buddhism | 0.26 | 0.27 | combined_dispersal | high_retention |
| 2050 | Christianity | 1.05 | 1.45 | combined_dispersal | high_retention |
| 2050 | Folk_Traditional | 0.16 | 0.12 | combined_dispersal | high_retention |
| 2050 | Hinduism | 0.23 | 0.11 | combined_dispersal | high_retention |
| 2050 | Islam | 0.56 | 0.24 | continued_secularization | persistent_fertility_gaps |
| 2050 | Judaism | 0.01 | 0.01 | continued_secularization | high_retention |
| 2050 | Other | 0.06 | 0.04 | combined_dispersal | high_retention |
| 2050 | Unaffiliated | 1.15 | 2.08 | high_retention | continued_secularization |
| 2100 | Buddhism | 0.43 | 0.53 | combined_dispersal | high_retention |
| 2100 | Christianity | 2.72 | 5.03 | combined_dispersal | high_retention |
| 2100 | Folk_Traditional | 0.27 | 0.30 | combined_dispersal | high_retention |
| 2100 | Hinduism | 0.60 | 0.51 | combined_dispersal | high_retention |
| 2100 | Islam | 1.64 | 1.83 | continued_secularization | persistent_fertility_gaps |
| 2100 | Judaism | 0.03 | 0.02 | combined_dispersal | high_retention |
| 2100 | Other | 0.13 | 0.13 | combined_dispersal | high_retention |
| 2100 | Unaffiliated | 3.01 | 6.70 | high_retention | continued_secularization |
| 3026 | Buddhism | 0.26 | 0.71 | persistent_fertility_gaps | high_retention |
| 3026 | Christianity | 10.56 | 33.21 | combined_dispersal | high_retention |
| 3026 | Folk_Traditional | 0.83 | 1.74 | combined_dispersal | high_retention |
| 3026 | Hinduism | 4.07 | 4.34 | persistent_fertility_gaps | high_retention |
| 3026 | Islam | 13.40 | 61.08 | continued_secularization | persistent_fertility_gaps |
| 3026 | Judaism | 0.41 | 0.55 | persistent_fertility_gaps | continued_secularization |
| 3026 | Other | 0.24 | 0.54 | persistent_fertility_gaps | high_retention |
| 3026 | Unaffiliated | 12.20 | 62.78 | persistent_fertility_gaps | continued_secularization |

## 6. What changes world shares, 2020-2100 (stabilising; percentage points)

From the simulation's sequential sub-steps (they add up exactly to the total). Migration cancels worldwide.

| religion | survival | births | switching | emigration | immigration | residual | calibration | total |
|---|---|---|---|---|---|---|---|---|
| Christianity | -0.49 | 3.18 | -4.92 | -0.12 | 0.12 | 0.00 | 0.02 | -2.21 |
| Islam | 6.39 | 8.82 | -0.32 | -0.04 | 0.04 | 0.00 | -1.45 | 13.44 |
| Hinduism | 0.28 | -2.17 | -0.21 | 0.39 | -0.39 | 0.00 | -0.68 | -2.79 |
| Buddhism | -1.06 | -1.19 | -0.31 | -0.01 | 0.01 | 0.00 | 0.27 | -2.29 |
| Judaism | 0.01 | -0.01 | 0.04 | -0.03 | 0.03 | 0.00 | 0.03 | 0.06 |
| Folk_Traditional | -0.12 | -0.20 | 0.06 | -0.03 | 0.03 | 0.00 | 0.03 | -0.24 |
| Other | -0.07 | -0.15 | 0.01 | -0.05 | 0.05 | 0.00 | 0.00 | -0.21 |
| Unaffiliated | -4.94 | -8.27 | 5.66 | -0.10 | 0.10 | 0.00 | 1.78 | -5.77 |

## 7. Countries whose dominant religion changes (most runs)

| scenario | changed_by_2050 | changed_by_2100 | changed_by_2200 | changed_by_2500 | changed_by_3026 |
|---|---|---|---|---|---|
| changing_migration | 6 | 24 | 62 | 102 | 121 |
| combined_dispersal | 6 | 28 | 102 | 140 | 141 |
| continued_secularization | 6 | 26 | 113 | 169 | 189 |
| high_retention | 3 | 12 | 27 | 40 | 65 |
| low_migration | 6 | 24 | 64 | 103 | 119 |
| persistent_fertility_gaps | 6 | 24 | 61 | 101 | 123 |
| rising_migration | 6 | 24 | 59 | 101 | 112 |
| stabilising | 6 | 24 | 62 | 101 | 118 |

## 8. Religious diversity within countries (population-weighted Gini-Simpson)

| scenario | 2020 | 2050 | 2100 | 2200 | 2500 | 3026 |
|---|---|---|---|---|---|---|
| changing_migration | 0.288 | 0.314 | 0.356 | 0.394 | 0.428 | 0.452 |
| combined_dispersal | 0.288 | 0.314 | 0.362 | 0.410 | 0.437 | 0.421 |
| continued_secularization | 0.288 | 0.315 | 0.364 | 0.423 | 0.416 | 0.389 |
| high_retention | 0.288 | 0.305 | 0.333 | 0.357 | 0.380 | 0.403 |
| low_migration | 0.288 | 0.314 | 0.357 | 0.395 | 0.429 | 0.450 |
| persistent_fertility_gaps | 0.288 | 0.314 | 0.355 | 0.375 | 0.288 | 0.166 |
| rising_migration | 0.288 | 0.314 | 0.356 | 0.396 | 0.435 | 0.456 |
| stabilising | 0.288 | 0.314 | 0.356 | 0.394 | 0.429 | 0.453 |

### 8b. Why migration changes diversity the way it does (`run.py experiments`)

Population-weighted within-country diversity; median of 6 runs. Every cell uses the same random draws, so differences come from the assumption alone. *calibrated*: migrants favour destinations where their religion is common (kappa) and minorities emigrate more (lambda), both fitted to Pew; *no_affinity*: kappa = 0; *mirror*: migrants have their origin's religious mix.

| year | variant | low_migration | rising_migration | stabilising |
|---|---|---|---|---|
| 2050 | calibrated | 0.318 | 0.317 | 0.318 |
| 2050 | mirror | 0.325 | 0.328 | 0.326 |
| 2050 | no_affinity | 0.320 | 0.320 | 0.320 |
| 2100 | calibrated | 0.364 | 0.362 | 0.363 |
| 2100 | mirror | 0.381 | 0.393 | 0.385 |
| 2100 | no_affinity | 0.369 | 0.372 | 0.371 |
| 2200 | calibrated | 0.404 | 0.403 | 0.403 |
| 2200 | mirror | 0.427 | 0.467 | 0.441 |
| 2200 | no_affinity | 0.411 | 0.422 | 0.415 |
| 2500 | calibrated | 0.428 | 0.427 | 0.426 |
| 2500 | mirror | 0.463 | 0.545 | 0.491 |
| 2500 | no_affinity | 0.434 | 0.475 | 0.443 |
| 3026 | calibrated | 0.429 | 0.414 | 0.422 |
| 3026 | mirror | 0.469 | 0.566 | 0.516 |
| 3026 | no_affinity | 0.428 | 0.486 | 0.429 |

Rising minus low migration, paired by run (positive = more migration, more diverse countries):

| year | variant | median | runs_above_zero | runs |
|---|---|---|---|---|
| 2050 | calibrated | -0.000 | 1 | 6 |
| 2050 | mirror | 0.002 | 6 | 6 |
| 2050 | no_affinity | 0.000 | 6 | 6 |
| 2100 | calibrated | -0.001 | 1 | 6 |
| 2100 | mirror | 0.012 | 6 | 6 |
| 2100 | no_affinity | 0.003 | 6 | 6 |
| 2200 | calibrated | -0.001 | 2 | 6 |
| 2200 | mirror | 0.041 | 6 | 6 |
| 2200 | no_affinity | 0.011 | 6 | 6 |
| 2500 | calibrated | -0.000 | 3 | 6 |
| 2500 | mirror | 0.085 | 6 | 6 |
| 2500 | no_affinity | 0.035 | 6 | 6 |
| 3026 | calibrated | -0.011 | 2 | 6 |
| 3026 | mirror | 0.093 | 6 | 6 |
| 3026 | no_affinity | 0.032 | 5 | 6 |

## 9. Against the earlier cohort model (Step 5D `demography_only`, from `results_step5/global_share_uncertainty.csv`)

The earlier model had no religious switching, so the gap between the two is almost entirely what switching adds.

| year | religion | earlier_model_demography_only | this_model | difference_pp |
|---|---|---|---|---|
| 2050 | Christianity | 30.65 | 27.91 | -2.74 |
| 2050 | Islam | 31.23 | 31.70 | 0.47 |
| 2050 | Hinduism | 14.68 | 14.52 | -0.16 |
| 2050 | Buddhism | 3.31 | 3.10 | -0.21 |
| 2050 | Judaism | 0.18 | 0.20 | 0.02 |
| 2050 | Folk_Traditional | 1.25 | 1.34 | 0.09 |
| 2050 | Other | 0.71 | 0.72 | 0.01 |
| 2050 | Unaffiliated | 17.99 | 20.50 | 2.51 |
| 2100 | Christianity | 34.81 | 26.56 | -8.25 |
| 2100 | Islam | 38.30 | 39.09 | 0.79 |
| 2100 | Hinduism | 12.63 | 12.15 | -0.48 |
| 2100 | Buddhism | 2.30 | 1.82 | -0.47 |
| 2100 | Judaism | 0.18 | 0.25 | 0.07 |
| 2100 | Folk_Traditional | 1.04 | 1.16 | 0.12 |
| 2100 | Other | 0.55 | 0.58 | 0.02 |
| 2100 | Unaffiliated | 10.20 | 18.39 | 8.19 |

## 10. Where world-share change comes from, 2020-2100

An exact split of each religion's change in WORLD share into countries' own shares changing and country populations growing at different rates. This is a different question from the mechanism accounting above, and for several groups the two parts point in opposite directions.

| religion | change_pp | within_country_pp | population_weighting_pp | interaction_pp |
|---|---|---|---|---|
| Christianity | -2.21 | -7.90 | 6.45 | -0.76 |
| Islam | 13.44 | 2.95 | 10.42 | 0.07 |
| Hinduism | -2.79 | -0.50 | -2.36 | 0.07 |
| Buddhism | -2.29 | -0.94 | -1.69 | 0.34 |
| Judaism | 0.06 | 0.03 | 0.05 | -0.02 |
| Folk_Traditional | -0.24 | 0.19 | -0.24 | -0.18 |
| Other | -0.21 | -0.10 | -0.11 | 0.00 |
| Unaffiliated | -5.77 | 6.26 | -12.51 | 0.48 |

## 11. What each mechanism contributes

The full model minus the same run with one mechanism switched off, paired run by run on identical draws. Percentage points of world population.

| outcome | year | demography only | fertility differences | migration | religious switching |
|---|---|---|---|---|---|
| dominant_changed_countries | 2050 | 6.58 | -0.50 | -0.25 | 6.50 |
| dominant_changed_countries | 2100 | 32.00 | -0.50 | -0.92 | 29.42 |
| world_Christianity | 2050 | -2.67 | -0.16 | -0.04 | -2.43 |
| world_Christianity | 2100 | -8.13 | -0.60 | -0.11 | -7.22 |
| world_Hinduism | 2050 | -0.21 | -0.15 | 0.03 | -0.08 |
| world_Hinduism | 2100 | -0.55 | -0.39 | 0.10 | -0.24 |
| world_Islam | 2050 | 0.65 | 0.65 | 0.04 | -0.02 |
| world_Islam | 2100 | 1.80 | 2.01 | 0.22 | -0.38 |
| world_Unaffiliated | 2050 | 2.39 | -0.26 | -0.04 | 2.61 |
| world_Unaffiliated | 2100 | 7.43 | -0.79 | -0.22 | 8.13 |

(`dominant_changed_countries` is a count, not a percentage.)


## 12. Which assumptions move the results

Standardised rank regression coefficients from a separate Monte Carlo design: how many standard deviations an outcome moves when one parameter moves by one. Top five per outcome.


**2100**

| outcome | parameter | coefficient | model_r2 |
|---|---|---|---|
| world_Christianity | survey_weight | -0.885 | 0.767 |
| world_Unaffiliated | survey_weight | 0.721 | 0.630 |
| world_Islam | Hf | 0.569 | 0.774 |
| world_Islam | survey_weight | 0.514 | 0.774 |
| world_Islam | psi | 0.376 | 0.774 |
| diversity_within_pop_weighted | survey_weight | 0.287 | 0.292 |
| diversity_within_pop_weighted | turnover | -0.256 | 0.292 |
| diversity_within_pop_weighted | e0_cap | 0.199 | 0.292 |
| world_Unaffiliated | tfr_dev_half_life | 0.191 | 0.630 |
| world_Unaffiliated | phi | -0.190 | 0.630 |
| diversity_within_pop_weighted | tfr_dev_half_life | 0.189 | 0.292 |
| world_Unaffiliated | Hf | -0.170 | 0.630 |
| world_Christianity | tfr_dev_half_life | -0.166 | 0.767 |
| diversity_within_pop_weighted | tfr_hl | 0.162 | 0.292 |
| world_Christianity | e0_cap | -0.157 | 0.767 |
| world_Unaffiliated | psi | -0.148 | 0.630 |
| world_Christianity | phi | 0.141 | 0.767 |
| world_Islam | m_g2 | -0.133 | 0.774 |
| world_Christianity | h1 | -0.126 | 0.767 |
| world_Islam | phi | 0.112 | 0.774 |

**3026**

| outcome | parameter | coefficient | model_r2 |
|---|---|---|---|
| world_Christianity | survey_weight | -0.521 | 0.401 |
| world_Islam | survey_weight | 0.512 | 0.491 |
| diversity_within_pop_weighted | survey_weight | -0.284 | 0.295 |
| world_Islam | turnover | -0.261 | 0.491 |
| diversity_within_pop_weighted | e0_cap | 0.225 | 0.295 |
| world_Unaffiliated | margin_rho | 0.223 | 0.193 |
| world_Islam | margin_rho | -0.215 | 0.491 |
| world_Islam | Hf | 0.210 | 0.491 |
| diversity_within_pop_weighted | Hf | -0.179 | 0.295 |
| world_Christianity | tfr_hl | 0.177 | 0.401 |
| world_Christianity | e0_cap | -0.174 | 0.401 |
| world_Islam | e0_cap | 0.158 | 0.491 |
| world_Unaffiliated | tfr_dev_half_life | 0.155 | 0.193 |
| world_Christianity | tfr_dev_half_life | -0.150 | 0.401 |
| world_Unaffiliated | e0_cap | 0.150 | 0.193 |
| diversity_within_pop_weighted | e0_gain | 0.145 | 0.295 |
| diversity_within_pop_weighted | tfr_hl | 0.145 | 0.295 |
| world_Unaffiliated | h2 | 0.139 | 0.193 |
| world_Christianity | drift_seed | 0.138 | 0.401 |
| world_Unaffiliated | h1 | 0.129 | 0.193 |

## 13. Does more migration make countries more mixed?

Rising minus low migration, paired by run, under three assumptions about where migrants go. Positive means more migration leaves countries more religiously mixed.

| year | variant | median | q05 | q95 | runs_more_diverse | runs |
|---|---|---|---|---|---|---|
| 2050 | calibrated | -0.0001 | -0.0003 | 0.0001 | 3 | 12 |
| 2050 | migrants mirror origin | 0.0022 | 0.0016 | 0.0028 | 12 | 12 |
| 2050 | no destination affinity | 0.0005 | 0.0003 | 0.0007 | 12 | 12 |
| 2100 | calibrated | -0.0010 | -0.0019 | 0.0002 | 3 | 12 |
| 2100 | migrants mirror origin | 0.0125 | 0.0090 | 0.0156 | 12 | 12 |
| 2100 | no destination affinity | 0.0026 | 0.0018 | 0.0033 | 12 | 12 |
| 2200 | calibrated | 0.0016 | -0.0027 | 0.0053 | 7 | 12 |
| 2200 | migrants mirror origin | 0.0418 | 0.0295 | 0.0538 | 12 | 12 |
| 2200 | no destination affinity | 0.0123 | 0.0073 | 0.0167 | 12 | 12 |
| 2500 | calibrated | 0.0036 | -0.0055 | 0.0170 | 7 | 12 |
| 2500 | migrants mirror origin | 0.0804 | 0.0629 | 0.1012 | 12 | 12 |
| 2500 | no destination affinity | 0.0368 | 0.0185 | 0.0547 | 12 | 12 |
| 3026 | calibrated | 0.0010 | -0.0188 | 0.0316 | 6 | 12 |
| 3026 | migrants mirror origin | 0.0949 | 0.0778 | 0.1106 | 12 | 12 |
| 3026 | no destination affinity | 0.0652 | 0.0274 | 0.0906 | 12 | 12 |

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
