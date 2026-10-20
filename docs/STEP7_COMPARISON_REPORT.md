# Step 7 comparison report (build run)

This page interprets the Step 7 run made in the build environment on 2026-10-20: 200 countries, 8 scenarios × 40 runs, seed 2026. Every number comes from these files:
- `religion_forecast_step1/religion_forecast_step1/results_step7/`: tracked copies of the run's outputs, with the complete generated tables in `results_step7/step7_comparison_report.md`;
- `data/forecasts_step7/` and `data/validation_step7/` on the machine that ran it (git-ignored).

To regenerate everything on your machine, see `README_STEP7.md`. The tables will differ somewhat, because your machine has data this run did not have (section 2).

## Summary

- **History tests:** every mechanistic model beats "nothing changes" only slightly, by 0.05-0.18 points on an error of about 4.5. Switching helps most on the recent decades. Migration is about neutral. The machine-learned residual never helped, so it is off. Extrapolating recent change is far worse than any model.
- **Migration is checked against migrant stocks:**
  - Simulating 1990-2020 from the UN 1990 stocks reproduces the UN 2020 foreign-born shares (error 0.91 points; persistence 1.76). This test set the circulation rate.
  - The flow fit is softened where WPP's projected margins conflict with the migrant network. The softness that best reproduces 1990-2020 corridors is used as the centre of its range.
- **Reference scenario (stabilising), world shares with 5-95% of 40 runs:**

  | Year | Christians | Muslims | Unaffiliated | Hindus |
  |---|---|---|---|---|
  | 2050 | 28.2% (27.7-28.8) | 31.4% (30.9-31.7) | 20.5% (19.9-21.2) | 14.6% |
  | 2100 | 27.4% (25.7-29.1) | 38.1% (36.8-39.0) | 18.6% (16.9-20.1) | 12.2% |

- **Compared with Step 5D (demography only)**, Christians are 7.4 points lower in 2100 and the unaffiliated 8.4 points higher. This is religious switching, which Step 5D did not have.
- **Dominant religion:** it changes by 2100 in 23 countries in the reference (12 under high retention, 27 under continued secularization). Almost all of these are Christian to unaffiliated, in Europe, Oceania, Canada and parts of Latin America. The USA is a toss-up: Christian 44%, unaffiliated 44%, Christian-largest in 52% of runs.
- **After 2100, scenario assumptions dominate.** By 3026 the unaffiliated range from 7% (persistent fertility gaps) to 68% (continued secularization). 2500 and 3026 are speculative scenarios, not forecasts.
- **Diversity within countries rises to 2100 in every scenario** (population-weighted Gini-Simpson 0.288 to about 0.36), mostly through switching. Whether more migration adds diversity depends on who migrates where. With the destination affinity seen in today's migrant stocks, it adds almost none.
- **Main gaps:**
  - No country data on fertility by religion. This makes Israel's Jewish share fall, probably wrongly.
  - The Pew 2010-2020 window was not available in this run.
  - The religion of migrants is calibrated on aggregates only.


## 1. What Step 7 adds to Steps 5D, 5E and 6

| Mechanism | Step 5D/5E | Step 7 |
|---|---|---|
| Births and deaths | Cohort model, national WPP fertility and mortality, fertility gaps by religion | Same, plus WPP age pyramids by sex. Life tables are fitted to WPP life expectancy and under-5 mortality. Generations: natives, foreign-born, second generation. |
| Religious switching | none (5D); an aggregate scenario term (5E) | Age-specific transition matrices from lifetime survey matrices. A hierarchical empirical-Bayes model by country and religion, fitted to net share changes and 67 survey cells in 33 countries. Development link. Generation intensities. |
| Migration | WPP net migration, religion of the destination | Gross origin-destination flows fitted to WPP net migration to 2100, softened where WPP's projected margins conflict with the migrant network. UN bilateral migrant stocks plus gravity for the pattern. Circulation is scaled by each country's observed mobility and calibrated to UN foreign-born stocks. The religion of migrants comes from a corridor model calibrated to Pew. People leave one country and arrive in another, so totals are conserved exactly. |
| Accounting | Shares only | Persons and share points by mechanism, per country, period and scenario. Taken from the simulation itself; they add up exactly. |
| Horizon | 2050/2100 | 2020-3030, with 2050, 2100, 2200, 2500 and 3026 reported; 2500 and 3026 are labelled speculative |
| Uncertainty | Monte Carlo over parameters | The same, plus posterior switching draws per country, and a split of model uncertainty from scenario uncertainty, with the same random draws in every scenario |

## 2. Inputs this run had, and what it lacked

