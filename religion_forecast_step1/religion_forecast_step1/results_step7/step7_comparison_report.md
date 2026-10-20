# Step 7 comparison report

Generated 2026-10-20 07:59 UTC from `data/validation_step7/` and `data/forecasts_step7/`.

## 1. Inputs used in this run

| input | status | detail |
|---|---|---|
| wpp_indicators | used | 237 countries, 1950-2100 |
| start_state | fallback | results_step5 2020 start state (201 countries); Pew 2010 unavailable |
| wrp | used | 1730 usable country-years of 1995 |
| natural_earth | used | 242 map units |
| wpp_age | used | 200 of 200 countries, 1950-2100 (5-year points) |
| bilateral_stock | used | undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx: 68941 country pairs x years, years [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024] |
| migrant_religion | missing | no country-level Pew migrant file; religion of migrants from the affinity model calibrated to Pew published aggregates (step7_inputs/migrant_religion_published.csv) |
| switching_survey | used | 67 verified cells, 33 countries |
| religion_fertility | missing | within-country gaps from damped Pew global ratios (assumption) |
| unhcr | used | 64809 rows 2010-2022 |

Start state: results_step5/headline_country_shares.csv (Pew 2020 start state of Step 5D). Runs per scenario: 40, seed 2026.

## 2. History tests (forward chaining; lower is better)

Population-weighted total-variation error in percentage points; negative change = better than persistence. Switching and residual weights were chosen on earlier windows only.

| scope | model | windows | popw_tv_pp | change_vs_persistence_pp | dominant_accuracy | changed_true | changed_hit | false_alarm |
|---|---|---|---|---|---|---|---|---|
| test windows 1990-2010 (WRP) | demography | 2 | 4.549 | -0.075 | 0.972 | 9 | 1 | 0 |
| test windows 1990-2010 (WRP) | demography_migration | 2 | 4.550 | -0.073 | 0.969 | 9 | 1 | 1 |
| test windows 1990-2010 (WRP) | demography_migration_momentum | 2 | 6.822 | 2.199 | 0.956 | 9 | 0 | 4 |
| test windows 1990-2010 (WRP) | demography_migration_switching | 2 | 4.550 | -0.073 | 0.969 | 9 | 1 | 1 |
| test windows 1990-2010 (WRP) | demography_migration_switching_residual | 2 | 4.550 | -0.073 | 0.969 | 9 | 1 | 1 |
| test windows 1990-2010 (WRP) | persistence | 2 | 4.623 | 0.000 | 0.969 | 9 | 0 | 0 |
| test windows 1990-2010 (WRP) | switching_strength_0.5 | 2 | 4.453 | -0.170 | 0.969 | 9 | 1 | 1 |
| test windows 1990-2010 (WRP) | switching_strength_1 | 2 | 4.449 | -0.175 | 0.969 | 9 | 1 | 1 |
| all WRP windows 1970-2010 | demography | 4 | 4.354 | -0.052 | 0.965 | 21 | 3 | 1 |
| all WRP windows 1970-2010 | demography_migration | 4 | 4.355 | -0.051 | 0.963 | 21 | 3 | 2 |
| all WRP windows 1970-2010 | demography_migration_momentum | 4 | 5.846 | 1.440 | 0.961 | 21 | 6 | 7 |
| all WRP windows 1970-2010 | demography_migration_switching | 4 | 4.506 | 0.099 | 0.966 | 21 | 4 | 2 |
| all WRP windows 1970-2010 | demography_migration_switching_residual | 4 | 4.569 | 0.163 | 0.967 | 21 | 5 | 2 |
| all WRP windows 1970-2010 | persistence | 4 | 4.406 | 0.000 | 0.961 | 21 | 0 | 0 |
| all WRP windows 1970-2010 | switching_strength_0.5 | 4 | 4.436 | 0.030 | 0.963 | 21 | 3 | 2 |
| all WRP windows 1970-2010 | switching_strength_1 | 4 | 4.694 | 0.287 | 0.966 | 21 | 4 | 2 |

### Does each new dataset improve the history tests?

