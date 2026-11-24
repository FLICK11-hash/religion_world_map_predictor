# Results

From the committed run in `results/`: reference scenario `stabilising`, 40 Monte Carlo runs per
scenario, seed 2026, start state Pew's 2020 estimates (`data/processed/pew_harmonized.csv`, from Pew's Global
Religious Futures dataset, identical to `inputs/pew2020_start_state.csv`), with Pew's 2010
estimates adding a fifth test decade. One integrity check fails in this run (9c, section 3). Every number here is in a file in `results/` (in its
`validation/`, `projection/` or `experiments/` folder); the run report
`results/comparison_report.md` has the full tables. Shares are percent of the population;
differences are percentage points (pp).

## 1. History tests: no variant beats assuming nothing changes

Ten-year forecasts of five decades, everything fitted only on earlier decades: the four World
Religion Project (WRP) decades 1970-2010 and Pew's decade 2010-2020, measured by the source the
projection starts from. Population-weighted total-variation (TV) error of country shares, mean over
the decades (`validation_summary.csv`):

| Model | WRP 1970-2010 | Pew 2010-2020 | All five decades | Against persistence |
|---|---|---|---|---|
| Persistence (no change) | 4.41 | 3.44 | 4.21 | – |
| Trend (the last decade's change repeated) | 5.97 | 4.45 | 5.67 | +35% |
| Births, deaths and migration + the last decade's unexplained change | 5.86 | 4.47 | 5.58 | +32% |
| Births and deaths | 4.38 | 3.43 | 4.19 | −0.5% |
| + migration | 4.37 | 3.41 | 4.18 | −0.8% |
| + switching, strength 0.5 | 4.57 | 3.28 | 4.31 | +2.4% |
| + switching, strength 1 (as projected) | 4.92 | 3.20 | 4.58 | +8.6% |
| + switching, strength chosen on earlier decades | 4.60 | 3.41 | 4.36 | +3.5% |

Country by country, over 758 country-decades in 200 countries (`inference.csv`), with 95% intervals
from a bootstrap over countries and the exact decade-level sign-flip test (five decades, so p cannot
fall below 0.0625):

| Model | Difference from persistence (pp) | 95% interval | Decades better | p (decades) |
|---|---|---|---|---|
| Trend | +1.61 | +0.80 to +2.34 | 0 of 5 | 0.0625 |
| Demography + last decade's unexplained change | +1.52 | +0.69 to +2.27 | 0 of 5 | 0.0625 |
| Births and deaths | −0.02 | −0.06 to +0.06 | 3 of 5 | 0.63 |
| + migration | −0.03 | −0.07 to +0.05 | 4 of 5 | 0.56 |
| + switching, strength 1 | +0.26 | −0.30 to +0.82 | 3 of 5 | 0.88 |
| + switching, chosen | +0.12 | −0.10 to +0.35 | 3 of 5 | 0.88 |

Three things follow. **Repeating recent change is clearly worse than assuming none**, whether the
change repeated is the observed one or the part demography did not explain, and it is worse in every
one of the five decades. **Births and deaths alone are indistinguishable from persistence, and at
most about 2% better** (the lower end of the interval, −0.07 pp of 4.21 with migration). **Switching
fitted to historical net change does not help.** At full strength it is 12% worse in the WRP decades
and 7% better in Pew's (−0.24 pp, 95% interval −0.70 to +0.16), in neither case distinguishably.
The strength chosen on earlier decades falls from 1 (1970-1980) to 0.5 (1980-1990) and 0 for the
three later decades, Pew's included (`out_of_sample_choices.csv`). Fitted to net change alone, the
switching model chooses the largest country spread its prior range allows in each of the four WRP
folds, and 1.67 of a maximum of 2 for the Pew fold (`switching_fit_by_fold.csv`); that spread
reproduces country trends in the historical residuals that do not continue, the failure of the trend
baselines. The bootstrap treats countries as independent within a decade, so its intervals are if
anything too narrow; the conclusion that nothing is distinguishable from persistence holds a
fortiori. Richer demographic inputs change the error of the demographic forecasts by at most
0.04 pp, in both sources (`data_ablations_summary.csv`).

## 2. Forecast error and predictive intervals

Monte Carlo forecasts from 1970, 1980, 1990 and 2000, scored at every later WRP decade to 2010, and
from 2010 against Pew's 2020 estimates (`forecast_error_record.csv`: 758 country forecasts at 10
years, 391 at 20, 253 at 30 and 117 at 40). The fitted error model is
`e = (h/10)^β (s(1−s) + 10⁻⁴)^b u` with **b = 0.83** and **β = 0.38** (`forecast_error_model.json`):
error grows more slowly than a random walk (β = 0.5). Mean absolute standardised error is 0.33, 0.43,
0.51 and 0.53 at 10, 20, 30 and 40 years.

