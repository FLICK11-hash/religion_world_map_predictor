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
| Trend (the last decade's change repeated) | 5.97 | +36% |
| Births, deaths and migration + the last decade's unexplained change | 5.85 | +33% |
| Births and deaths | 4.38 | −0.7% |
| + migration | 4.37 | −0.8% |
| + switching, strength 0.5 | 4.68 | +6.2% |
| + switching, strength 1 (as projected) | 5.16 | +17.0% |
| + switching, strength chosen on earlier decades | 4.59 | +4.2% |

Country by country, over 558 country-decades in 171 countries (`inference.csv`), with 95% intervals
from a bootstrap over countries and the exact decade-level sign-flip test:

| Model | Difference from persistence (pp) | 95% interval | Decades better | p (decades) |
|---|---|---|---|---|
| Trend | +1.86 | +1.21 to +2.41 | 0 of 4 | 0.125 |
| Demography + last decade's unexplained change | +1.71 | +1.05 to +2.26 | 0 of 4 | 0.125 |
| Births and deaths | −0.03 | −0.10 to +0.06 | 2 of 4 | 0.75 |
| + migration | −0.03 | −0.09 to +0.04 | 2 of 4 | 0.75 |
| + switching, strength 1 | +0.72 | −0.19 to +1.70 | 1 of 4 | 0.375 |
| + switching, chosen | +0.17 | −0.10 to +0.45 | 2 of 4 | 0.875 |

Three things follow. **Repeating recent change is clearly worse than assuming none**, whether the
change repeated is the observed one or the part demography did not explain. **Births and deaths
alone are indistinguishable from persistence, and at most about 2% better** (the lower end of the
interval, −0.10 pp of 4.41). **Switching fitted to historical net change does not help**: at full
strength it is worse on average, though not significantly. Fitted to net change alone, the
switching model chooses the largest country spread its prior range allows in every decade
(`switching_fit_by_fold.csv`), and it forecasts worse because that spread reproduces country trends
in the historical residuals that do not continue, the failure of the trend baselines. The bootstrap
treats countries as independent within a decade, so its intervals are if anything too narrow; the
conclusion that nothing is distinguishable from persistence holds a fortiori.

## 2. Forecast error and predictive intervals

Monte Carlo forecasts from 1970, 1980, 1990 and 2000, scored at every later decade to 2010
(`forecast_error_record.csv`). The fitted error model is `e = (h/10)^β (s(1−s) + 10⁻⁴)^b u` with
**b = 0.80** and **β = 0.27** (`forecast_error_model.json`): error grows more slowly than a random
walk (β = 0.5). Mean absolute standardised error is 0.32, 0.37, 0.44 and 0.47 at 10, 20, 30 and 40
years.

Out of sample (`predictive_calibration.csv`, scheme `non-overlapping`): for every forecast, the
error model is refitted on the record entries that share no calendar years with it, and the
forecast is scored. Share of country × religion shares observed above zero that fall inside the
90% interval, and interval score (pp, lower is better):

| Horizon | Parameter-only | Calibrated (as projected) | Calibrated, real time | Score, parameter-only | Score, calibrated |
|---|---|---|---|---|---|
| 10 years | 23.4% | 87.6% | 86.6% | 29.2 | 13.6 |
| 20 years | 24.9% | 85.6% | 84.7% | 44.1 | 19.2 |
| 30 years | 25.1% | 87.6% | 88.9% | 57.2 | 26.9 |

Over all cells, including groups recorded at exactly zero, coverage is 89.7%, 87.6% and 90.1%; for
cells forecast at 20% or more it is 88.3%, 83.8% and 89.0%. No 40-year forecast has an entry left
that shares no years with it, so calibration cannot be checked beyond 30 years. For world totals of
the observed countries (`predictive_calibration_world.csv`), the 90% interval contained 84.7% of 72
held-out world shares (87.5% at 10 and 20 years, 75% at 30), and 75% of 48 in real time; the
parameter-only band contained 16.7%.

So the calibrated intervals are close to nominal for countries but **a few points too narrow**, and
coarser for world totals, which rest on the common shocks of four decades. The design matters:
the earlier leave-one-origin-out validation, which kept the decades a forecast was scored on in the
error model's pool, reported 89-92% and 90% for world totals. Adding the errors to the central path
only, rather than to every run, calibrates worse (84.7% against 87.0% pooled over horizons), and
centring the errors on their pooled mean changes little (87.3%) while moving world medians (below).
The model's own Monte Carlo bands are parameter uncertainty and nothing else: they contain the
truth about a quarter as often as they claim.

## 3. Religious switching

The empirical Bayes fit to historical net change (six World Religion Project decades) and 48 survey
rows gives, as the mean of three replicate fits (`projection_report.json`, `switching_fit`):
δ = −0.06 (standard error 0.18), β_d = 1.27 (0.10), τ_u = 1.46 (standard error of log τ_u 0.11).
The replicates differ by 0.03, 0.01 and 0.02, about a seventh of a standard error or less, and
every country's importance sample has at least 79 effective draws of 512 (median 314). Each
projection run draws its own hyperparameters from their Laplace approximation.

**Does the estimator recover what it estimates?** In 20 replications with evidence simulated from
these values under the real design (`estimator_recovery.csv`), the estimates have bias −0.08
(± 0.04) for δ, +0.01 (± 0.01) for β_d and −0.03 (± 0.02) for log τ_u, root mean squared errors of
0.20, 0.05 and 0.11, and 90% Laplace intervals that cover the truth in 85%, 95% and 85% of
replications. The overall level δ is estimated about half a standard error too low, which makes
the fitted level of switching, if anything, slightly conservative.

In Pew's measure, people raised in a religion who have left it per 100, adults 18-54 in 117
countries (`switching_check_vs_pew.csv`):

| Raised | Fitted level | Pew (2025) survey level |
|---|---|---|
| Christian | 12.8 | 17.1 |
| Buddhist | 14.1 | 22.1 |
| Muslim | 1.7 | 1.0 |
| Hindu | 1.4 | 1.0 |
| Unaffiliated (returned to a religion) | 8.3 | 7.5 |

An earlier version reported 11.7 against 17.1 for Christians; most of that gap was an error in the
survey likelihood (respondents counted several times over, and single conversion cells compared
with the probability of any conversion). Each projection run draws a weight between the two levels.

## 4. World shares to 2100

Reference scenario: the mean of the 40 runs (the central path), and the 90% predictive interval,
which adds the record's forecast errors (`global_share_by_scenario.csv`, columns `mean`, `pi05`,
`pi95`; `predictive_sensitivity_centring.csv` for the medians):

