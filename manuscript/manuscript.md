# How predictable is the religious composition of countries? A probabilistic cohort-component projection and its out-of-sample evaluation

Conrad Flick

*Draft for submission. Every number in this draft is taken from the committed run in `results/`;
`manuscript/README.md` lists which file each comes from. Text in [square brackets] marks what
still has to be done before submission.*

## Abstract

Projections of the world's religious composition are cited widely but rarely evaluated, and
rarely carry honest uncertainty. We build a probabilistic cohort-component projection for 200
countries, by religion, migrant generation and age, driven by fertility, mortality, religious
switching and migration, with every change in share attributed exactly to its mechanism, and we
evaluate it on the decades 1970-2010 with every parameter fitted only to data available at the
forecast origin. Over 558 country-decades no variant of the model is distinguishable from assuming
no change: the demographic model is at most about 2% better than persistence, and switching fitted
to historical net change does not help. The model's own Monte Carlo bands contain the observed
share 19-20% of the time at nominal 90%. An empirical error model fitted to the model's past
forecasts, in which error scales as (s(1−s))^0.85 and grows with horizon as h^0.34, gives predictive
intervals that cover 89-92% of held-out observations at nominal 90% for horizons of 10 to 40 years,
and 90% of world totals. Conditional on the UN's national demography, the world Muslim share rises
from 25.6% in 2020 to 38.7% in 2100 (90% predictive interval 36.5-42.5%) and the Christian share
falls to 25.8% (22.3-29.3%); four fifths of Islam's rise reflects the faster population growth of
Muslim-majority countries rather than change within countries, while religious switching drives
most within-country change. We also show that two estimation errors common in this setting, a
survey likelihood that counts respondents repeatedly and an importance sampler drawn from the
prior, changed substantive conclusions.

## 1. Introduction

Projections of the world's religious composition are widely cited, and the best known of them
(Pew Research Center 2015, with methods in Hackett et al. 2015 [verify]) are deterministic
cohort-component projections: fertility, mortality, religious switching and migration are applied
to each religion's population by age and sex, under one set of assumptions. They are reported
without uncertainty intervals, and they are rarely evaluated against what actually happened. The
question of how far such a model improves on assuming that nothing changes, and how wide its
honest uncertainty is, has to our knowledge not been answered for religious composition.

This paper builds a probabilistic version of that model for 200 countries and asks three
questions of it. First, does a mechanistic projection forecast the decades 1970-2020 better than
assuming no change, once every parameter is fitted only to data available at the forecast origin?
Second, how large is its forecast error, how does that error grow with horizon, and can it be
turned into predictive intervals that are calibrated out of sample? Third, conditional on stated
assumptions, which mechanisms account for projected change in the world's religious composition
to 2100, and how much of that change is change within countries rather than in where the world's
population lives?

The contribution is as much about what such a projection can support as about the projection
itself. First, at decadal horizons the projection cannot be distinguished from persistence, and
switching fitted to historical net change makes it worse rather than better. Second, the
uncertainty such a model reports from its own parameters is several times too narrow, but an
empirical error model fitted to the model's own past forecasts gives predictive intervals that are
calibrated out of sample at horizons of 10 to 40 years, for countries and for world totals. Third,
with those intervals, the projection to 2100 still separates the largest groups, and most of the
projected change in world composition comes from differences in population growth between
countries rather than from change within them.

## 2. Data

**Religious composition.** Country shares for 2010 and 2020 come from Pew Research Center (2025),
harmonised to eight groups: Christianity, Islam, Hinduism, Buddhism, Judaism, folk or traditional
religions, other religions, and the religiously unaffiliated. Pew reports folk religions inside
"other religions"; they are split using each country's ratio in the World Religion Project, and
the split is labelled as a proxy. Historical composition for 1950-2010 comes from the World
Religion Project (Maoz and Henderson 2013), national file, every five years, harmonised to the
same eight groups. Its country coverage grows over time, so the historical test windows score
117 to 164 countries, and Indonesia is missing in 1980 and 1985.