| scope | data_variant | model | popw_tv_pp | change_vs_persistence_pp |
|---|---|---|---|---|
| WRP 1970-1990 | WPP indicators only (as Step 5D/5E) | demography | 4.156 | -0.033 |
| WRP 1990-2010 | WPP indicators only (as Step 5D/5E) | demography | 4.551 | -0.072 |
| WRP 1970-1990 | WPP indicators only (as Step 5D/5E) | demography_migration | 4.121 | -0.068 |
| WRP 1990-2010 | WPP indicators only (as Step 5D/5E) | demography_migration | 4.577 | -0.046 |
| WRP 1970-1990 | + WPP age structure by sex | demography | 4.162 | -0.027 |
| WRP 1990-2010 | + WPP age structure by sex | demography | 4.553 | -0.070 |
| WRP 1970-1990 | + WPP age structure by sex | demography_migration | 4.128 | -0.062 |
| WRP 1990-2010 | + WPP age structure by sex | demography_migration | 4.578 | -0.045 |
| WRP 1970-1990 | + UN bilateral migrant stocks | demography | 4.162 | -0.027 |
| WRP 1990-2010 | + UN bilateral migrant stocks | demography | 4.548 | -0.076 |
| WRP 1970-1990 | + UN bilateral migrant stocks | demography_migration | 4.128 | -0.062 |
| WRP 1990-2010 | + UN bilateral migrant stocks | demography_migration | 4.529 | -0.095 |
| WRP 1970-1990 | + religion of migrants calibrated to Pew | demography | 4.160 | -0.030 |
| WRP 1990-2010 | + religion of migrants calibrated to Pew | demography | 4.549 | -0.075 |
| WRP 1970-1990 | + religion of migrants calibrated to Pew | demography_migration | 4.161 | -0.029 |
| WRP 1990-2010 | + religion of migrants calibrated to Pew | demography_migration | 4.550 | -0.073 |

The calibrated religion of migrants uses Pew 2020 migrant data, so its effect on the 1970-2010 windows contains information from after those windows (labelled, not hidden).


Residual learner weight chosen out of sample: {'alpha': 100.0, 'weight': 0.0}.

Switching strength (multiplier on fitted rates), mean error: all four windows {'0.0': 4.355, '0.5': 4.436, '1.0': 4.694}; 1990-2010 {'0.0': 4.55, '0.5': 4.453, '1.0': 4.449}.

Forecast: switching strength fixed at 1 (step7_assumptions.json, switching.strength_range), not taken from the history tests. Over all four windows no switching scores best, because the two earliest folds were fitted on only two or three noisy WRP decades (see switching_fit_by_fold.csv); on 1990-2010, where the fit had four or five decades, full strength scores best; and surveys observe switching directly. The level of switching is uncertain and enters each run through survey_level_weight.

## 3. Religious switching

Empirical Bayes fit: delta = 0.0, beta_d (development effect, logit per unit) = 0.8, tau_u (country spread) = 0.8; median posterior effective sample size 222 of 256 (closer to the maximum = data say less about that country).

Lifetime switching levels against Pew 2025 (adults 18-54, 117 countries; left per 100 raised). Each run mixes the two model levels with a random weight.

| religion | pew_left_per_100_raised_18_54 | history_level_model | survey_level_model | logit_shift | countries_with_own_survey_cells |
|---|---|---|---|---|---|
| Christianity | 17.10 | 11.67 | 17.10 | 0.55 | 27 |
| Islam | 1.00 | 1.66 | 1.00 | -0.53 | 2 |
| Hinduism | 1.00 | 1.29 | 1.00 | -0.26 | 4 |
| Buddhism | 22.10 | 14.09 | 22.10 | 0.75 | 5 |
| Judaism |  | 11.60 | 11.60 | 0.00 | 2 |
| Folk_Traditional |  | 13.05 | 13.05 | 0.00 | 0 |
| Other |  | 9.54 | 9.54 | 0.00 | 0 |
| Unaffiliated | 7.50 | 8.11 | 7.50 | -0.09 | 4 |