| Religion | 2020 | 2050 | 90% interval | 2100 | 90% interval |
|---|---|---|---|---|---|
| Islam | 25.6 | 31.7 | 29.9-34.2 | 39.1 | 36.7-42.4 |
| Christianity | 28.8 | 27.8 | 26.0-29.7 | 25.7 | 22.6-28.8 |
| Unaffiliated | 24.2 | 20.7 | 16.2-21.4 | 19.5 | 13.9-21.8 |
| Hinduism | 14.9 | 14.5 | 11.4-16.5 | 12.0 | 9.1-14.1 |
| Buddhism | 4.1 | 3.0 | 2.7-5.4 | 1.7 | 1.4-3.3 |
| Folk/Traditional | 1.4 | 1.3 | 0.8-3.7 | 1.1 | 0.6-4.4 |
| Other | 0.8 | 0.7 | 0.6-2.9 | 0.5 | 0.6-2.8 |
| Judaism | 0.2 | 0.2 | 0.1-0.2 | 0.3 | 0.2-0.3 |

What the intervals support. **Islam becomes the largest group:** its 2100 interval (36.7-42.4%)
lies entirely above Christianity's (22.6-28.8%), and by 2050 the two no longer overlap. **The
Christian share falls,** probably by 0 to 6 pp. **The unaffiliated share falls in the world,** even
though it rises inside most countries (section 5); its interval is skewed downward (predictive
median 17.8%), because the countries compositionally closest to China in the error record,
post-communist and East Asian, saw unaffiliated shares fall in 1970-2010. **Folk and other
religions** have long upper tails for the same reason in reverse: the record's reclassifications
between folk religion and no religion. (For "Other" the central path lies just below the interval,
which describes the error-perturbed distribution, not the path.) The parameter spread alone would
have suggested intervals about half as wide for Christianity and the unaffiliated and a tenth as
wide for folk and other religions.