**Demography.** National fertility, mortality, mean age at childbearing, population and net
migration for 1950-2100 come from the UN World Population Prospects 2024 (estimates to 2023 and the
medium variant after), with population by five-year age group and sex.

**Migration.** Bilateral migrant stocks by origin and destination, 1990-2024, from the UN
International Migrant Stock 2024; Natural Earth boundaries for distances, borders and continents.

**Religion-specific inputs.** 67 verified survey cells of lifetime religious switching (share of
adults raised in one religion who now identify with another) from 48 survey rows in 33 countries;
published religion-specific fertility ratios (country figures for India, Israel, Nigeria and the
United States, regional and world figures from Pew 2015); and 19 published figures on the
religious composition of migrants (Pew 2024). Each is transcribed with its source and an evidence
grade in `inputs/`.

## 3. Model

### 3.1 State and step

The state is persons by country (200), religion (8), migrant generation (native, foreign-born,
native-born child of a foreign-born mother) and five-year age group (17, the last open at 80+),
moved forward in five-year steps. Each step applies, in order: survival, births, a rescaling of
each country's natural growth to WPP (to 2100), religious switching, emigration and immigration.
The change in every country's religious shares is recorded at each sub-step, so the decomposition
of change by mechanism adds up exactly to the simulated change.

**Survival** uses a Siler-type hazard fitted to WPP life expectancy at birth and under-five
mortality; the open age group follows
`N_80+(t+5) = (5L80 / 5L75) N_75-79(t) + (T85 / T80) N_80+(t)`.

**Births** to women of religion *r* and generation *g* in country *c* are
`B = TFR_c · k_c · rel[c,r,g] · Σ_a f_c(a) W[c,r,g,a]`, where `W` is woman-years, `f_c` a fertility
age schedule matching WPP's mean age at childbearing, and `k_c` normalises so that the country
total reproduces WPP's TFR exactly. The relative fertility `rel` comes from the most local
published figure available; regional and world ratios are damped, because a ratio measured across
countries mostly reflects where each group lives rather than within-country differences. Gaps
converge towards zero with a half-life of 30-80 years. Children take the mother's religion.
Mortality does not differ by religion.

**Religious switching** is parameterised by three lifetime probabilities per country:
disaffiliation `d_r` (raised in *r*, now unaffiliated), conversion `v_r` (raised in *r*, now another
religion, destinations in proportion to local prevalence) and affiliation `a` (raised unaffiliated,
now religious). The lifetime matrix is spread over ages 15-49 by solving for five-year
age-specific matrices whose product reproduces it, so that a survey measure of lifetime switching
is never treated as an annual rate.

**Migration** is a gross origin-destination flow matrix per step whose net per country equals
WPP's projected net migration to 2100, fitted by Sinkhorn scaling with soft margins to a kernel
that mixes the observed migrant network with a gravity term; the softness of the margins moves
flows between corridors but leaves the world volume of migration unchanged. Who moves is drawn from
each origin's cells in proportion to an age schedule, a generation propensity and a
corridor-specific religious mix calibrated to Pew's published composition of migrants: migrants
favour destinations where their religion is common, and minorities emigrate more, with a
religion's propensity per person bounded at three to six times its origin's average (unbounded,
the effect drains small minorities in high-emigration countries within decades). The same persons
leave and arrive, so migration conserves every religion's world total exactly.

### 3.2 Estimation of switching

Lifetime rates follow a hierarchical logit model,

`logit d[c,r] = μ_d[r] + δ + β_d z_c + τ_u ξ_c + τ_e ξ_{c,r}`,
`logit a[c] = μ_a + β_a z_c + τ_a ξ′_c`,  `logit v[c,r] = μ_v[r] + τ_v ξ″_c`,

where `z_c` is a development index (standardised life expectancy and negative log fertility), the
`μ` are prior centres ordered as in Pew (2025), and the ten country effects `ξ` are standard
normal. The hyperparameters `H = (δ, β_d, τ_u)` are estimated by maximising the marginal
likelihood of two kinds of evidence, with the country effects integrated out.