Highest fitted lifetime disaffiliation of people raised Christian (history level, 2020 development):

| country_id | mean | q05 | q95 | evidence |
|---|---|---|---|---|
| ALB | 0.598 | 0.116 | 0.712 | net change + hierarchical prior |
| KOR | 0.489 | 0.489 | 0.489 | survey + net change |
| NLD | 0.486 | 0.432 | 0.526 | survey + net change |
| BLZ | 0.464 | 0.094 | 0.603 | net change + hierarchical prior |
| BEL | 0.430 | 0.324 | 0.501 | net change + hierarchical prior |
| NZL | 0.420 | 0.224 | 0.580 | net change + hierarchical prior |
| CAN | 0.413 | 0.299 | 0.498 | survey + net change |
| SWE | 0.391 | 0.339 | 0.436 | survey + net change |
| AUS | 0.364 | 0.286 | 0.438 | survey + net change |
| ESP | 0.364 | 0.313 | 0.426 | survey + net change |

## 4. Migration

Religion of migrants calibrated to Pew's published composition of migrants (19 targets): destination affinity kappa = 0.5, minority effect lambda = 0.65; error 2.21 pp versus 5.93 pp if migrants mirrored their origin.

Migration volumes against data: start from the UN 1990 foreign-born stocks, simulate 1990-2020 (WPP demography, the migration model, no switching) and compare each country's 2020 foreign-born share with the UN 2020 stocks. The circulation range in step7_assumptions.json is calibrated on this test.

| model | popw_mae_pp | country_mae_pp | corr_with_un | world_foreign_born_millions | un_world_foreign_born_millions |
|---|---|---|---|---|---|
| migration model, circulation 0.0000/year | 1.044 | 3.607 | 0.903 | 198.616 | 252.118 |
| migration model, circulation 0.0002/year | 0.905 | 3.046 | 0.913 | 238.990 | 252.118 |
| migration model, circulation 0.0004/year | 0.976 | 3.206 | 0.913 | 272.150 | 252.118 |
| persistence (1990 foreign-born share) | 1.758 | 4.112 | 0.890 | 211.316 | 252.118 |

Corridors 1990-2020 by margin softness (margin_rho; 1 = WPP margins exact): origin mix of simulated inflows into the 25 largest destinations against the growth of UN bilateral stocks. The forecast draws margin_rho per run (range in step7_assumptions.json).

| margin_rho | destination_origin_mix_corr | destination_origin_mix_tv | simulated_moves_millions | stock_growth_millions |
|---|---|---|---|---|
| 1.000 | 0.651 | 0.507 | 227.384 | 143.455 |
| 0.750 | 0.662 | 0.490 | 191.854 | 143.455 |
| 0.500 | 0.588 | 0.517 | 174.945 | 143.455 |

Largest simulated corridors 2020-2050 (reference scenario, persons over the period):

| origin | destination | persons |
|---|---|---|
| MEX | USA | 5623488 |
| IND | USA | 4466899 |
| PAK | GBR | 2607009 |
| CHN | USA | 2347188 |
| PAK | USA | 2321066 |
| PHL | USA | 2101532 |
| UKR | RUS | 1812168 |
| BGD | IND | 1722036 |
| VEN | COL | 1704929 |
| PAK | SAU | 1648844 |
| ZWE | ZAF | 1536556 |
| TUR | DEU | 1461877 |

## 5. World shares by scenario (%)


**2050**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 28.2 | 31.4 | 14.6 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |
| combined_dispersal | 28.1 | 31.5 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.8 |
| continued_secularization | 28.0 | 31.3 | 14.5 | 3.0 | 0.2 | 1.3 | 0.7 | 20.9 |
| high_retention | 29.4 | 31.5 | 14.6 | 3.3 | 0.2 | 1.4 | 0.7 | 18.8 |
| low_migration | 28.2 | 31.4 | 14.6 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |
| persistent_fertility_gaps | 28.3 | 31.5 | 14.5 | 3.1 | 0.2 | 1.3 | 0.7 | 20.4 |
| rising_migration | 28.2 | 31.4 | 14.6 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |
| stabilising | 28.2 | 31.4 | 14.6 | 3.1 | 0.2 | 1.3 | 0.7 | 20.5 |