By 2100 the eight scenarios differ by less than the width of the predictive interval for every
group; the closest is the unaffiliated, with scenario means 6.7 pp apart against a predictive band
of 7.9 pp (`uncertainty_model_vs_scenario.csv`). What the stated scenarios vary matters less than
what the model has historically got wrong.

## 5. Where the change comes from

An exact split of each religion's change in world share, 2020-2100 (reference scenario,
`world_share_shift_share.csv`), into countries' own shares changing at fixed 2020 population
weights, the weights changing at fixed 2020 shares, and a small interaction:

| Religion | Change | Within countries | Population weighting | Interaction |
|---|---|---|---|---|
| Islam | +13.5 | +3.3 | +10.3 | −0.1 |
| Christianity | −3.0 | −8.7 | +6.5 | −0.8 |
| Hinduism | −2.9 | −0.6 | −2.4 | +0.1 |
| Buddhism | −2.4 | −1.1 | −1.7 | +0.4 |
| Unaffiliated | −4.6 | +7.3 | −12.5 | +0.5 |

About three quarters of Islam's rise is the faster population growth of Muslim-majority countries.
The unaffiliated share rises inside countries, by switching, and falls in the world, because the
countries where it is concentrated (China above all) grow more slowly. Christianity loses within
countries and gains from the growth of sub-Saharan Africa.

## 6. What each mechanism contributes

Each mechanism's contribution in 2100, the full model minus the same run with that mechanism
switched off, paired run by run on identical draws (`ablation_effects.csv`; mean and 5-95% of 12
paired runs, pp of world population):

| Mechanism | Christianity | Islam | Unaffiliated | Hinduism | Countries whose largest religion changes |
|---|---|---|---|---|---|
| Religious switching | −8.0 (−10.1 to −6.7) | −0.7 | +9.3 (+7.4 to +11.7) | −0.2 | 42 (30 to 50) |
| Fertility differences within countries | −0.7 | +2.4 (+2.0 to +3.0) | −0.9 | −0.4 | −1 |
| Migration | −0.2 | +0.3 | −0.3 | +0.1 | −2 |

Switching is what changes countries: without it the world Christian share would be 8 pp higher and
the unaffiliated share 9 pp lower in 2100, and some 42 fewer countries would change their largest
religion. Within-country fertility differences add about 2.4 pp to the Muslim share. Migration
moves no world share by more than about a third of a point, as it must in a model in which migrants
keep their religion: it relocates people and changes world shares only through what happens to
them afterwards.

**Does more migration make countries more mixed?** Slightly, under the calibrated religion of
migrants (`migrant_sorting_effect.csv`): rising minus low migration raises population-weighted
within-country diversity by a median 0.004 by 2100 (5-95% 0.004-0.005), in all 12 paired runs. If
migrants mirrored their origin the effect would be three times larger (0.013), and without
destination affinity about twice (0.007): migrants calibrated to Pew's figures mostly go where
their religion is already common. (An earlier version, whose unbounded minority effect drained
small minorities from emigration countries, found no effect.)

## 7. Countries whose largest religion changes

In the reference scenario, the largest religion changes by 2100 in 26 countries with predictive
probability above one half, and in 4 by 2050 (`dominant_change.csv`, `prob_changed_by_*_predictive`).
All but one are Christian-majority countries, or Buddhist or folk-majority ones in East Asia, where
the unaffiliated become the largest group:

| Country | Probability by 2050 | Probability by 2100 |
|---|---|---|
| France | 55% | 89% |
| United Kingdom | 42% | 85% |
| Germany | 30% | 78% |
| Australia | 58% | 74% |
| Canada | 32% | 69% |
| Chile | 16% | 65% |
| Spain | 10% | 61% |
| United States | 14% | 42% |

Mongolia, Singapore and Taiwan (Buddhist or folk to unaffiliated) have the highest probabilities
(93%, 91%, 86%), and North Macedonia's most likely change is from Christianity to Islam (77%). The
share of parameter runs that change (`prob_changed_by_*`) is much higher for many of these, 100% for
France, the United Kingdom and Germany: without forecast error the model would state as nearly
certain what it can only call likely.

## 8. What the results turn on