| Input | Status | Detail |
|---|---|---|
| WPP 2024 indicators | used | 237 countries, 1950-2100 |
| WPP 2024 population by age and sex | used | 200 of 200 countries, 1950-2100 |
| UN DESA International Migrant Stock 2024 (origin × destination) | used | 68,941 country pairs × years, 1990-2024 |
| World Religion Project | used | 1,730 usable country-years |
| Survey switching cells | used | 67 cells, 33 countries (22 transcribed from the 2014 US Religious Landscape Study, 22 from Pew page text, 23 from news reports of Pew figures) |
| Pew published migrant and switching aggregates | used | `step7_inputs/` (with citations) |
| UNHCR refugee statistics | loaded | Refugees are already in the UN stocks and WPP net migration, so they are not a separate component |
| **Pew 2010-2020 country file** | **fallback** | Step 2 was not run here, so the 2020 start state is Step 5D's export and the Pew 2010-2020 window is neither fitted nor tested |
| **Pew country-level religion of migrants** | **missing** | Free Pew account needed; the corridor model is calibrated to Pew's published aggregates instead |
| **Fertility by religion within countries** | **missing** | No verified rows (the web search budget ran out before NFHS-5, Israel CBS or DHS figures could be checked). Within-country gaps use damped Pew global ratios. |

## 3. History tests

Forward chaining on the WRP decades. Each test decade is predicted from its start year with WPP demography of that decade. Switching is fitted only on earlier decades. The score is the population-weighted total-variation error of country shares, in percentage points; lower is better.