**2100**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 27.4 | 38.1 | 12.2 | 1.8 | 0.2 | 1.1 | 0.6 | 18.6 |
| combined_dispersal | 26.3 | 38.7 | 12.0 | 1.6 | 0.2 | 1.0 | 0.5 | 19.6 |
| continued_secularization | 26.0 | 37.8 | 12.1 | 1.7 | 0.2 | 1.1 | 0.5 | 20.6 |
| high_retention | 30.9 | 38.7 | 12.4 | 2.2 | 0.3 | 1.3 | 0.6 | 13.7 |
| low_migration | 27.4 | 38.0 | 12.2 | 1.8 | 0.2 | 1.1 | 0.6 | 18.6 |
| persistent_fertility_gaps | 27.7 | 39.0 | 12.0 | 1.8 | 0.2 | 1.0 | 0.5 | 17.8 |
| rising_migration | 27.3 | 38.1 | 12.3 | 1.8 | 0.2 | 1.1 | 0.6 | 18.5 |
| stabilising | 27.4 | 38.1 | 12.2 | 1.8 | 0.2 | 1.1 | 0.6 | 18.6 |

**2500** (speculative)

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 20.7 | 41.9 | 7.5 | 0.5 | 0.3 | 1.1 | 0.4 | 27.5 |
| combined_dispersal | 5.1 | 48.1 | 3.7 | 0.1 | 0.3 | 0.2 | 0.1 | 42.4 |
| continued_secularization | 4.0 | 27.4 | 4.8 | 0.2 | 0.4 | 0.4 | 0.3 | 62.5 |
| high_retention | 32.7 | 44.1 | 8.0 | 1.0 | 0.3 | 1.4 | 0.5 | 12.0 |
| low_migration | 20.7 | 42.2 | 7.4 | 0.5 | 0.3 | 1.1 | 0.4 | 27.3 |
| persistent_fertility_gaps | 21.8 | 61.6 | 4.5 | 0.2 | 0.2 | 0.3 | 0.1 | 11.4 |
| rising_migration | 20.7 | 40.6 | 7.3 | 0.6 | 0.3 | 1.1 | 0.4 | 29.0 |
| stabilising | 20.7 | 41.8 | 7.3 | 0.5 | 0.3 | 1.1 | 0.4 | 27.8 |

**3026** (speculative)

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk_Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| changing_migration | 18.8 | 41.0 | 7.5 | 0.4 | 0.4 | 1.2 | 0.5 | 30.1 |
| combined_dispersal | 1.3 | 54.0 | 3.7 | 0.1 | 0.5 | 0.1 | 0.1 | 40.2 |
| continued_secularization | 0.7 | 24.5 | 5.3 | 0.1 | 0.9 | 0.3 | 0.3 | 67.9 |
| high_retention | 34.1 | 42.3 | 7.6 | 0.9 | 0.4 | 1.7 | 0.6 | 12.5 |
| low_migration | 18.3 | 42.8 | 6.8 | 0.4 | 0.4 | 1.2 | 0.5 | 29.5 |
| persistent_fertility_gaps | 16.3 | 73.0 | 3.6 | 0.1 | 0.2 | 0.1 | 0.1 | 6.6 |
| rising_migration | 19.6 | 37.0 | 7.3 | 0.5 | 0.4 | 1.3 | 0.4 | 33.6 |
| stabilising | 18.8 | 41.0 | 7.0 | 0.4 | 0.4 | 1.2 | 0.5 | 30.7 |

### Model uncertainty versus scenario uncertainty (world shares, pp)

Within = mean 5-95% band inside a scenario (parameters, switching evidence, country noise). Between = range of scenario means (assumptions).