Out of sample (`predictive_calibration.csv`, scheme `non-overlapping`): for every forecast, the
error model is refitted on the record entries whose periods do not overlap it, and the forecast is
scored. When those entries all have a 10-year horizon, β cannot be estimated and is set to that of
a random walk (0.5). The one 40-year forecast, 1970-2010, has a single such entry, Pew's 2010-2020
decade. Share of country × religion shares observed above zero that fall inside the 90% interval,
and interval score (pp, lower is better):

| Horizon | Parameter-only | Calibrated (as projected) | Calibrated, real time | Score, parameter-only | Score, calibrated |
|---|---|---|---|---|---|
| 10 years | 23.2% | 88.4% | 88.9% | 25.7 | 12.2 |
| 20 years | 24.4% | 86.6% | 85.0% | 43.5 | 18.8 |
| 30 years | 24.7% | 84.7% | 88.7% | 56.7 | 26.3 |
| 40 years | 25.2% | 78.1% | – | 65.8 | 33.2 |

Over all cells, including groups recorded at exactly zero, coverage is 90.0%, 89.0%, 88.1% and
82.1%; for cells forecast at 20% or more it is 90.0%, 86.0%, 84.0% and 73.2%. For world totals of the
observed countries (`predictive_calibration_world.csv`), the 90% interval contained 78.4% of 88
held-out world shares (85.0% at 10 years, 83.3% at 20, 56.2% at 30, 75.0% at 40), and 76.8% of 56 in
real time; the parameter-only band contained 18.2%.

So the calibrated intervals are close to nominal for countries at 10-30 years but **a few points too
narrow**, about 12 points too narrow at 40 years, where they rest on one held-out decade, and coarser
for world totals, which rest on the common shocks of five decades. The design matters: the
leave-one-origin-out validation, which keeps the decades a forecast is scored on in the error model's
pool, reports 88-91% for countries and 91% for world totals. Adding the errors to the central path
only, rather than to every run, calibrates worse (85.7% against 87.0% pooled over horizons), and
centring the errors on their pooled mean changes little (87.2%) while moving world medians (below).
The model's own Monte Carlo bands are parameter uncertainty and nothing else: they contain the
truth about a quarter as often as they claim.

## 3. Religious switching