*Net change.* A demographic and migration hindcast of each historical decade without switching
leaves a residual in every country's shares. Its link to the rates is the first-order effect of
switching, given each religion's population exposed at switching ages, and its likelihood is
Student-t with four degrees of freedom, robust to breaks between data rounds. Because the hindcast
contains births, deaths, ageing and migration, only the part they leave unexplained is attributed
to switching. The exposure follows the engine's order of operations (people age, then switch), so a
cohort aged *a* at the start of a decade meets the switching rates of ages *a*+1 and *a*+2.

*Surveys.* Each survey row, the adults of one country raised in one religion in one survey, is one
Dirichlet-multinomial observation of the cells it reports, at the probabilities the model gives
them, plus a complement cell for what it does not report. A reported conversion "raised *r*, now
*s*" has probability `v_r` times the model's share of converts reaching *s*. The concentration
`α = 100` limits a row to the information of about a hundred respondents however large the survey,
allowing for design effects and for the model's simplifications; α = 30 and 100 have equal marginal
likelihood and 300 lower.

*Integration.* The country integrals are estimated by importance sampling with 512 draws per
country from a three-component defensive mixture (Hesterberg 1995 [verify]): the prior (20%); a
multivariate t centred on the country's posterior mode with the inverse curvature there as scale,
that is, Laplace importance sampling (40%); and a t matched to the importance-weighted moments of
a pilot sample, shrunk towards the Laplace scale when the pilot's effective sample is small (40%),
which covers curved posteriors. Weights carry the ratio of prior to proposal density, so the
estimator is unbiased for every `H`. Because the effects are standard normal whatever `H` is, one
set of draws serves every `H` and the estimated likelihood is smooth in it. The proposal matters:
ten survey rows locate the United States' effects to within about ±0.02, where prior draws, or a
Gaussian fitted to degenerate weights, leave an effective sample of one or two.

*Maximisation.* The estimated log marginal likelihood is maximised by Nelder-Mead from the three
best points of a coarse grid, in unbounded coordinates (a scaled logit of `(δ, β_d, log τ_u)` on
the prior box `δ ∈ [−1.5, 1.5]`, `β_d ∈ [−0.5, 2.4]`, `τ_u ∈ [0.4, 2.0]`, on which the hyperprior is
flat). The proposal is then re-centred on the optimum and the search restarted, until the optimum
moves by less than 0.02, because each country's posterior moves with `H`.

*Hyperparameter uncertainty.* The curvature of the estimated log marginal likelihood at its
maximum, taken from a least-squares quadratic fitted to 27 points about one standard error away
(which averages out the Monte Carlo noise a narrow finite-difference stencil would amplify), gives
a Laplace approximation to the posterior of `H`, truncated to the box. Each Monte
Carlo run draws its own `H` from it and then each country's effects from their posterior at that
`H`, so the projection does not condition on the point estimate (Kass and Steffey 1989 [verify]).
Three replicate fits with independent draws are used across runs, run *r* using replicate *r* mod 3,
so the remaining Monte Carlo error of the fit is carried too. A parametric simulation study under
the real design (evidence simulated from the fitted `H` for the same countries, decades and survey
rows, then refitted) checks the estimator's bias and the coverage of its intervals (section 5.2).

Pew's 2025 global figure for adults aged 18-54 defines a second, "survey" level of switching
through a logit shift per religion, recalibrated at each run's `H`, and each run draws a weight
between the fitted level and the survey level.

### 3.3 Uncertainty

Three sources are kept apart. Parameter uncertainty is the spread of 40 Monte Carlo runs per
scenario, each drawing every uncertain parameter (ranges in `config/assumptions.json`), the
switching hyperparameters from their Laplace approximation, one posterior draw of every country's
switching rates and one of three replicate fits. Scenario uncertainty is the range across eight scenarios that vary switching,
migration and fertility assumptions. Forecast error, the error the model has made historically, is
added by the error model of section 4.3 to give predictive intervals to 2100.

## 4. Evaluation design

