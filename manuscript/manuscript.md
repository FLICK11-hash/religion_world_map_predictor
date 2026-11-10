# How predictable is the religious composition of countries? A probabilistic cohort-component projection and its out-of-sample evaluation

Conrad Flick

*Draft for submission. Every number in this draft is taken from the committed run in `results/`;
`manuscript/README.md` lists which file each comes from. Text in [square brackets] marks what
still has to be done before submission.*

## Abstract

[[ABSTRACT]]

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
itself. [[CONTRIBUTION SUMMARY: three findings]]

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
countries mostly reflects where each group lives rather than within-country differences. Children
take the mother's religion. Mortality does not differ by religion.

**Religious switching** is parameterised by three lifetime probabilities per country:
disaffiliation `d_r` (raised in *r*, now unaffiliated), conversion `v_r` (raised in *r*, now another
religion, destinations in proportion to local prevalence) and affiliation `a` (raised unaffiliated,
now religious). The lifetime matrix is spread over ages 15-49 by solving for five-year
age-specific matrices whose product reproduces it, so that a survey measure of lifetime switching
is never treated as an annual rate.

**Migration** is a gross origin-destination flow matrix per step whose net per country equals
WPP's projected net migration to 2100, fitted by Sinkhorn scaling with soft margins to a kernel
that mixes the observed migrant network with a gravity term. Who moves is drawn from each origin's
cells in proportion to an age schedule, a generation propensity and a corridor-specific religious
mix calibrated to Pew's published composition of migrants. The same persons leave and arrive, so
migration conserves every religion's world total exactly.

### 3.2 Estimation of switching

[[Section from docs/METHODS.md, "Rates come from a hierarchical model": hierarchical logit model;
net-change evidence with Student-t likelihood; survey rows as Dirichlet-multinomial; adaptive
defensive-mixture importance sampling; Nelder-Mead; replicate fits. Include the two-level
(history and survey) treatment.]]

### 3.3 Uncertainty

Three sources are kept apart. Parameter uncertainty is the spread of 40 Monte Carlo runs per
scenario, each drawing every uncertain parameter (23 of them, ranges in
`config/assumptions.json`), one posterior draw of every country's switching rates and one of three
replicate fits. Scenario uncertainty is the range across eight scenarios that vary switching,
migration and fertility assumptions. Forecast error, the error the model has made historically, is
added by the error model of section 4.3 to give predictive intervals to 2100.

## 4. Evaluation design

### 4.1 Point forecasts

Each World Religion Project decade from 1970-1980 to 2000-2010 (and Pew 2010-2020 when the Pew
workbook is available) is forecast from its first year, with switching fitted only on decades that
end by then. National demography inside each window is WPP 2024's estimate, so every model is
scored conditional on national fertility, mortality and net migration. The score is the
total-variation distance between forecast and observed shares, `½ Σ_k |ŝ_k − s_k|`, weighted by
population over countries. Models: persistence (shares unchanged); a naive trend (the model's
last-decade residual repeated); births and deaths only; plus migration; plus switching at strength
0, 0.5 and 1 (1 being the projection's setting); and plus switching at the strength that scored
best on earlier decades.

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
horizons of 10 to 40 years. With *s* the mean forecast share, the error is modelled as

`e = (h/10)^β · (s(1 − s) + 10⁻⁴)^b · u`,

with `b` estimated from the relation between |e| and s(1 − s) at ten years and `β` from the growth
of the mean absolute standardised error with horizon. Predictive draws add
`(h/10)^β (s(1−s)+10⁻⁴)^b u` to each Monte Carlo run, with `u` resampled by decade and then by
country within the decade, which keeps the common shock of a decade (and so the correlation that
matters for world totals) while giving every country the pooled error distribution. The intervals
are validated by leaving one origin out, re-estimating `b`, `β` and the resampling pool without
it, and scoring coverage and the interval score of Gneiting and Raftery (2007) on its forecasts.

## 5. Results

[[5.1 History tests and inference]]

[[5.2 Forecast error and calibration]]

[[5.3 Projections to 2100]]

[[5.4 Mechanisms: shift-share and ablations]]

[[5.5 Sensitivity]]

## 6. Discussion

[[DISCUSSION]]

## 7. Limitations

[[LIMITATIONS]]

## Data and code availability

All code, the inputs transcribed from publications, the configuration and the results of the run
reported here are in the repository [URL; archive a tagged release on Zenodo for a DOI before
submission]. The UN, World Religion Project and Natural Earth data are public and are downloaded by
the code, with checksums of the exact files used recorded in `config/data_manifest.json`. The Pew
2010-2020 country workbook requires a free account and is not redistributed.

## Use of AI tools

[[Statement: most of the code and documentation was written with an AI coding assistant (Claude,
Anthropic) under the author's direction; every reported number is produced by the code from
documented inputs. Check the target journal's policy for the required wording.]]

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