The empirical Bayes fit to historical net change (six WRP decades and Pew's 2010-2020) and 48 survey
rows gives, as the mean of three replicate fits (`projection_report.json`, `switching_fit`):
δ = −0.22 (standard error 0.15), β_d = 1.35 (0.11), τ_u = 1.01 (standard error of log τ_u 0.16).
The replicates differ by at most 0.15 standard errors (integrity check 9a), and every country's
importance sample has at least 65 effective draws of 512 (median 316; check 9b). Each projection run
draws its own hyperparameters from their Laplace approximation.

**Does the estimator recover what it estimates?** In 20 replications with evidence simulated from
these values under the real design (`estimator_recovery.csv`), δ and β_d are recovered well: bias
−0.05 (± 0.03) and −0.01 (± 0.01), root mean squared errors 0.13 and 0.05, and 90% Laplace intervals
that cover the truth in 90% and 100% of replications. **The country spread τ_u is not**: bias −0.11
(± 0.03) on the log scale, root mean squared error 0.17, and coverage 65% (13 of 20). Integrity check
9c requires at least 70% coverage and a bias no larger than the mean Laplace standard error (0.11),
so it **fails** for log τ_u, narrowly on both counts, and `run.py all` stopped before the figures
and the report; they were produced with `run.py figures` and `run.py report --export`, and the
failure is recorded in `results/integrity_checks.txt` and `results/run_stamp.json`. In practice the
fitted differences between countries in switching are about 10% too small (exp(−0.11) ≈ 0.90). This
narrows the parameter spread of the runs, not the predictive intervals, which come from the record's
errors, and τ_u is among the less influential inputs (section 8). The overall level δ is estimated
about 0.4 standard errors too low, which makes the fitted level of switching, if anything, slightly
conservative.

In Pew's measure, people raised in a religion who have left it per 100, adults 18-54 in 117
countries (`switching_check_vs_pew.csv`):

| Raised | Fitted level | Pew (2025) survey level |
|---|---|---|
| Christian | 13.3 | 17.1 |
| Buddhist | 13.3 | 22.1 |
| Muslim | 1.5 | 1.0 |
| Hindu | 1.4 | 1.0 |
| Unaffiliated (returned to a religion) | 7.5 | 7.5 |

An earlier version reported 11.7 against 17.1 for Christians; most of that gap was an error in the
survey likelihood (respondents counted several times over, and single conversion cells compared
with the probability of any conversion). Each projection run draws a weight between the two levels.

## 4. World shares to 2100

Reference scenario: the mean of the 40 runs (the central path), and the 90% predictive interval,
which adds the record's forecast errors (`global_share_by_scenario.csv`, columns `mean`, `pi05`,
`pi95`; `predictive_sensitivity_centring.csv` for the medians):

| Religion | 2020 | 2050 | 90% interval | 2100 | 90% interval |
|---|---|---|---|---|---|
| Islam | 25.6 | 31.7 | 29.7-34.2 | 39.2 | 36.6-43.2 |
| Christianity | 28.8 | 27.8 | 25.7-29.9 | 26.1 | 22.8-29.3 |
| Unaffiliated | 24.2 | 20.7 | 15.9-23.0 | 19.1 | 13.1-22.6 |
| Hinduism | 14.9 | 14.5 | 12.0-16.2 | 12.0 | 8.4-13.4 |
| Buddhism | 4.1 | 3.1 | 2.6-4.7 | 1.7 | 1.4-3.2 |
| Folk/Traditional | 1.4 | 1.3 | 0.7-3.9 | 1.0 | 0.5-4.2 |
| Other | 0.8 | 0.7 | 0.6-3.0 | 0.5 | 0.6-3.2 |
| Judaism | 0.2 | 0.2 | 0.1-0.2 | 0.2 | 0.1-0.3 |

What the intervals support. **Islam becomes the largest group:** the Muslim share passes the
Christian share in 2035 in the central path, its 2100 interval (36.6-43.2%) lies entirely above
Christianity's (22.8-29.3%), and from 2055 the two no longer overlap. **The Christian share
probably falls,** by up to 6 pp. **The unaffiliated share falls in the world,** even though it rises
inside most countries (section 5); its interval is skewed downward (predictive median 17.8%),
because the countries compositionally closest to China in the error record, post-communist and East
Asian, saw unaffiliated shares fall in 1970-2010. **Folk and other religions** have long upper tails
for the same reason in reverse: the record's reclassifications between folk religion and no
religion. (For "Other" the central path lies just below the interval, which describes the
error-perturbed distribution, not the path.) The parameter spread alone would have suggested
intervals about a third as wide for Christianity and the unaffiliated and less than a tenth as wide
for folk and other religions.

The eight scenarios differ by less than the width of the predictive interval for every group in
2050 and 2100; the closest case is Christianity in 2100, with scenario means 4.6 pp apart against a
predictive band of 6.4 pp (`uncertainty_model_vs_scenario.csv`). What the stated scenarios vary
matters less than what the model has historically got wrong.

## 5. Where the change comes from

An exact split of each religion's change in world share, 2020-2100 (reference scenario,
`world_share_shift_share.csv`), into countries' own shares changing at fixed 2020 population
weights, the weights changing at fixed 2020 shares, and a small interaction:

| Religion | Change | Within countries | Population weighting | Interaction |
|---|---|---|---|---|
| Islam | +13.6 | +3.3 | +10.3 | 0.0 |
| Christianity | −2.6 | −8.9 | +6.5 | −0.3 |
| Hinduism | −3.0 | −0.7 | −2.4 | +0.1 |
| Buddhism | −2.4 | −1.2 | −1.7 | +0.5 |
| Unaffiliated | −5.0 | +7.7 | −12.5 | −0.3 |

About three quarters of Islam's rise is the faster population growth of Muslim-majority countries.
The unaffiliated share rises inside countries, by switching, and falls in the world, because the
countries where it is concentrated (China above all) grow more slowly. Christianity loses within
countries and gains from the growth of sub-Saharan Africa. If every country kept its 2020
composition and only national populations changed as WPP projects, the world would be 35.9% Muslim
and 35.3% Christian in 2100: persistence alone brings Islam level with Christianity by the end of
the century, and change within countries brings the crossover forward to 2035.

## 6. What each mechanism contributes

Each mechanism's contribution in 2100, the full model minus the same run with that mechanism
switched off, paired run by run on identical draws (`ablation_effects.csv`; mean and 5-95% of 12
paired runs, pp of world population):

| Mechanism | Christianity | Islam | Unaffiliated | Hinduism | Countries whose largest religion changes |
|---|---|---|---|---|---|
| Religious switching | −7.1 (−8.0 to −6.0) | −0.7 | +8.8 (+7.8 to +10.6) | −0.4 | 34 (26 to 42) |
| Fertility differences within countries | −0.8 | +2.3 (+2.0 to +2.9) | −0.8 | −0.4 | −2 |
| Migration | −0.2 | +0.3 | −0.3 | +0.1 | −2 |

Switching is what changes countries: without it the world Christian share would be 7 pp higher and
the unaffiliated share 9 pp lower in 2100, and some 34 fewer countries would change their largest
religion. Within-country fertility differences add about 2.3 pp to the Muslim share. Migration
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

In the reference scenario, the largest religion changes by 2100 in 32 countries with predictive
probability above one half, and in 7 by 2050 (`dominant_change.csv`, `prob_changed_by_*_predictive`).
All but one are Christian-majority countries, or Buddhist or folk-majority ones in East Asia, where
the unaffiliated become the largest group:

| Country | Probability by 2050 | Probability by 2100 |
|---|---|---|
| France | 60% | 86% |
| United Kingdom | 54% | 83% |
| Australia | 67% | 78% |
| Germany | 45% | 76% |
| Canada | 49% | 72% |
| Chile | 26% | 71% |
| Spain | 21% | 66% |
| Brazil | 5% | 59% |
| United States | 23% | 56% |

Mongolia and Singapore (Buddhist to unaffiliated) have the highest probabilities (92% and 88%),
followed by Taiwan (folk to unaffiliated, 82%), and North Macedonia's most likely change is from
Christianity to Islam (67%). In the United States and Brazil the change is close to even: no
religion ends about a point ahead of Christianity in the mean path, with intervals that overlap
almost entirely. The share of parameter runs that change (`prob_changed_by_*`) is much higher for
many of these, 100% for France, the United Kingdom and Germany: without forecast error the model
would state as nearly certain what it can only call likely.

## 8. What the results turn on

A global sensitivity analysis over the drawn parameters, including the switching hyperparameters
each run draws, on 120 runs of the reference scenario separate from the projection runs
(`sensitivity_coefficients.csv`; standardised rank regression coefficients, R² of the linear
reading in brackets). A placebo, drawn like a parameter but used nowhere, reaches |0.12| at 2050 and
2100, which is the noise floor of 120 runs:

| Outcome | 2050 | 2100 |
|---|---|---|
| Christian world share | `survey_weight` −0.70, `beta_d` −0.20 (R² 0.70) | `survey_weight` −0.60 (0.57) |
| Muslim world share | `psi` +0.73, `survey_weight` +0.30 (0.77) | `Hf` +0.43, `survey_weight` +0.38, `psi` +0.34 (0.67) |
| Unaffiliated world share | `survey_weight` +0.37, `delta` +0.32, `beta_d` +0.26 (0.49) | `delta` +0.31, `beta_d` +0.29, `survey_weight` +0.25 (0.42) |
| Countries whose largest religion changes | | `survey_weight` +0.65, `beta_d` +0.49 (0.70) |

