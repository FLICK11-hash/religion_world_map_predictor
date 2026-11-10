# Results

From the committed run in `results/`: reference scenario `stabilising`, 40 Monte Carlo runs per
scenario, seed 2026, start state `inputs/pew2020_start_state.csv` (Pew 2020; the Pew 2010-2020
decade is not available in this run). Every number here is in a file in `results/`; the run report
`results/comparison_report.md` has the full tables. Shares are percent of the population;
differences are percentage points (pp).

## 1. History tests: no variant beats assuming nothing changes

Ten-year forecasts of the four World Religion Project decades 1970-2010, everything fitted only on
earlier decades. Population-weighted total-variation (TV) error of country shares, mean over the
four decades (`validation_summary.csv`):

| Model | TV error (pp) | Against persistence |
|---|---|---|
| Persistence (no change) | 4.41 | – |
| Trend (last decade repeated) | 5.85 | +33% |
| Births and deaths | 4.38 | −0.6% |
| + migration | 4.38 | −0.6% |
| + switching, strength 0.5 | 4.56 | +3.4% |
| + switching, strength 1 (as projected) | 4.90 | +11.3% |
| + switching, strength chosen on earlier decades | 4.52 | +2.6% |

Country by country, over 558 country-decades in 171 countries (`inference.csv`), with 95% intervals
from a bootstrap over countries and the exact decade-level sign-flip test:

| Model | Difference from persistence (pp) | 95% interval | Decades better | p (decades) |
|---|---|---|---|---|
| Trend | +1.71 | +1.03 to +2.25 | 0 of 4 | 0.125 |
| Births and deaths | −0.02 | −0.10 to +0.06 | 2 of 4 | 0.75 |
| + migration | −0.02 | −0.08 to +0.06 | 2 of 4 | 0.75 |
| + switching, strength 1 | +0.48 | −0.19 to +1.15 | 1 of 4 | 0.375 |
| + switching, chosen | +0.12 | −0.08 to +0.30 | 2 of 4 | 0.875 |

Three things follow. **Repeating recent change is clearly worse than assuming none** (the interval
excludes zero by a wide margin). **Births and deaths alone are indistinguishable from persistence,
and at most about 2% better** (the lower end of the interval, −0.10 pp of 4.41). **Switching fitted
to historical net change does not help**: with full strength it is worse on average, though not
significantly. Fitted to net change alone, the switching model chooses the largest country spread
its prior range allows in every decade (`switching_fit_by_fold.csv`, `at_bound`), and it forecasts
worse because that spread reproduces country trends in the historical residuals that do not
continue, the same failure as the trend baseline. The bootstrap treats countries as independent
within a decade, so its intervals are if anything too narrow; the conclusion that nothing is
distinguishable from persistence holds a fortiori.

## 2. Forecast error and calibrated intervals

Monte Carlo forecasts from 1970, 1980, 1990 and 2000, scored at every later decade to 2010
(`forecast_error_record.csv`). The fitted error model is `e = (h/10)^β (s(1−s) + 10⁻⁴)^b u` with
**b = 0.85** and **β = 0.34** (`forecast_error_model.json`): error grows more slowly than a random
walk (β = 0.5). Mean absolute standardised error is 0.49, 0.59, 0.75 and 0.77 at 10, 20, 30 and 40
years.

Leave one origin out (`predictive_calibration.csv`), share of held-out country × religion shares
inside the 90% interval, and its interval score (pp, lower is better). The projection uses the
errors as recorded; centring them is shown for comparison:

| Horizon | Parameter-only | Calibrated (as projected) | Calibrated, centred | Score, parameter-only | Score, calibrated |
|---|---|---|---|---|---|
| 10 years | 18.7% | 89.0% | 89.8% | 21.8 | 10.8 |
| 20 years | 19.9% | 91.3% | 89.6% | 33.7 | 13.8 |
| 30 years | 18.8% | 91.0% | 89.6% | 43.4 | 17.6 |
| 40 years | 19.4% | 92.3% | 90.8% | 48.9 | 18.9 |