| Model | 1990-2010 (2 test decades) | vs persistence | 1970-2010 (4 test decades) | vs persistence |
|---|---|---|---|---|
| Persistence (nothing changes) | 4.623 | 0 | 4.406 | 0 |
| Demography only | 4.549 | −0.075 | 4.354 | −0.052 |
| Demography + migration | 4.550 | −0.073 | 4.355 | −0.051 |
| + switching at half strength | 4.453 | −0.170 | 4.436 | +0.030 |
| + switching at full strength (used in the forecast) | 4.449 | −0.175 | 4.694 | +0.287 |
| + residual learner (weight chosen out of sample: 0) | = without it | | = without it | |
| Momentum (continue last decade's change) | 6.822 | +2.199 | 5.846 | +1.440 |

What this shows:
- **All mechanistic models beat persistence only slightly** (by 0.05-0.18 points on an error of about 4.5). Most decade-to-decade change in the WRP data is not explained by demography, migration or switching. Much of it is probably measurement: WRP's sources change between decades. Extrapolating recent change (momentum) is much worse than any model.
- **Switching helps on the recent decades and hurts on the early ones.** For 1970-1990 the fit had only two or three earlier decades and chose a very large country spread (τ_u = 2, the grid maximum). With four or five decades of training data, the fitted switching improved 1990-2010 more than any other mechanism. The forecast uses full strength because surveys observe switching directly. This is a judgment, and it is labelled as one in `step7_validation_report.json` (`used_by_forecast`).
- **Migration is neutral at decade scale.** It neither helps nor hurts on average; with UN stocks but without the migrant-religion calibration it helps a little (section 4).
- **The residual learner never improved out-of-sample error.** Its weight is 0, so the forecast has no machine-learned correction.
- Dominant religion was right for about 97% of countries in every model, persistence included. Of the 9 countries whose dominant group changed in 1990-2010, the models caught 1.

### Migration volumes against the UN migrant stocks

Starting from the UN 1990 foreign-born stocks, Step 7 simulates 1990-2020 (WPP demography, migration, no switching). It then compares each country's 2020 foreign-born share with the UN 2020 stocks:

| Circulation per year | Population-weighted error (pp) | Country-mean error (pp) | Correlation with UN | World foreign-born, millions (UN: 252) |
|---|---|---|---|---|
| 0 (net migration only) | 1.04 | 3.61 | 0.903 | 199 |
| 0.0002 (centre of the range used) | 0.91 | 3.05 | 0.913 | 239 |
| 0.0004 (top of the range used) | 0.98 | 3.21 | 0.913 | 272 |
| Persistence (1990 foreign-born share) | 1.76 | 4.11 | 0.890 | 211 |

The earlier circulation range (0.0005-0.0018 per year, set from gross-flow estimates) made far too many foreign-born residents. Its centre gave 407 million and a 2.1-point error. This test replaced the range with 0-0.0004. Gross-flow estimates are higher because many migrants return home, and the model counts a returning emigrant as foreign-born. So the model understates gross churn but gets foreign-born stocks right, and those stocks are what carry religion between countries.

### Which corridors, against the UN migrant stocks

The same 1990-2020 run compares the origin mix of simulated arrivals in the 25 largest destinations with the growth of UN bilateral stocks. It does this for three values of the margin softness ρ (1 = WPP margins exact):

| ρ | Correlation of origin mix | Distance of origin mix (TV, lower = better) |
|---|---|---|
| 1 | 0.651 | 0.507 |
| 0.75 | 0.662 | 0.490 |
| 0.5 | 0.588 | 0.517 |

ρ near 0.75 fits history best. In projections, exact margins (ρ = 1) force WPP's inconsistent projected nets through the network. For example, Pakistan would supply 46% of UK immigrants in 2020-2050, against 8% of the UK's 2020 foreign-born, because WPP keeps Pakistan's emigration high while Gulf net immigration falls to almost zero. The forecast therefore draws ρ between 0.5 and 1 in each run.

## 4. Does each new dataset improve accuracy?

Demography + migration, change in error versus persistence (pp; negative = better):

| Data | 1970-1990 | 1990-2010 |
|---|---|---|
| WPP indicators only (as in Steps 5D/5E) | −0.068 | −0.046 |
| + WPP age structure by sex | −0.062 | −0.045 |
| + UN bilateral migrant stocks (network and mobility) | −0.062 | −0.095 |
| + religion of migrants calibrated to Pew | −0.029 | −0.073 |

- **UN bilateral stocks** improve 1990-2010, the only window where they exist (they start in 1990). That variant is the best migration model in the history tests.
- **The calibrated religion of migrants** fits Pew's direct figures on migrants far better than "migrants mirror their origin": a 2.2-point error instead of 5.9. Yet it is slightly worse in these share hindcasts. The forecast keeps it, because the direct data measure the quantity being modelled, while the hindcast differences (0.02-0.03 points) are within noise. The calibration also uses Pew's 2020 migrant figures, so its effect on the earlier windows includes later information (labelled, not hidden).
- **Age structure** barely matters for shares, as Step 5E found for fertility gaps.

## 5. Religious switching: what is observed and what is modelled

A survey's raised-versus-current matrix is lifetime evidence, not an annual rate. Step 7 turns each country's lifetime matrix into five-year transition matrices for ages 15-49 (README, section 3) and fits rates from two kinds of evidence:
- **Observed:**
  - 67 survey cells in 33 countries, with 231 country × religion rates resting partly on them;
  - Pew's 117-country figures for adults 18-54.
- **Estimated from net change:** the six WRP decades. A hierarchical model shares information across countries (development effect β = 0.8 logit per unit, country spread τ = 0.8). The other 1,169 country × religion rates rest on net change and that model.

The two levels disagree for Christians and Buddhists, and each run draws a weight between them:

| religion | pew_left_per_100_raised_18_54 | history_level_model | survey_level_model | logit_shift | countries_with_own_survey_cells |
|---|---|---|---|---|---|
| Christianity | 17.1 | 11.67 | 17.1 | 0.55 | 27 |
| Islam | 1.0 | 1.66 | 1.0 | -0.53 | 2 |
| Hinduism | 1.0 | 1.29 | 1.0 | -0.26 | 4 |
| Buddhism | 22.1 | 14.09 | 22.1 | 0.75 | 5 |
| Judaism | nan | 11.6 | 11.6 | 0.0 | 2 |
| Folk_Traditional | nan | 13.05 | 13.05 | 0.0 | 0 |
| Other | nan | 9.54 | 9.54 | 0.0 | 0 |
| Unaffiliated | 7.5 | 8.11 | 7.5 | -0.09 | 4 |

From 2020 to 2100 in the reference scenario, 609 million people raised Christian switch out and 112 million switch in. Into the unaffiliated, 755 million switch in and 177 million out. These are gross flows in both directions, not one-way secularization.

## 6. Migration: corridors and diversity

Religion of migrants: destination affinity κ = 0.5 and minority effect λ = 0.65, fitted to 19 published Pew figures. The error is 2.2 points, against 5.9 if migrants mirrored their origin. The world Christian share of migrants is still about 5 points too low.

Largest simulated corridors, 2020-2050 (reference, millions over the 30 years):

| origin | destination | millions |
|---|---|---|
| MEX | USA | 5.62 |
| IND | USA | 4.47 |
| PAK | GBR | 2.61 |
| CHN | USA | 2.35 |
| PAK | USA | 2.32 |
| PHL | USA | 2.1 |
| UKR | RUS | 1.81 |
| BGD | IND | 1.72 |
| VEN | COL | 1.7 |
| PAK | SAU | 1.65 |
| ZWE | ZAF | 1.54 |
| TUR | DEU | 1.46 |
| AFG | IRN | 1.33 |
| BGD | SAU | 1.26 |
| IDN | MYS | 1.26 |

Some corridors are probably still too large. Pakistan to the UK (2.6 million) and to the USA (2.3 million) are inflated by WPP's projected margins, even after softening. India-Pakistan and Bangladesh-India probably carry the large historical stocks left by Partition (1947) and the 1971 war. See section 14.

**Does more migration make countries more diverse?** `step7_sensitivity.py` reruns the low, reference and rising migration scenarios with the same random draws under three assumptions about who migrates where. Rising minus low migration, population-weighted within-country diversity (median of 6 paired runs):

| Assumption | 2100 | 2200 | 2500 | 3026 |
|---|---|---|---|---|
| Calibrated (κ = 0.5, λ = 0.65; used in the forecast) | −0.001 | −0.001 | −0.001 | −0.011 |
| No destination affinity (κ = 0) | +0.003 | +0.011 | +0.035 | +0.033 |
| Migrants mirror their origin | +0.012 | +0.041 | +0.085 | +0.093 |

Migration raises diversity only if migrants do not sort toward co-religionists. The sorting in today's migrant stocks says they do, so in the forecast more migration means more foreign-born residents but not more religiously mixed countries. The model does not force rising diversity, and this is the assumption to revisit if Pew's corridor-level data show weaker sorting.

## 7. World shares by scenario (%)

Reference scenario, mean (5-95% of runs):

| Religion | 2020 | 2050 | 2100 | 2200 | 2500 | 3026 |
|---|---|---|---|---|---|---|
| Christianity | 28.8 | 28.2 (27.7-28.8) | 27.4 (25.7-29.1) | 24.3 (21.9-27.2) | 20.7 (16.2-29.1) | 18.8 (9.1-38.7) |
| Islam | 25.6 | 31.4 (30.9-31.7) | 38.1 (36.8-39.0) | 41.6 (38.8-43.8) | 41.8 (35.1-49.2) | 41.0 (23.0-59.6) |
| Hinduism | 14.9 | 14.6 (14.4-14.8) | 12.2 (11.8-12.7) | 9.3 (8.5-10.5) | 7.3 (3.8-15.7) | 7.0 (1.1-30.6) |
| Buddhism | 4.1 | 3.1 (2.9-3.2) | 1.8 (1.6-2.0) | 0.9 (0.7-1.2) | 0.5 (0.3-0.8) | 0.4 (0.2-1.0) |
| Judaism | 0.2 | 0.2 (0.2-0.2) | 0.2 (0.2-0.3) | 0.3 (0.2-0.3) | 0.3 (0.3-0.5) | 0.4 (0.2-0.8) |
| Folk/Traditional | 1.4 | 1.3 (1.3-1.4) | 1.1 (1.0-1.2) | 1.0 (0.8-1.2) | 1.1 (0.7-1.4) | 1.2 (0.4-2.6) |
| Other | 0.8 | 0.7 (0.7-0.7) | 0.6 (0.5-0.6) | 0.4 (0.4-0.5) | 0.4 (0.3-0.5) | 0.5 (0.3-0.9) |
| Unaffiliated | 24.2 | 20.5 (19.9-21.2) | 18.6 (16.9-20.1) | 22.1 (19.4-25.1) | 27.8 (24.4-31.2) | 30.7 (22.6-39.0) |

**2100**

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk/Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| stabilising | 27.4 | 38.1 | 12.2 | 1.8 | 0.2 | 1.1 | 0.6 | 18.6 |
| continued_secularization | 26.0 | 37.8 | 12.1 | 1.7 | 0.2 | 1.1 | 0.5 | 20.6 |
| high_retention | 30.9 | 38.7 | 12.4 | 2.2 | 0.3 | 1.3 | 0.6 | 13.7 |
| rising_migration | 27.3 | 38.1 | 12.3 | 1.8 | 0.2 | 1.1 | 0.6 | 18.5 |
| low_migration | 27.4 | 38.0 | 12.2 | 1.8 | 0.2 | 1.1 | 0.6 | 18.6 |
| changing_migration | 27.4 | 38.1 | 12.2 | 1.8 | 0.2 | 1.1 | 0.6 | 18.6 |
| persistent_fertility_gaps | 27.7 | 39.0 | 12.0 | 1.8 | 0.2 | 1.0 | 0.5 | 17.8 |
| combined_dispersal | 26.3 | 38.7 | 12.0 | 1.6 | 0.2 | 1.0 | 0.5 | 19.6 |

**2200** (long-run assumptions)

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk/Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| stabilising | 24.3 | 41.6 | 9.3 | 0.9 | 0.3 | 1.0 | 0.4 | 22.1 |
| continued_secularization | 17.7 | 39.0 | 8.7 | 0.6 | 0.3 | 0.8 | 0.4 | 32.5 |
| high_retention | 31.4 | 43.1 | 9.7 | 1.3 | 0.3 | 1.2 | 0.5 | 12.4 |
| rising_migration | 24.3 | 41.6 | 9.3 | 0.9 | 0.3 | 1.0 | 0.4 | 22.1 |
| low_migration | 24.4 | 41.6 | 9.3 | 0.9 | 0.3 | 1.0 | 0.4 | 22.0 |
| changing_migration | 24.4 | 41.7 | 9.3 | 0.9 | 0.3 | 1.0 | 0.4 | 22.0 |
| persistent_fertility_gaps | 25.5 | 46.6 | 8.4 | 0.7 | 0.3 | 0.7 | 0.3 | 17.6 |
| combined_dispersal | 18.9 | 44.2 | 7.9 | 0.5 | 0.2 | 0.5 | 0.2 | 27.4 |

**2500** (speculative)

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk/Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| stabilising | 20.7 | 41.8 | 7.3 | 0.5 | 0.3 | 1.1 | 0.4 | 27.8 |
| continued_secularization | 4.0 | 27.4 | 4.8 | 0.2 | 0.4 | 0.4 | 0.3 | 62.5 |
| high_retention | 32.7 | 44.1 | 8.0 | 1.0 | 0.3 | 1.4 | 0.5 | 12.0 |
| rising_migration | 20.7 | 40.6 | 7.3 | 0.6 | 0.3 | 1.1 | 0.4 | 29.0 |
| low_migration | 20.7 | 42.2 | 7.4 | 0.5 | 0.3 | 1.1 | 0.4 | 27.3 |
| changing_migration | 20.7 | 41.9 | 7.5 | 0.5 | 0.3 | 1.1 | 0.4 | 27.5 |
| persistent_fertility_gaps | 21.8 | 61.6 | 4.5 | 0.2 | 0.2 | 0.3 | 0.1 | 11.4 |
| combined_dispersal | 5.1 | 48.1 | 3.7 | 0.1 | 0.3 | 0.2 | 0.1 | 42.4 |

**3026** (highly speculative)

| scenario | Christianity | Islam | Hinduism | Buddhism | Judaism | Folk/Traditional | Other | Unaffiliated |
|---|---|---|---|---|---|---|---|---|
| stabilising | 18.8 | 41.0 | 7.0 | 0.4 | 0.4 | 1.2 | 0.5 | 30.7 |
| continued_secularization | 0.7 | 24.5 | 5.3 | 0.1 | 0.9 | 0.3 | 0.3 | 67.9 |
| high_retention | 34.1 | 42.3 | 7.6 | 0.9 | 0.4 | 1.7 | 0.6 | 12.5 |
| rising_migration | 19.6 | 37.0 | 7.3 | 0.5 | 0.4 | 1.3 | 0.4 | 33.6 |
| low_migration | 18.3 | 42.8 | 6.8 | 0.4 | 0.4 | 1.2 | 0.5 | 29.5 |
| changing_migration | 18.8 | 41.0 | 7.5 | 0.4 | 0.4 | 1.2 | 0.5 | 30.1 |
| persistent_fertility_gaps | 16.3 | 73.0 | 3.6 | 0.1 | 0.2 | 0.1 | 0.1 | 6.6 |
| combined_dispersal | 1.3 | 54.0 | 3.7 | 0.1 | 0.5 | 0.1 | 0.1 | 40.2 |

The scenarios are almost identical in 2050 (within about 2 points). Migration scenarios barely move world shares, because migration moves people between countries and cancels out worldwide. They change world shares only through differences in later fertility and mortality between countries.

## 8. What changes world shares, 2020-2100 (reference; percentage points)

Sequential sub-steps of the simulation; each row adds up exactly to its total.

| Religion | survival | births | switching | emigration | immigration | residual | calibration | total |
|---|---|---|---|---|---|---|---|---|
| Christianity | -0.22 | 3.92 | -5.11 | -0.12 | 0.12 | 0.0 | 0.01 | -1.4 |
| Islam | 6.09 | 8.13 | -0.34 | -0.03 | 0.03 | 0.0 | -1.44 | 12.44 |
| Hinduism | 0.32 | -2.12 | -0.22 | 0.39 | -0.39 | 0.0 | -0.69 | -2.7 |
| Buddhism | -1.06 | -1.17 | -0.35 | -0.01 | 0.01 | 0.0 | 0.27 | -2.31 |
| Judaism | 0.01 | -0.02 | 0.04 | -0.03 | 0.03 | 0.0 | 0.03 | 0.06 |
| Folk/Traditional | -0.14 | -0.22 | 0.05 | -0.03 | 0.03 | 0.0 | 0.04 | -0.28 |
| Other | -0.08 | -0.16 | 0.01 | -0.05 | 0.05 | 0.0 | 0.0 | -0.22 |
| Unaffiliated | -4.93 | -8.36 | 5.92 | -0.1 | 0.1 | 0.0 | 1.78 | -5.59 |

- **Islam grows by 12.4 points**, through births and the young age structure (survival).
- **Christianity loses 1.4 points:** births add 3.9 and switching takes away 5.1.
- **The unaffiliated fall by 5.6 points** despite gaining 5.9 from switching, because they are old and have few children (China, Japan, Europe).
- **Calibration** is the rescaling to WPP's national natural growth. It mainly corrects Islam (−1.4) and the unaffiliated (+1.8), because WPP's national fertility differs from the fertility implied by group rates.

## 9. Countries

Dominant religion changes (countries where most runs change):

| scenario | 2050 | 2100 | 2200 | 2500 | 3026 |
|---|---|---|---|---|---|
| stabilising | 6 | 23 | 62 | 97 | 121 |
| continued_secularization | 6 | 27 | 112 | 165 | 188 |
| high_retention | 1 | 12 | 22 | 39 | 67 |
| rising_migration | 6 | 23 | 61 | 97 | 118 |
| low_migration | 6 | 23 | 64 | 104 | 118 |
| changing_migration | 6 | 23 | 62 | 96 | 122 |
| persistent_fertility_gaps | 6 | 21 | 49 | 97 | 118 |
| combined_dispersal | 6 | 25 | 90 | 137 | 142 |

Reference scenario, changes by 2100:

| country_id | dominant_2020 | most_likely_2100 | prob_changed_by_2100 | pop2100_m |
|---|---|---|---|---|
| AUS | Christianity | Unaffiliated | 1.0 | 41.2 |
| AUT | Christianity | Unaffiliated | 1.0 | 7.2 |
| BEL | Christianity | Unaffiliated | 1.0 | 10.8 |
| CAN | Christianity | Unaffiliated | 1.0 | 48.9 |
| GBR | Christianity | Unaffiliated | 1.0 | 71.0 |
| ESP | Christianity | Unaffiliated | 1.0 | 32.8 |
| DEU | Christianity | Unaffiliated | 1.0 | 67.6 |
| SWE | Christianity | Unaffiliated | 1.0 | 10.9 |
| SGP | Buddhism | Unaffiliated | 1.0 | 4.4 |
| FRA | Christianity | Unaffiliated | 1.0 | 67.7 |
| CHE | Christianity | Unaffiliated | 0.98 | 8.8 |
| MNG | Buddhism | Unaffiliated | 0.92 | 5.5 |
| FIN | Christianity | Unaffiliated | 0.9 | 4.4 |
| TWN | Folk_Traditional | Unaffiliated | 0.85 | 10.0 |
| BLZ | Christianity | Unaffiliated | 0.85 | 0.4 |
| CHL | Christianity | Unaffiliated | 0.78 | 13.3 |
| NOR | Christianity | Unaffiliated | 0.75 | 5.3 |
| MKD | Christianity | Islam | 0.72 | 0.8 |
| NIC | Christianity | Unaffiliated | 0.7 | 8.5 |
| EST | Christianity | Unaffiliated | 0.65 | 0.8 |
| SLV | Christianity | Unaffiliated | 0.6 | 4.6 |
| SVN | Christianity | Unaffiliated | 0.55 | 1.6 |
| ITA | Christianity | Unaffiliated | 0.52 | 35.1 |

Selected countries (reference scenario):

| Country | Largest 2020 | its share 2020 / 2050 / 2100 / 2200 (%) | Unaffiliated 2020 / 2100 (%) | Muslim 2020 / 2100 (%) | Foreign-born 2100 (%) | Largest 2100 (runs agreeing) |
|---|---|---|---|---|---|---|
| USA | Christianity | 64 / 58 / 44 / 27 | 30 / 44 | 1 / 5 | 17 | Christianity (52%) |
| BRA | Christianity | 81 / 72 / 55 / 34 | 13 / 40 | 0 / 0 | 0 | Christianity (88%) |
| MEX | Christianity | 89 / 80 / 61 / 39 | 11 / 37 | 0 / 0 | 2 | Christianity (92%) |
| GBR | Christianity | 49 / 40 / 25 / 11 | 40 / 50 | 6 / 19 | 17 | Unaffiliated (100%) |
| FRA | Christianity | 46 / 37 / 23 / 10 | 43 / 55 | 9 / 20 | 13 | Unaffiliated (100%) |
| DEU | Christianity | 56 / 47 / 29 / 12 | 36 / 53 | 7 / 17 | 16 | Unaffiliated (100%) |
| SWE | Christianity | 61 / 46 / 26 / 9 | 29 / 50 | 8 / 20 | 20 | Unaffiliated (100%) |
| RUS | Christianity | 70 / 62 / 46 / 26 | 20 / 37 | 8 / 15 | 10 | Christianity (55%) |
| NGA | Islam | 56 / 58 / 60 / 61 | 0 / 3 | 56 / 60 | 1 | Islam (100%) |
| ETH | Christianity | 62 / 57 / 47 / 34 | 0 / 12 | 36 / 40 | 1 | Christianity (82%) |
| EGY | Islam | 95 / 94 / 92 / 88 | 0 / 4 | 95 / 92 | 1 | Islam (100%) |
| SAU | Islam | 93 / 92 / 90 / 84 | 0 / 4 | 93 / 90 | 19 | Islam (100%) |
| IND | Hinduism | 79 / 78 / 76 / 73 | 0 / 3 | 15 / 18 | 0 | Hinduism (100%) |
| CHN | Unaffiliated | 90 / 88 / 84 / 80 | 90 / 84 | 2 / 4 | 0 | Unaffiliated (100%) |
| JPN | Unaffiliated | 57 / 64 / 74 / 78 | 57 / 74 | 0 / 2 | 8 | Unaffiliated (100%) |
| KOR | Unaffiliated | 48 / 52 / 57 / 58 | 48 / 57 | 0 / 1 | 6 | Unaffiliated (100%) |
| IDN | Islam | 87 / 87 / 86 / 84 | 0 / 5 | 87 / 86 | 0 | Islam (100%) |
| AUS | Christianity | 47 / 39 / 25 / 12 | 42 / 52 | 4 / 12 | 28 | Unaffiliated (100%) |
| ISR | Judaism | 77 / 73 / 64 / 54 | 4 / 9 | 15 / 22 | 10 | Judaism (100%) |
| ARE | Islam | 73 / 72 / 72 / 69 | 0 / 6 | 73 / 72 | 36 | Islam (100%) |

Israel's decline is very likely an artefact (section 14).

## 10. Religious diversity within countries (population-weighted Gini-Simpson)

| scenario | 2020 | 2050 | 2100 | 2200 | 2500 | 3026 |
|---|---|---|---|---|---|---|
| stabilising | 0.288 | 0.314 | 0.358 | 0.399 | 0.435 | 0.456 |
| continued_secularization | 0.288 | 0.314 | 0.366 | 0.429 | 0.416 | 0.398 |
| high_retention | 0.288 | 0.304 | 0.333 | 0.359 | 0.38 | 0.398 |
| rising_migration | 0.288 | 0.314 | 0.357 | 0.4 | 0.439 | 0.465 |
| low_migration | 0.288 | 0.314 | 0.358 | 0.4 | 0.436 | 0.452 |
| changing_migration | 0.288 | 0.314 | 0.358 | 0.399 | 0.434 | 0.458 |
| persistent_fertility_gaps | 0.288 | 0.314 | 0.357 | 0.388 | 0.327 | 0.24 |
| combined_dispersal | 0.288 | 0.314 | 0.365 | 0.427 | 0.45 | 0.431 |

Diversity rises to 2100 in every scenario, mainly because switching creates large unaffiliated minorities in Christian-majority countries. After 2200 it falls again where one group becomes dominant: the unaffiliated under continued secularization, Muslims under persistent fertility gaps. The diversity maps (`diversity_*`, `diversity_change_*`) show the country pattern.

## 11. Model uncertainty versus scenario uncertainty (world shares, percentage points)

"Within" is the mean 5-95% band inside a scenario (parameters, switching evidence, country noise, migration routing). "Between" is the range of the scenario means.

| year | religion | within | between | lowest_scenario | highest_scenario |
|---|---|---|---|---|---|
| 2050 | Christianity | 1.1 | 1.4 | continued_secularization | high_retention |
| 2050 | Hinduism | 0.4 | 0.1 | combined_dispersal | high_retention |
| 2050 | Islam | 0.8 | 0.2 | continued_secularization | high_retention |
| 2050 | Unaffiliated | 1.3 | 2.1 | high_retention | continued_secularization |
| 2100 | Christianity | 3.3 | 4.9 | continued_secularization | high_retention |
| 2100 | Hinduism | 1.1 | 0.5 | combined_dispersal | high_retention |
| 2100 | Islam | 2.3 | 1.2 | continued_secularization | persistent_fertility_gaps |
| 2100 | Unaffiliated | 3.2 | 6.9 | high_retention | continued_secularization |
| 2200 | Christianity | 5.5 | 13.7 | continued_secularization | high_retention |
| 2200 | Hinduism | 2.5 | 1.8 | combined_dispersal | high_retention |
| 2200 | Islam | 6.1 | 7.6 | continued_secularization | persistent_fertility_gaps |
| 2200 | Unaffiliated | 5.9 | 20.2 | high_retention | continued_secularization |
| 2500 | Christianity | 11.3 | 28.7 | continued_secularization | high_retention |
| 2500 | Hinduism | 10.6 | 4.2 | combined_dispersal | high_retention |
| 2500 | Islam | 16.5 | 34.2 | continued_secularization | persistent_fertility_gaps |
| 2500 | Unaffiliated | 9.0 | 51.2 | persistent_fertility_gaps | continued_secularization |
| 3026 | Christianity | 23.7 | 33.4 | continued_secularization | high_retention |
| 3026 | Hinduism | 22.9 | 4.0 | persistent_fertility_gaps | high_retention |
| 3026 | Islam | 35.3 | 48.6 | continued_secularization | persistent_fertility_gaps |
| 3026 | Unaffiliated | 15.9 | 61.4 | persistent_fertility_gaps | continued_secularization |

- **To 2100** both kinds are similar in size, a few points.
- **After 2100** scenario assumptions dominate.
- **Within-scenario bands become very wide by 3026**, for example 1-31% for Hindus. The reason is persistent country fertility deviations (0.1 child per woman) compounding over 900 years: whichever large country draws higher fertility grows to a larger share of the world.

## 12. Step 7 versus Step 5D

World shares, Step 5D headline (demography only) against the Step 7 reference:

| Year | Religion | Step 5D | Step 7 | Difference (pp) |
|---|---|---|---|---|
| 2050 | Christianity | 30.65 | 28.21 | −2.44 |
| 2050 | Islam | 31.23 | 31.38 | +0.15 |
| 2050 | Unaffiliated | 17.99 | 20.53 | +2.54 |
| 2100 | Christianity | 34.81 | 27.37 | −7.44 |
| 2100 | Islam | 38.30 | 38.09 | −0.21 |
| 2100 | Hinduism | 12.63 | 12.23 | −0.39 |
| 2100 | Unaffiliated | 10.20 | 18.57 | +8.38 |

The Muslim share hardly differs, because demography drives it in both models. The Christian and unaffiliated shares differ by switching, which Step 5D did not model. The full table is in `results_step7/step7_comparison_report.md`.

## 13. Maps and charts

`step7_maps_svg.py` writes 48 maps and a world-shares chart to `outputs/maps_step7_svg/`, with `index.html`. `step7_make_maps.py` writes the same maps as PNGs in the Step 6 style, plus four charts. In the build environment matplotlib could not be installed. That script was run end to end with stand-in plotting libraries: all 52 figures passed its data checks, but no PNG was drawn here.

The maps cover:
- dominant religion in 2020, 2050, 2100, 2200, 2500 and 3026;
- each religion's share in 2050, 2100 and 3026;
- diversity, and its change;
- countries whose dominant religion changes, and the share of runs that change;
- the effects of migration and switching, and the main driver of change;
- the foreign-born share in 2100;
- four scenario-difference maps.

## 14. Known problems, and what would fix them

| Problem | Effect | Fix |
|---|---|---|
| No country data on fertility by religion | Within-country gaps come from damped Pew global ratios. In **Israel** this makes the Jewish share fall and the Muslim share rise. That is very likely wrong, because in Israeli statistics Jewish fertility is about as high as Muslim fertility (not verified here). India, Nigeria and Lebanon are also sensitive to this. | Add verified rows to `step7_inputs/religion_fertility_observed.csv` (Israel CBS, India NFHS-5, DHS reports). They replace the global ratios for that country. |
| Pew 2010-2020 window not used | The most recent and best-measured decade is neither fitted nor tested in this run | Run Step 2 on your machine (needs `data/raw/pew_2010_2020.xlsx`), then rerun Step 7 |
| Switching level | Fitted to net change, Christians leave at about 12 per 100 raised; in Pew's 2025 surveys, 17. Buddhists 14 vs 22. Each run mixes the two levels. | Pew Spring 2024 microdata and ISSP 2018 matrices (free accounts) would give country matrices instead of excerpts |
| Development link | Countries now developing (for example Ethiopia, Mexico, Brazil) inherit the disaffiliation seen in richer countries | This is the scenario assumption that `high_retention` relaxes. More survey countries in Africa and Asia would test it. |
| Religion of migrants | Calibrated to 19 published aggregates. The world Christian share of migrants is still about 5 points too low. Destination affinity κ decides the effect of migration on diversity (section 10). | Pew's country-level migrant dataset (free account) |
| Gross migration | Circulation is calibrated to foreign-born stocks, so gross churn is understated. UN stocks carry historical corridors into the network (for example about 0.9 million each way between India and Pakistan in 2020-2050, a legacy of 1947). | Abel & Cohen corridor flows as the network (the figshare files) |
| WPP's projected net migration | WPP keeps South Asian emigration high (Pakistan 0.5-1 million a year) while Gulf net immigration falls to almost zero after 2030, so those emigrants must land in the countries WPP gives positive net immigration. Softening the margins (ρ 0.5-1) cuts Pakistan's share of UK arrivals in 2020-2050 from 46% to 32% (8% of the 2020 UK foreign-born), and of US arrivals from 14% to 7% (0.9%). Some excess remains. This lifts the Muslim share of the UK and USA. | Abel & Cohen corridor flows, or an explicit Gulf circular-migration component |
| After 2100 | All demography is assumption; 2500 and 3026 are speculative scenarios | None. Read them as consequences of stated assumptions. |
| Folk/Other split; China | Pew counts folk religion inside "other"; WRP and Pew classify China differently | Step 2's proxy is labelled; country studies of China would help |
| History tests | WRP's decade-to-decade noise is large; models beat persistence by only about 0.1 point | The Pew 2010-2020 window (above) and census series by religion |

## 15. Integrity checks (`verify_step7.py`)

- PASS  1a shares non-negative and finite (33600 rows)
- PASS  1b shares sum to 100% in every country, year and scenario
- PASS  1c q05 bands within 0-100%
- PASS  1c q95 bands within 0-100%
- PASS  2a sub-step contributions sum to the total
- PASS  2b components reproduce the simulated change of mean shares (max error 6.16e-07 pp)
- PASS  3a migration conserves people by religion worldwide (max imbalance 0.0 persons of 927,018,877)
- PASS  3b migration leaves world religious shares unchanged
- PASS  4a world shares sum to 100%
- PASS  4b world population finite and positive to 3030 (range 2.19-10.27 billion)
- PASS  5a dominant-change probabilities in [0, 1]
- PASS  5b switching rates are probabilities
- PASS  5c diversity index within [0, 0.875]
- PASS  6a start state reported: results_step5/headline_country_shares.csv (Pew 2020 start state of Step 5D)

All checks passed in the build run.