`survey_weight`, how far switching follows Pew's survey level rather than the level fitted to
historical net change, is the most influential assumption for the Christian share and the number of
countries that change. For the Muslim share in 2050 the most influential is `psi`, the fraction of
the global median-age gap between religions applied inside countries; its inputs are Pew's (2012)
median ages by religion, all eight checked against the report (folk and other religions corrected to
33 and 32 years for this run). `Hf`, how fast within-country fertility gaps converge, matters by
2100. The estimation uncertainty of the switching hyperparameters matters for the unaffiliated share,
where `delta` and `beta_d` are about as influential as `survey_weight`, and for the number of
countries that change (`beta_d` +0.49); for the Christian and Muslim shares it is near the noise
floor. `tau_u`, the parameter the estimator recovers worst (section 3), reaches at most 0.12 for the
Christian, Muslim and unaffiliated shares and 0.08 for the number of countries that change. The
bound on the minority effect (`selectivity_cap`) matters little for world shares (at most 0.12).

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
| Unaffiliated | −3.4 | −2.4 | −1.1 | +8.6 |
| Christianity | −0.9 | +0.2 | −1.2 | −2.3 |
| Buddhism | −1.1 | −1.4 | +0.3 | −2.5 |
| Folk/Traditional | −0.1 | −0.8 | +0.7 | −4.2 |
| Hinduism | −0.4 | −0.3 | −0.1 | −0.2 |

The two separately built models agree on the size of every group's change within 1.3 pp over
thirty years, and on its direction for six of the eight groups; the exceptions are Christianity
and Judaism (changes under 0.02 pp). They disagree far more about where 2020 started: Pew's 2015
estimate of 2020 differs from Pew's later data, used here, by up to 8.6 pp (the unaffiliated),
mostly because China is classified differently. Scored country by country, Pew's 2015 projection
of 2020 misses Pew's later measurement by 10.7 pp population-weighted, barely better than freezing
2010 (10.9), and China is 69% of that (`benchmark_pew2015_skill.csv`). No projection can be scored
more precisely than its measurements agree.

## 11. Against Pew Research Center's 2026 projections

Pew's newest projections (Hackett et al. 2026) start from the same 2020 estimates as this model:
the 2020 shares in Pew's Global Religious Futures dataset are identical, country by country, to
`inputs/pew2020_start_state.csv`. Pew holds recently observed switching, fertility differences and
migration constant and publishes no probabilistic intervals. `scripts/benchmark_pew2026.py`
compares the two projections (`benchmark_pew2026_world.csv`, `benchmark_pew2026_countries_2050.csv`,
`benchmark_pew2026_summary.json`); it is a check of agreement, not of accuracy.

- **World, 2030-2070.** Every one of Pew's world shares, for every group with an interval and every
  decade, lies inside this model's 90% predictive interval (30 of 30). The largest gaps are in the
  groups switching moves: 1.8 pp for Christianity and 2.3 pp for the unaffiliated by 2070, against
  0.5 pp for Islam. Both projections put Muslims ahead of Christians by 2035.
- **Countries, 2050.** The largest religion agrees in 196 of 200 countries; the exceptions are Canada
  (Christianity here, unaffiliated in Pew), Estonia (unaffiliated here, Christianity in Pew), and
  Mongolia and Singapore (unaffiliated here, Buddhist in Pew). 98.7% of Pew's 1,200 country-by-group
  shares lie inside this model's 90% predictive intervals. The population-weighted total-variation
  distance between the two is 3.0 pp. The largest differences are in Belarus (16 pp), Bolivia, Costa
  Rica and Ecuador (15 pp), where this model projects much more disaffiliation than Pew does.
- **Pew's own decade.** A no-change forecast of Pew's 2020 estimates from its 2010 estimates errs by
  3.35 pp population-weighted (seven groups, 201 countries; 3.44 pp in the eight groups and 200
  countries of the history tests), against 4.41 pp for WRP decades. This decade is now part of the
  history tests (section 1).