A global sensitivity analysis over the drawn parameters, including the switching hyperparameters
each run draws, on 120 runs of the reference scenario separate from the projection runs
(`sensitivity_coefficients.csv`; standardised rank regression coefficients, R² of the linear
reading in brackets). A placebo, drawn like a parameter but used nowhere, reaches |0.15| at 2050 and
2100, which is the noise floor of 120 runs:

| Outcome | 2050 | 2100 |
|---|---|---|
| Christian world share | `survey_weight` −0.70 (R² 0.63) | `survey_weight` −0.51 (0.50) |
| Muslim world share | `psi` +0.69 (0.73) | `Hf` +0.41, `survey_weight` +0.38, `psi` +0.34 (0.63) |
| Unaffiliated world share | `survey_weight` +0.45, `psi` −0.33 (0.54) | `survey_weight` +0.25, `delta` +0.24 (0.43) |

`survey_weight`, how far switching follows Pew's survey level rather than the level fitted to
historical net change, is the most influential assumption for the Christian and unaffiliated
shares. For the Muslim share in 2050 the most influential is `psi`, the fraction of the global
median-age gap between religions applied inside countries; its inputs, Pew's 2010 median ages by
religion, are marked unverified in `config/assumptions.json` and must be checked before the result
is cited. `Hf`, how fast within-country fertility gaps converge, matters by 2100. The estimation
uncertainty of the switching hyperparameters (`delta`, `beta_d`, `tau_u`) is at or just above the
noise floor: it matters less than the choice between the two levels of switching. The bound on the
minority effect (`selectivity_cap`) matters little for world shares (at most 0.21, for Judaism).

## 9. Migration

Starting from the UN 1990 foreign-born stocks, the migration model reproduces each country's 2020
foreign-born share with a population-weighted error of 0.97 pp at the central circulation rate,
against 1.76 pp for the 1990 share unchanged (correlation with the UN 0.91; 276 million
foreign-born worldwide against the UN's 252 million, 254 million with no extra circulation;
`migration_foreign_born_check.csv`). The origin mix of simulated 1990-2020 arrivals in the 25
largest destinations correlates 0.67 with the growth of UN bilateral stocks at margin softness 0.75
(0.64 with exact margins; `migration_corridor_check.csv`). Capping any origin's share of a
destination's arrivals at 1.5 to 4 times its share of the stock lowers that fit at every softness
(0.52-0.59), and observed arrivals were more concentrated by origin than the model simulates
(largest origin 41% of arrivals against 31%), so no cap is applied.

With soft margins, a run's net migration departs from WPP's by 27% of the world's total absolute
net migration on average, 2020-2100 (`projection_report.json`, `migration_net_gap_to_wpp_mean`):
the margins give way where WPP's projected nets conflict with the migrant network. In the
projection, the largest single origin supplies a much larger share of some destinations' arrivals
in 2020-2050 than of their 2020 migrant stock (`migration_corridor_concentration.csv`), notably
Pakistan into the United Kingdom (36% of arrivals against 8% of the stock) and Turkey into Germany
(26% against 12%), because WPP 2024 keeps South Asian emigration high while Gulf net immigration
falls to almost zero after 2030; results for such destinations, including the United Kingdom's
projected Muslim share of 25% in 2100, should be read with that in mind.

The bound on the minority effect keeps small minorities in emigration countries close to their
census trajectories: Christians in Pakistan go from 1.3% in 2020 to 0.8% in 2050 and 0.7% in 2100
(0.4% and 0.15% unbounded), and in Bangladesh from 0.30% to 0.23% and 0.20% (0.04% and 0.01%).

## 10. Against Pew Research Center's 2015 projection

Pew Research Center's 2015 report projected the same quantity to 2050. Change in world share,
2020-2050, as each projects it (`benchmark_vs_pew2015.csv`):

| Religion | This model | Pew 2015 | Difference | 2020 level difference |
|---|---|---|---|---|
| Islam | +6.1 | +4.8 | +1.3 | +0.7 |
| Unaffiliated | −3.4 | −2.4 | −1.0 | +8.6 |
| Christianity | −1.0 | +0.2 | −1.2 | −2.3 |
| Buddhism | −1.1 | −1.4 | +0.3 | −2.5 |
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