| year | religion | within_scenario_band_pp_mean | between_scenario_range_pp | lowest_scenario | highest_scenario |
|---|---|---|---|---|---|
| 2050 | Buddhism | 0.28 | 0.26 | combined_dispersal | high_retention |
| 2050 | Christianity | 1.08 | 1.43 | continued_secularization | high_retention |
| 2050 | Folk_Traditional | 0.14 | 0.12 | combined_dispersal | high_retention |
| 2050 | Hinduism | 0.37 | 0.10 | combined_dispersal | high_retention |
| 2050 | Islam | 0.76 | 0.19 | continued_secularization | high_retention |
| 2050 | Judaism | 0.02 | 0.01 | combined_dispersal | high_retention |
| 2050 | Other | 0.06 | 0.04 | combined_dispersal | high_retention |
| 2050 | Unaffiliated | 1.29 | 2.09 | high_retention | continued_secularization |
| 2100 | Buddhism | 0.44 | 0.53 | combined_dispersal | high_retention |
| 2100 | Christianity | 3.29 | 4.88 | continued_secularization | high_retention |
| 2100 | Folk_Traditional | 0.25 | 0.30 | combined_dispersal | high_retention |
| 2100 | Hinduism | 1.09 | 0.46 | combined_dispersal | high_retention |
| 2100 | Islam | 2.32 | 1.21 | continued_secularization | persistent_fertility_gaps |
| 2100 | Judaism | 0.03 | 0.02 | combined_dispersal | high_retention |
| 2100 | Other | 0.12 | 0.13 | combined_dispersal | high_retention |
| 2100 | Unaffiliated | 3.22 | 6.88 | high_retention | continued_secularization |
| 3026 | Buddhism | 0.71 | 0.82 | persistent_fertility_gaps | high_retention |
| 3026 | Christianity | 23.65 | 33.35 | continued_secularization | high_retention |
| 3026 | Folk_Traditional | 1.50 | 1.63 | combined_dispersal | high_retention |
| 3026 | Hinduism | 22.89 | 4.01 | persistent_fertility_gaps | high_retention |
| 3026 | Islam | 35.28 | 48.58 | continued_secularization | persistent_fertility_gaps |
| 3026 | Judaism | 0.65 | 0.68 | persistent_fertility_gaps | continued_secularization |
| 3026 | Other | 0.51 | 0.46 | persistent_fertility_gaps | high_retention |
| 3026 | Unaffiliated | 15.87 | 61.35 | persistent_fertility_gaps | continued_secularization |

## 6. What changes world shares, 2020-2100 (stabilising; percentage points)

From the simulation's sequential sub-steps (they add up exactly to the total). Migration cancels worldwide.

| religion | survival | births | switching | emigration | immigration | residual | calibration | total |
|---|---|---|---|---|---|---|---|---|
| Christianity | -0.22 | 3.92 | -5.11 | -0.12 | 0.12 | 0.00 | 0.01 | -1.40 |
| Islam | 6.09 | 8.13 | -0.34 | -0.03 | 0.03 | 0.00 | -1.44 | 12.44 |
| Hinduism | 0.32 | -2.12 | -0.22 | 0.39 | -0.39 | 0.00 | -0.69 | -2.70 |
| Buddhism | -1.06 | -1.17 | -0.35 | -0.01 | 0.01 | 0.00 | 0.27 | -2.31 |
| Judaism | 0.01 | -0.02 | 0.04 | -0.03 | 0.03 | 0.00 | 0.03 | 0.06 |
| Folk_Traditional | -0.14 | -0.22 | 0.05 | -0.03 | 0.03 | 0.00 | 0.04 | -0.28 |
| Other | -0.08 | -0.16 | 0.01 | -0.05 | 0.05 | 0.00 | 0.00 | -0.22 |
| Unaffiliated | -4.93 | -8.36 | 5.92 | -0.10 | 0.10 | 0.00 | 1.78 | -5.59 |

## 7. Countries whose dominant religion changes (most runs)