Averaged over horizons, the calibrated intervals cover 52%, 81%, 90% and 95% at nominal 50%, 80%,
90% and 95%. For world totals of the observed countries (`predictive_calibration_world.csv`; 80
held-out world shares), the 90% predictive interval contained the observation 90.0% of the time
and the parameter-only band 13.8%. Centring the errors calibrates slightly worse (interval score
14.4 against 13.9 averaged over horizons) and moves world medians away from the central path.

The model's own Monte Carlo bands are parameter uncertainty and nothing else: they contain the truth
about a fifth as often as they claim. The predictive intervals used below add the errors the model
actually made.

## 3. Religious switching

The empirical Bayes fit to historical net change (six World Religion Project decades) and 48 survey
rows gives, as the mean of three replicate fits (`projection_report.json`, `switching_fit`):
δ = −0.05 (replicate s.d. 0.16), β_d = 1.16 (0.005), τ_u = 1.61 (0.34). The development effect
β_d is tightly determined: disaffiliation rises with development. The country spread τ_u is the
least determined, and one replicate sits at the upper bound of its prior range.

In Pew's measure, people raised in a religion who have left it per 100, adults 18-54 in 117
countries (`switching_check_vs_pew.csv`):

| Raised | Fitted level | Pew (2025) survey level |
|---|---|---|
| Christian | 13.0 | 17.1 |
| Buddhist | 14.0 | 22.1 |
| Muslim | 1.8 | 1.0 |
| Hindu | 1.3 | 1.0 |
| Unaffiliated (returned to a religion) | 8.5 | 7.5 |

The fitted level is now much closer to the survey level than it used to be: an earlier version
reported 11.7 against 17.1 for Christians, most of that gap being an error in the survey
likelihood (respondents counted several times over, and single conversion cells compared with the
probability of any conversion). Each projection run draws a weight between the two levels.

## 4. World shares to 2100

Reference scenario: the mean of the 40 runs (the central path), and the 90% predictive interval,
which adds the record's forecast errors (`global_share_by_scenario.csv`, columns `mean`, `pi05`,
`pi95`; `predictive_sensitivity_centring.csv` for the medians):

| Religion | 2020 | 2050 | 90% interval | 2100 | 90% interval |
|---|---|---|---|---|---|
| Islam | 25.6 | 31.6 | 29.5-34.1 | 38.7 | 36.5-42.5 |
| Christianity | 28.8 | 27.7 | 25.4-29.9 | 25.8 | 22.3-29.3 |
| Unaffiliated | 24.2 | 20.8 | 16.4-21.6 | 19.6 | 12.5-21.1 |
| Hinduism | 14.9 | 14.5 | 10.2-17.0 | 12.1 | 8.1-13.4 |
| Buddhism | 4.1 | 3.1 | 2.7-5.0 | 1.8 | 1.5-3.6 |
| Folk/Traditional | 1.4 | 1.3 | 0.7-4.2 | 1.1 | 0.6-6.8 |
| Other | 0.8 | 0.7 | 0.6-3.6 | 0.6 | 0.6-3.8 |
| Judaism | 0.2 | 0.2 | 0.1-0.2 | 0.3 | 0.2-0.4 |

What the intervals support. **Islam becomes the largest group:** its 2100 interval (36.5-42.5%)
lies entirely above Christianity's (22.3-29.3%), and the two barely overlap by 2050. **The
Christian share falls,** probably by 2 to 6 pp. **The unaffiliated share falls in the world,**
even though it rises inside most countries (section 5); its interval is skewed downward
(predictive median 17.1%), because the countries compositionally closest to China in the error
record, post-communist and East Asian, saw unaffiliated shares fall in 1970-2010. **Folk and other
religions** have long upper tails for the same reason in reverse: the record's reclassifications
between folk religion and no religion. The parameter spread alone would have suggested intervals
between about two fifths as wide (Christianity, the unaffiliated) and a twentieth as wide (folk
and other religions).