### 4.1 Point forecasts

Each World Religion Project decade from 1970-1980 to 2000-2010 (and Pew 2010-2020 when the Pew
workbook is available) is forecast from its first year, with switching fitted only on decades that
end by then. National demography inside each window is WPP 2024's estimate, so every model is
scored conditional on national fertility, mortality and net migration. The score is the
total-variation distance between forecast and observed shares, `½ Σ_k |ŝ_k − s_k|`, weighted by
population over countries. Models: persistence (shares unchanged); a naive trend (the previous
decade's observed change repeated); a hybrid (births, deaths and migration plus the previous
decade's unexplained change); births and deaths only; plus migration; plus switching at strength
0.5 and 1 (1 being the projection's setting); and plus switching at the strength that scored best
on earlier decades.

### 4.2 Inference

With four or five test decades, an exact paired test at the decade level cannot fall below
p = 0.125. Models are therefore also compared with persistence country by country: the
population-weighted mean difference in error over all country-decades, with a 95% interval from a
bootstrap that resamples countries (all of a country's decades together). Because countries within
a decade share common shocks, which that interval does not capture, the decade-level sign-flip
test is reported alongside as the conservative bound.

### 4.3 Forecast-error model and predictive intervals

From each origin 1970, 1980, 1990 and 2000 the model is run forward 40 times with everything fitted
as it would have been at the origin, and scored at every later decade to 2010, giving forecasts at
horizons of 10 to 40 years. The history runs have the projection's structure: development and the
convergence of fertility gaps evolve from the origin exactly as they do from 2020. With *s* the mean
forecast share, the error is modelled as

`e = (h/10)^β · (s(1 − s) + 10⁻⁴)^b · u`,

with `b` estimated from the relation between |e| and s(1 − s) at ten years, over shares observed
above zero (a group recorded at exactly zero has an error equal to its forecast by construction),
and `β` from the growth of the mean absolute standardised error with horizon. Predictive draws add
`(h/10)^β (s(1−s)+10⁻⁴)^b u` to each Monte Carlo run. The standardised error `u` is resampled in two
stages: one historical decade for the whole world, which keeps the common shock of that decade and
so the cross-country correlation that matters for world totals; then, for each country, the whole
eight-religion error vector of one of its 15 nearest neighbours in that decade, by total-variation
distance between forecast compositions (a k-nearest-neighbour bootstrap; Lall and Sharma 1996
[verify]). Matching on composition keeps an error measured on a tiny minority from being applied to
a majority. Each draw is one error path, the same `u` at every horizon. Errors are used as recorded. In
1970-2010 the unaffiliated share was consistently observed below the forecast, mostly in post-
communist and East Asian countries, and that direction is carried into the intervals; centring the
errors was tested and calibrates slightly worse, and is reported as a sensitivity.

The intervals are validated out of sample in calendar time: for each forecast in the record, `b`,
`β` and the resampling pool are re-estimated from the entries that share no calendar years with it,
and the forecast is scored for coverage and for the interval score of Gneiting and Raftery (2007).
A 1970→1990 forecast is therefore never scored with the 1980-1990 error in the pool. A stricter
real-time variant uses only entries that had ended by the forecast's origin. Coverage is reported
over shares observed above zero, because a group recorded at exactly zero is inside any interval
that reaches zero, which the clipping of shares at zero makes common. With four decades, no
40-year forecast has a non-overlapping entry, so calibration can be checked to 30 years.

## 5. Results

### 5.1 The model does not beat persistence at decadal horizons

Table 1 gives the population-weighted total-variation error of ten-year forecasts of the four
World Religion Project decades from 1970 to 2010. Persistence errs by 4.41 pp. Births and deaths
alone err by 4.38 pp (−0.6%), adding migration changes nothing, and adding switching at the
projection's strength raises the error to 4.90 pp (+11%). A naive trend that repeats the model's
last-decade residual errs by 5.85 pp (+33%).

**Table 1.** Ten-year forecast error, World Religion Project decades 1970-2010 (population-weighted
total-variation distance, pp), and the country-level difference from persistence with a 95%
bootstrap interval over countries.

| Model | Error | vs persistence | Difference, country level | 95% interval |
|---|---|---|---|---|
| Persistence | 4.41 | – | – | – |
| Trend (last decade repeated) | 5.85 | +33% | +1.71 | +1.03 to +2.25 |
| Births and deaths | 4.38 | −0.6% | −0.02 | −0.10 to +0.06 |
| + migration | 4.38 | −0.6% | −0.02 | −0.08 to +0.06 |
| + switching, strength 1 | 4.90 | +11% | +0.48 | −0.19 to +1.15 |
| + switching, strength chosen on earlier decades | 4.52 | +2.6% | +0.12 | −0.08 to +0.30 |

Country by country (Figure 2; 558 country-decades in 171 countries), the difference from
persistence is −0.02 pp for births and deaths (95% interval −0.10 to +0.06), +0.48 pp with
full-strength switching (−0.19 to +1.15) and +1.71 pp for the naive trend (+1.03 to +2.25). Only
the trend is distinguishable from persistence, and it is worse. The demographic model is at most
about 2% better than assuming no change. Because countries in a decade share common shocks, the
country bootstrap understates uncertainty, so the conclusion that no mechanistic variant is
distinguishable from persistence holds a fortiori. The decade-level sign-flip test agrees
(p ≥ 0.375 for every mechanistic variant; with four decades it cannot fall below 0.125).

Switching fitted to historical net change alone does not help. In every fold its country spread
`τ_u` reaches the upper bound of the prior range, and a model that is free to fit large
country-specific effects reproduces country trends in the residuals of earlier decades. Those
trends do not persist, which is why the naive trend fails, and switching fitted this way fails for
the same reason.

### 5.2 Forecast error grows slowly, and calibrated intervals can be built from it

The error record yields b = 0.85 and β = 0.34: errors scale nearly in proportion to s(1 − s), and
grow with horizon more slowly than a random walk. Mean absolute standardised error is 0.49, 0.59,
0.75 and 0.77 at horizons of 10, 20, 30 and 40 years.

The model's Monte Carlo bands contain the held-out observation 19-20% of the time at nominal 90%,
at every horizon (Figure 3). The error-calibrated intervals, re-estimated without the origin they
are tested on, cover 89.0%, 91.3%, 91.0% and 92.3% at horizons of 10, 20, 30 and 40 years, and
52%, 81%, 90% and 95% at nominal 50%, 80%, 90% and 95% averaged over horizons. Their interval
scores are less than half as large (10.8 against 21.8 pp at ten years; 18.9 against 48.9 at forty).
For the world totals of the observed countries, the 90% intervals contained 90.0% of held-out
values, against 13.8% for the Monte Carlo bands.

**Table 2.** Leave-one-origin-out calibration of 90% intervals for country × religion shares.

| Horizon | Parameter-only coverage | Error-calibrated coverage | Interval score, parameter-only | Interval score, calibrated |
|---|---|---|---|---|
| 10 years | 18.7% | 89.0% | 21.8 | 10.8 |
| 20 years | 19.9% | 91.3% | 33.7 | 13.8 |
| 30 years | 18.8% | 91.0% | 43.4 | 17.6 |
| 40 years | 19.4% | 92.3% | 48.9 | 18.9 |

### 5.3 Projections to 2100

Figure 1 shows world shares in the reference scenario with both kinds of band. Conditional on
WPP 2024, the Muslim share rises from 25.6% in 2020 to 31.6% in 2050 (90% predictive interval
29.5-34.1%) and 38.7% in 2100 (36.5-42.5%). The Christian share falls from 28.8% to 27.7% (25.4-29.9%)
and 25.8% (22.3-29.3%), so that by 2100 the two intervals no longer overlap. The unaffiliated share
falls from 24.2% to 19.6% (12.5-21.1%), the Hindu share from 14.9% to 12.1% (8.1-13.4%) and the
Buddhist share from 4.1% to 1.8% (1.5-3.6%).

The intervals are asymmetric where the error record is. The unaffiliated interval is skewed
downward, and the folk and other religions have long upper tails, because the countries
compositionally closest to China in the record, post-communist and East Asian, saw large
reclassifications between no religion, folk religion and Christianity between rounds of the World
Religion Project. Parameter uncertainty alone would have given intervals between about two fifths
and a twentieth as wide, and by 2100 the eight scenarios differ by less than the width of the
predictive interval for every group.

At the country level (Figure 6), the largest religion is more likely than not to change by 2100 in
27 countries, almost all Christian-majority countries where the unaffiliated become the largest
group: France (78%), Australia (78%), the United Kingdom (75%), Germany (69%) and Canada (67%), with
the United States close to even (47%). Without forecast error the model would put the first three
at 100%.

### 5.4 Switching changes countries; population growth changes the world

An exact decomposition of the change in each religion's world share between 2020 and 2100 (Figure
4) separates change within countries, at fixed 2020 population weights, from change in the weights.
Of the Muslim share's rise of 13.0 pp, 10.4 pp is population weighting, the faster growth of
Muslim-majority countries, and 2.7 pp change within countries. The unaffiliated share rises within
countries by 7.2 pp but falls in the world by 4.5 pp, because the countries where it is concentrated
grow more slowly (−12.5 pp). Christianity loses 8.5 pp within countries and regains 6.4 pp through
the growth of sub-Saharan Africa.

Mechanism ablations (Figure 5) attribute to switching −8.1 pp of the world Christian share in 2100
(5-95% of paired runs −9.8 to −6.8), +9.5 pp of the unaffiliated share (+8.2 to +11.8) and the
change of largest religion in about 41 countries (33 to 51). Within-country fertility differences
add 2.0 pp to the Muslim share (1.6 to 2.5). Migration moves no world share by more than a quarter
of a point: migrants keep their religion, so migration changes world shares only through what
happens to them after they move. Under the calibrated religion of migrants, rising rather than low
migration does not make countries more religiously mixed by 2100 (median change in
population-weighted Gini-Simpson diversity −0.0003), because migrants go disproportionately where
their religion is already common; if migrants mirrored their origin, every run would be more
diverse.

### 5.5 What the results turn on

In a global sensitivity analysis over 23 drawn parameters, the weight given to the survey level
of switching rather than the fitted level is the most influential assumption for the Christian
world share (standardised rank coefficient −0.78 in 2050, −0.60 in 2100). For the Muslim share in
2050 the most influential is the strength of the within-country age tilt between religions
(+0.71), whose inputs, Pew's 2010 median ages by religion, are [to be verified]. The convergence
half-life of within-country fertility gaps matters by 2100 (+0.35). By 2100 no single assumption
explains most of the spread (R² 0.21-0.58).


## 6. Discussion

Three results stand out, and two of them concern what the model cannot do.

First, a careful mechanistic projection is no better than assuming no change over ten-year
horizons, and the demographic part of it is at most about 2% better. This is not a failure of a
particular specification: births, deaths, ageing and migration move religious shares slowly, and
most of what changes a country's measured composition in a decade is either switching, which the
historical record identifies poorly, or measurement, which no model of behaviour can forecast. The
naive trend is the clearest warning. Repeating recent change is 33% worse than persistence, and
switching fitted freely to historical net change fails for the same reason: much of the country
level change between rounds of the World Religion Project does not continue.

Second, the uncertainty a projection reports from its own parameters is the wrong uncertainty.
The Monte Carlo bands of this model, like any band built from parameter draws alone, contain the
truth about a fifth as often as they claim, because they omit the error that dominates. An
empirical error model fitted to the model's own past forecasts restores calibration at every
horizon available, at the country level and for world totals, at the price of intervals that are
wide at the country level. Error grows with horizon roughly as h^0.34, which is slower than a
random walk and makes long-range intervals narrower than a naive extrapolation of ten-year errors
would imply. The approach is general: it needs nothing but a model that can be run from past
origins and a record to score it against.

Third, conditional on the UN's demography and on stated assumptions, the projection still says
something definite about the world, and it says it through population growth rather than through
belief. Four fifths of Islam's projected rise is the faster growth of Muslim-majority countries,
and the unaffiliated share falls in the world while it rises in most countries. Both conclusions
rest mainly on WPP's national fertility projections, which the intervals here take as given; they
would be the first thing to make probabilistic in extending this work, for instance with the UN's
own probabilistic projections. Switching, by contrast, is what changes countries, and its level is
the assumption the results are most sensitive to and the one that history identifies least well.

A methodological lesson runs through the revision of the model itself. Two errors in the
estimation of switching, a likelihood that counted survey respondents several times over and an
importance sampler whose output depended on its seed, changed substantive conclusions: the first
manufactured most of an apparent disagreement between survey and historical evidence, and the
second, through the downward bias of a log-mean of noisy weights, made the historical evidence
appear to favour small country differences in switching. Both were found by checking the
estimator rather than its output, which we recommend for any model of this kind.

## 7. Limitations

The evaluation is conditional on national demography: the historical windows use WPP 2024
estimates, not the projections available at the time, and the projection takes WPP's medium
variant as given, so uncertainty in national fertility, the main driver of world totals through
population weighting, is absent from every interval. The error record covers horizons to 40 years
and one source of historical composition; the error growth law is extrapolated to 80 years, and
the record's measurement noise is assumed representative of future measurement. Switching is
identified by 67 survey cells in 33 countries and by historical net change that the tests show to
be a poor guide; the weight between the survey and the fitted level is the most influential
assumption. Religion-specific fertility is measured for few countries, the religion of migrants
is calibrated to aggregate figures, and the within-country age tilt between religions rests on
median ages still to be verified. The model has no intermarriage, no religion-specific mortality,
no sub-national variation and no shock process for conflict or persecution. Beyond 2100 every input
is an assumption, and those horizons are reported as exploratory only.

## Data and code availability

All code, the inputs transcribed from publications, the configuration and the results of the run
reported here are in the repository [URL; archive a tagged release on Zenodo for a DOI before
submission]. The UN, World Religion Project and Natural Earth data are public and are downloaded by
the code, with checksums of the exact files used recorded in `config/data_manifest.json`. The Pew
2010-2020 country workbook requires a free account and is not redistributed.

## Use of AI tools

Most of the code and documentation for this study was written with an AI coding assistant (Claude,
Anthropic) under the author's direction. The author specified the questions, reviewed the methods
and results, and takes responsibility for the content. Every reported number is produced by the
code from documented inputs and can be regenerated with `python run.py all`. [Adapt to the target
journal's policy.]

## References

[Verify every reference against the original before submission.]

- Gneiting, T. and Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and
  estimation. *Journal of the American Statistical Association* 102(477), 359-378.
- Hackett, C., Stonawski, M., Potančoková, M., Grim, B. J. and Skirbekk, V. (2015). The future size
  of religiously affiliated and unaffiliated populations. *Demographic Research* 32(27), 829-842.
- Maoz, Z. and Henderson, E. A. (2013). The World Religion Dataset, 1945-2010: logic, estimates,
  and trends. *International Interactions* 39(3), 265-291.
- Pew Research Center (2015). *The Future of World Religions: Population Growth Projections,
  2010-2050.* Washington, DC.
- Pew Research Center (2025). *How the Global Religious Landscape Changed From 2010 to 2020.*
  Washington, DC.
- United Nations, Department of Economic and Social Affairs, Population Division (2024). *World
  Population Prospects 2024.* New York.
- United Nations, Department of Economic and Social Affairs, Population Division (2024).
  *International Migrant Stock 2024.* New York.
- [Add: probabilistic population projection (e.g. Raftery et al. 2012, PNAS); forecast accuracy
  of population projections (e.g. Keilman); importance sampling with defensive mixtures (Hesterberg
  1995; Owen and Zhou 2000); Dirichlet-multinomial overdispersion; religious switching measurement.]