| scenario | changed_by_2050 | changed_by_2100 | changed_by_2200 | changed_by_2500 | changed_by_3026 |
|---|---|---|---|---|---|
| changing_migration | 6 | 23 | 62 | 96 | 122 |
| combined_dispersal | 6 | 25 | 90 | 137 | 142 |
| continued_secularization | 6 | 27 | 112 | 165 | 188 |
| high_retention | 1 | 12 | 22 | 39 | 67 |
| low_migration | 6 | 23 | 64 | 104 | 118 |
| persistent_fertility_gaps | 6 | 21 | 49 | 97 | 118 |
| rising_migration | 6 | 23 | 61 | 97 | 118 |
| stabilising | 6 | 23 | 62 | 97 | 121 |

## 8. Religious diversity within countries (population-weighted Gini-Simpson)

| scenario | 2020 | 2050 | 2100 | 2200 | 2500 | 3026 |
|---|---|---|---|---|---|---|
| changing_migration | 0.288 | 0.314 | 0.358 | 0.399 | 0.434 | 0.458 |
| combined_dispersal | 0.288 | 0.314 | 0.365 | 0.427 | 0.450 | 0.431 |
| continued_secularization | 0.288 | 0.314 | 0.366 | 0.429 | 0.416 | 0.398 |
| high_retention | 0.288 | 0.304 | 0.333 | 0.359 | 0.380 | 0.398 |
| low_migration | 0.288 | 0.314 | 0.358 | 0.400 | 0.436 | 0.452 |
| persistent_fertility_gaps | 0.288 | 0.314 | 0.357 | 0.388 | 0.327 | 0.240 |
| rising_migration | 0.288 | 0.314 | 0.357 | 0.400 | 0.439 | 0.465 |
| stabilising | 0.288 | 0.314 | 0.358 | 0.399 | 0.435 | 0.456 |

### 8b. Why migration changes diversity the way it does (`step7_sensitivity.py`)

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

## 9. Step 7 versus Step 5D (headline `demography_only`, from `results_step5/global_share_uncertainty.csv`)

| year | religion | step5d_demography_only | step7_reference | difference_pp |
|---|---|---|---|---|
| 2050 | Christianity | 30.65 | 28.21 | -2.44 |
| 2050 | Islam | 31.23 | 31.38 | 0.15 |
| 2050 | Hinduism | 14.68 | 14.55 | -0.13 |
| 2050 | Buddhism | 3.31 | 3.09 | -0.22 |
| 2050 | Judaism | 0.18 | 0.20 | 0.02 |
| 2050 | Folk_Traditional | 1.25 | 1.33 | 0.07 |
| 2050 | Other | 0.71 | 0.71 | 0.01 |
| 2050 | Unaffiliated | 17.99 | 20.53 | 2.54 |
| 2100 | Christianity | 34.81 | 27.37 | -7.44 |
| 2100 | Islam | 38.30 | 38.09 | -0.21 |
| 2100 | Hinduism | 12.63 | 12.23 | -0.39 |
| 2100 | Buddhism | 2.30 | 1.81 | -0.49 |
| 2100 | Judaism | 0.18 | 0.25 | 0.06 |
| 2100 | Folk_Traditional | 1.04 | 1.12 | 0.09 |
| 2100 | Other | 0.55 | 0.57 | 0.01 |
| 2100 | Unaffiliated | 10.20 | 18.57 | 8.38 |

## 10. What remains uncertain

- Switching levels: rates fitted to net share changes are lower than Pew 2025 survey levels for Christians and Buddhists; runs span both. History tests at decade scale cannot settle which is right.
- The religion of migrants is calibrated to aggregate Pew figures; corridor-level religion (Pew dataset, free account) would replace the calibration. Destination affinity (kappa) decides whether more migration makes countries more diverse (section 8b).
- Circulation is calibrated to foreign-born stocks, so gross churn is understated (returning emigrants count as foreign-born). UN stocks also carry legacy corridors (for example India-Pakistan from 1947) into the network.
- Group fertility gaps are damped Pew global ratios except where religion_fertility_observed.csv is supplied.
- After 2100 all demography is assumption; 2500 and 3026 are speculative scenarios, not forecasts.
- Folk/Traditional versus Other in Pew data is a WRP proxy; WRP and Pew classify much of China differently.