By 2100 the eight scenarios differ by less than the width of the predictive interval for every
group; the closest is the unaffiliated, with scenario means 6.7 pp apart against a predictive band
of 8.6 pp (`uncertainty_model_vs_scenario.csv`). What the stated scenarios vary matters less than
what the model has historically got wrong.

## 5. Where the change comes from

An exact split of each religion's change in world share, 2020-2100 (reference scenario,
`world_share_shift_share.csv`), into countries' own shares changing at fixed 2020 population
weights, the weights changing at fixed 2020 shares, and a small interaction:

| Religion | Change | Within countries | Population weighting | Interaction |
|---|---|---|---|---|
| Islam | +13.0 | +2.7 | +10.4 | −0.0 |
| Christianity | −2.9 | −8.5 | +6.4 | −0.9 |
| Hinduism | −2.9 | −0.6 | −2.4 | +0.1 |
| Buddhism | −2.3 | −0.9 | −1.7 | +0.3 |
| Unaffiliated | −4.5 | +7.2 | −12.5 | +0.8 |

Four fifths of Islam's rise is the faster population growth of Muslim-majority countries. The
unaffiliated share rises inside countries, by switching, and falls in the world, because the
countries where it is concentrated (China above all) grow more slowly. Christianity loses within
countries and gains from the growth of sub-Saharan Africa.

## 6. What each mechanism contributes

Each mechanism's contribution in 2100, the full model minus the same run with that mechanism
switched off, paired run by run on identical draws (`ablation_effects.csv`; mean and 5-95% of 12
paired runs, pp of world population):

| Mechanism | Christianity | Islam | Unaffiliated | Hinduism | Countries whose largest religion changes |
|---|---|---|---|---|---|
| Religious switching | −8.1 (−9.8 to −6.8) | −0.7 | +9.5 (+8.2 to +11.8) | −0.3 | 41 (33 to 51) |
| Fertility differences within countries | −0.6 | +2.0 (+1.6 to +2.5) | −0.8 | −0.4 | −1 |
| Migration | −0.1 | +0.2 | −0.2 | +0.1 | −2 |

Switching is what changes countries: without it the world Christian share would be 8 pp higher
and the unaffiliated share 9.5 pp lower in 2100, and some 41 fewer countries would change their
largest religion. Within-country fertility differences add about 2 pp to the Muslim share.
Migration moves no world share by more than a quarter of a point, as it must in a model in which
migrants keep their religion: it relocates people and changes world shares only through what
happens to them afterwards.

**Does more migration make countries more mixed?** Not by 2100 under the calibrated religion of
migrants (`migrant_sorting_effect.csv`): rising minus low migration changes population-weighted
within-country diversity by a median −0.0003, with 5 of 12 runs more diverse. If migrants mirrored
their origin, every run would be more diverse (+0.013). The difference is destination affinity:
migrants calibrated to Pew's figures go where their religion is already common.

## 7. Countries whose largest religion changes

In the reference scenario, the largest religion changes by 2100 in 27 countries with predictive
probability above one half, and in 7 by 2050 (`dominant_change.csv`, `prob_changed_by_*_predictive`).
Almost all are Christian-majority countries where the unaffiliated become the largest group:

| Country | Probability by 2050 | Probability by 2100 |
|---|---|---|
| France | 54% | 78% |
| Australia | 62% | 78% |
| United Kingdom | 56% | 75% |
| Germany | 36% | 69% |
| Canada | 40% | 67% |
| Chile | 16% | 67% |
| Spain | 12% | 63% |
| United States | 14% | 47% |

Mongolia, Singapore and Taiwan (Buddhist or folk to unaffiliated) have the highest probabilities
(92%, 85%, 80%), and North Macedonia's most likely change is from Christianity to Islam (66%).
The share of parameter runs that change (`prob_changed_by_*`) is much higher for many of these, 100%
for France, the United Kingdom and Germany: without forecast error the model would state as nearly
certain what it can only call likely.

## 8. What the results turn on

A global sensitivity analysis over the 23 drawn parameters, on 120 runs of the reference scenario
separate from the projection runs (`sensitivity_coefficients.csv`; standardised rank regression
coefficients, R² of the linear reading in brackets):

| Outcome | 2050 | 2100 |
|---|---|---|
| Christian world share | `survey_weight` −0.78 (R² 0.66) | `survey_weight` −0.60 (0.42) |
| Muslim world share | `psi` +0.71 (0.72) | `survey_weight` +0.40, `Hf` +0.35, `psi` +0.33 (0.58) |
| Unaffiliated world share | `survey_weight` +0.41, `psi` −0.34 (0.38) | `survey_weight` +0.29 (0.21) |

`survey_weight`, how far switching follows Pew's survey level rather than the level fitted to
historical net change, is the most influential assumption for the Christian and unaffiliated
shares. For the Muslim share in 2050 the most influential is `psi`, the fraction of the global
median-age gap between religions applied inside countries; its inputs, Pew's 2010 median ages by
religion, are marked unverified in `config/assumptions.json` and must be checked before the result
is cited. `Hf`, how fast within-country fertility gaps converge, matters by 2100. R² falls with
horizon: by 2100 no single assumption explains most of the spread, and the parameters interact
(the replicate switching fits and country posterior draws also vary between runs).

## 9. Migration

Starting from the UN 1990 foreign-born stocks, the migration model reproduces each country's 2020
foreign-born share with a population-weighted error of 0.91 pp, against 1.76 pp for the 1990 share
unchanged (correlation with the UN 0.91; 240 million foreign-born worldwide against the UN's 252
million; `migration_foreign_born_check.csv`). The origin mix of simulated 1990-2020
arrivals in the 25 largest destinations correlates 0.66 with the growth of UN bilateral stocks
(`migration_corridor_check.csv`). Capping any origin's share of a destination's arrivals
at 1.5 to 4 times its share of the stock lowers that fit at every margin softness (0.53-0.58), and
observed arrivals were more concentrated by origin than the model simulates (largest origin 41% of
arrivals against 31%), so no cap is applied. In the projection, the largest single origin supplies a much larger share of some
destinations' arrivals in 2020-2050 than of their 2020 migrant stock
(`migration_corridor_concentration.csv`), notably Pakistan into the United Kingdom (33% of arrivals
against 8% of the stock) and Turkey into Germany (25% against 12%), because WPP 2024 keeps South
Asian emigration high while Gulf net immigration falls to almost zero after 2030; results for such
destinations should be read with that in mind.

## 10. Against Pew Research Center's 2015 projection

Pew Research Center's 2015 report projected the same quantity to 2050. Change in world share,
2020-2050, as each projects it (`benchmark_vs_pew2015.csv`):

| Religion | This model | Pew 2015 | Difference | 2020 level difference |
|---|---|---|---|---|
| Islam | +6.0 | +4.8 | +1.2 | +0.7 |
| Unaffiliated | −3.4 | −2.4 | −1.0 | +8.6 |
| Christianity | −1.0 | +0.2 | −1.3 | −2.3 |
| Buddhism | −1.0 | −1.4 | +0.4 | −2.5 |
| Folk/Traditional | −0.1 | −0.8 | +0.7 | −4.2 |
| Hinduism | −0.4 | −0.3 | −0.1 | −0.2 |

The two independently built models agree on the size of every group's change within 1.3 pp over
thirty years, and on its direction for six of the eight groups; the exceptions are Christianity
and Judaism (changes under 0.02 pp). They disagree far more about where 2020 started: Pew's 2015
estimate of 2020 differs from Pew's later data, used here, by up to 8.6 pp (the unaffiliated),
mostly because China is classified differently. Scored country by country, Pew's 2015 projection
of 2020 misses Pew's later measurement by 10.7 pp population-weighted, barely better than freezing
2010 (10.9), and China is 69% of that (`benchmark_pew2015_skill.csv`). No projection can be scored
more precisely than its measurements agree.
