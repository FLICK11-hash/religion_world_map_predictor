# Methods

The state is `P[c,r,g,a]`: persons in country *c* (200 countries), religion *r* (8 groups),
generation *g* (3) and five-year age group *a* (17, the last open at 80+). Generations are
0 = native (third generation or later), 1 = foreign-born, 2 = native-born child of a foreign-born
mother. The step is five years, from 2020 to 3030. The year 3026 is reported as
`0.8 × 3025 + 0.2 × 3030`.

The eight groups are Christianity, Islam, Hinduism, Buddhism, Judaism, Folk/Traditional, Other and
Unaffiliated.

## The step

Each five-year step applies these sub-steps in order, recording the change in persons and in
religious shares at each one, so that the component breakdown adds up exactly to the simulated
change (checked by `run.py checks`).

### 1. Survival

`P[a+1](t+5) = s_a * P[a](t)`, with `s_a = 5L(a+1) / 5L(a)` from a life table. The open group
is `P[80+](t+5) = (5L80 / 5L75) P[75-79](t) + (T85 / T80) P[80+](t)`, which reproduces a
stationary population exactly (`tests/test_model.py`). An earlier version applied `T80/T75`, the
ratio for the combined 75+ population, to the 75-79 group alone, understating its survival by
about a sixth; to 2100 the national rescaling to WPP hid most of that, after 2100 it did not.

The life table is a Siler-type hazard, `h(x) = 0.0004 + c·e^(−0.9x) + b·e^(0.09x)`, fitted to two
WPP series: *b* by bisection so that life expectancy at birth equals WPP's `e0`, and *c* in closed
form so that the probability of dying before age 5 equals WPP's `q5`. Tables are interpolated from
a precomputed grid over (`e0`, log `q5`).

Mortality does not differ by religion. No dataset the project has supports a difference, and
inventing one would change results without evidence.

### 2. Births

Births over the step to mothers of group (r, g):

> `B[c,r,g] = TFR_c · k_c · rel[c,r,g] · Σ_a f_c(a) · W[c,r,g,a]`

- `W` is woman-years: the female share by age (from WPP's population by age and sex, national
  otherwise) times the mean of the start and end populations.
- `f_c(a)` is a fertility age pattern — a discretised normal of standard deviation 6 years whose
  mean equals WPP's mean age at childbearing.
- `k_c` is set so the national total reproduces WPP's TFR exactly whatever the group pattern is.

The child takes the mother's religion. Generations map g0 → g0, g1 → g2, g2 → g0.

**`rel` — relative fertility of a religion inside a country.** This is the one place where
religion-specific demography enters, and the evidence for it is uneven, so the model takes the
most local published figure available and says which tier it used
(`data/projections/fertility_evidence.csv`):

| Tier | Source | Treatment |
|---|---|---|
| country | India NFHS-5, Israel CBS, Nigeria (IIASA reconstruction), United States Pew | used as published |
| region | Pew 2015 for Europe and sub-Saharan Africa | damped by `phi_region` ∈ [0.6, 1.0] |
| world | Pew 2015, all eight groups | damped by `phi` ∈ [0.3, 0.7] |

Every figure enters as a **ratio** to the reference fertility the same source reports for the same
population and period, never as a level, because a level divided by a reference from another
period would be wrong. The damping exists because a ratio measured across countries is not a
within-country ratio: globally, Muslim fertility is high largely because Muslims live in
high-fertility countries. History tests cannot identify `phi` (the error is flat in it), so it stays an
assumption with a stated range; the United States figures are a useful check, implying an
unaffiliated ratio of 0.86 where the world ratio of 0.68 reproduces 0.86 at `phi ≈ 0.5`.

Gaps converge towards zero with a half-life of 30-80 years, except in the
`persistent_fertility_gaps` scenario. A gap carried over from a world or regional figure is read
partly as a constant ratio and partly as a constant number of extra children (weight `w_add`); a
gap measured in the country itself keeps its own ratio, since no transfer is involved.

### Calibration to WPP (to 2100 only)

After births, each country is rescaled uniformly so that its **natural** growth over the step
equals WPP's: `(P_WPP(t+5) − N_WPP) / P_WPP(t)`. This acts like a common correction to fertility
and mortality. It leaves religious shares unchanged, never touches migrants, and so lets migration
scenarios move national totals away from WPP while migration stays exactly conserved.

### 3. Religious switching

A survey's lifetime matrix — the share of people raised in *r* who now identify with *s* — is not
an annual rate, and treating it as one is the commonest error in this literature. The model
parameterises the lifetime matrix by three probabilities per country:

- `d_r` raised in *r*, now unaffiliated
- `v_r` raised in *r*, now a different religion, with destinations in proportion to local prevalence
- `a` raised unaffiliated, now religious

It spreads switching over ages 15-49 with weights (0.20, 0.27, 0.22, 0.14, 0.09, 0.05, 0.03) and
solves for five-year matrices `T_a = I + w_a·(L* − I)` whose product over ages reproduces the
lifetime matrix `L` (Newton, then a fixed-point refinement). At realistic rates the
→ unaffiliated column is reproduced within 0.3 points and the diagonal within 1 point. Switching
is scaled for the foreign-born (0.3-0.6) and the second generation (0.4-0.8).

Rates come from a hierarchical model, estimated by empirical Bayes:

> `logit d[c,r] = μ_d[r] + δ + β_d·z_c(t) + τ_u·ξ_c + τ_e·ξ_{c,r}`
> `logit a[c]   = μ_a + β_a·z_c + τ_a·ξ′_c`
> `logit v[c,r] = μ_v[r] + τ_v·ξ″_c`

`z` is a development index (standardised WPP life expectancy and −log TFR, capped at the most
developed level observed). The country effects `ξ` are standard normal; `δ`, `β_d` and `τ_u` are
estimated by maximising the marginal likelihood of the evidence, with the country effects
integrated out.

Two kinds of evidence enter:

- **Net change.** A demographic-plus-migration hindcast of each historical decade, run *without*
  switching, leaves a residual. Its link to the rates is the first-order effect of switching on
  shares, which matches exact simulation within 0.05 points. The likelihood is Student-t (4
  degrees of freedom), robust to source breaks. Because the hindcast already contains births,
  deaths, ageing and migration, only the unexplained part is attributed to switching, so nothing
  is counted twice.
- **Surveys.** 67 verified lifetime cells from 48 survey rows (a country's adults raised in one
  religion, in one survey) in 33 countries. Each row is one **Dirichlet-multinomial**: the cells it
  reports, at the probabilities the model gives them, plus one complement cell for whatever it
  does not report. A cell "raised *r*, now *s*" has probability `v_r` times the model's share of
  converts going to *s* (local prevalence, as in the lifetime matrix), not `v_r` itself. The
  concentration `α = 100` lets a row carry the information of at most about a hundred respondents
  however large the survey, which allows for design effects and for the model's simplifications
  (one conversion effect per country, converts placed by prevalence). `α = 30` and `100` fit
  equally well and `300` worse; `α → ∞` is the multinomial.

  An earlier version scored each cell as a separate binomial against the total conversion
  probability. That counted the respondents of a row several times over and compared cells such
  as "raised unaffiliated, now Muslim (0.6%)" with the probability of affiliating with any
  religion (about 45%), which pulled the affiliation rate, and with it the disaffiliation rate,
  far down. Most of the gap the project used to report between the history-fitted and the
  survey level of switching was that error.

**Estimation.** The marginal likelihood of `H = (δ, β_d, τ_u)` is a product over countries of
ten-dimensional integrals over each country's effects, estimated by importance sampling. Draws
from the prior are inefficient wherever the evidence is sharp, and made the estimate depend on
the random seed. The fit therefore (i) evaluates a coarse grid with prior draws; (ii) replaces each
country's draws with a **defensive mixture** proposal, 25% prior and 75% a Gaussian fitted to that
country's importance-weighted draws, carrying the weight log prior − log proposal so that the
estimator stays unbiased for every `H`; (iii) repeats the grid and the adaptation; and (iv)
maximises continuously with Nelder-Mead on `(δ, β_d, log τ_u)`, inside the prior box
`δ ∈ [−1.5, 1.5]`, `β_d ∈ [−0.5, 2.4]`, `τ_u ∈ [0.4, 2.0]` (the range of the project's original
search grid). The fit the projection uses lies inside it. Fits to historical net change alone,
used in the history tests, prefer a larger country spread (`τ_u` near 3); with it full-strength
switching forecasts worse, because the extra spread reproduces country trends in the historical
residuals that do not persist. The bound is therefore kept, and folds that reach it are flagged
in `switching_fit_by_fold.csv`. Because the latent effects are
standard normal whatever `H` is, one set of draws serves every `H`, and the estimated likelihood
is a smooth function of it. Some Monte Carlo error remains, so the projection uses **three
replicate fits** with independent draws, run *r* using replicate *r* mod 3. That carries the error
into the projection's spread, and the replicates' standard deviation is reported in
`projection_report.json`. Country effects are drawn from each replicate's importance-weighted
posterior.

Pew's 2025 survey of 117 countries (adults 18-54) then fixes a second, "survey" level per religion
through a logit shift, and every run draws a weight between the two levels rather than the
project choosing one.

### 4-5. Migration

`F[o,d]` is persons moving over the step.

**How many.** To 2100 WPP's net migration fixes each country's net, and two-way circulation is
added on top: emigrants `E_c = 5·turnover·m_c·pop_c + max(−N_c, 0)`, immigrants
`I_c = 5·turnover·m_c·pop_c + max(N_c, 0)`.

- `m_c` is the country's observed mobility — UN immigrant plus emigrant stock per person,
  normalised to a population-weighted mean of 1. Without it, India and China would generate the
  world's largest flows purely through size.
- `turnover` (0-0.0004 per year) is calibrated on stocks: simulating 1990-2020 from the UN 1990
  foreign-born stocks matches the UN 2020 stocks best in this range. Gross-flow estimates imply
  about 0.0016, four times higher, because many migrants return and this model counts a returning
  emigrant as foreign-born. Gross churn is therefore understated while stocks are right.

**Where.** The kernel is `K = (1 − ω)·UN bilateral stock + ω·gravity`, with gravity
`distance^−1.5 × (1 + 2·land border) × (1 + 0.5·same continent)`. Flows are fitted to the margins
by Sinkhorn scaling with softness `ρ`: `a = (E / K b)^ρ`, `b = (I / Kᵀa)^ρ`. At `ρ = 1` both WPP
margins hold exactly, but WPP's projected margins conflict with the network — it keeps Pakistan
emitting 0.5-1 million people a year while Gulf net immigration falls to almost zero after 2030 —
and exact margins then force those emigrants into whichever countries have positive net
immigration. Each run draws `ρ` from 0.5 to 1; the 1990-2020 corridor test fits best near 0.75.

After 2100 there is no WPP: `E_c = rate_c(2095-2100) × multiplier × pop_c`, and destinations keep
their 2100 attraction, falling as they grow (congestion θ).

A cap on corridors (no origin may supply more than *c* times its share of a destination's migrant
stock) was tested on 1990-2020 for *c* from 1.5 to 4 and fits the observed corridors worse at every
margin softness; observed arrivals were more concentrated by origin than the uncapped model
simulates. It is therefore not applied. The projection's largest corridors relative to 2020
stocks are listed in `migration_corridor_concentration.csv`.

**Who.** Each corridor draws from origin cells in proportion to persons × age propensity ×
generation propensity × a corridor mix
`m[o,d,r] ∝ share_o[r]^(−λ) · (share_d[r] + 0.01)^κ`. λ is the minority effect (minorities
emigrate more), κ destination affinity (migrants move where their religion is already common).
Both are fitted to 19 published Pew figures on the religion of migrants: κ = 0.5, λ = 0.65,
error 2.2 points against 5.9 if migrants simply mirrored their origin.

No cell can lose more than half its people in five years; full cells are capped and the remainder
redistributed by water-filling. Immigrants arrive as first generation, split by age exactly as
the emigrants were, so worldwide migration changes no religion's numbers at all.

## After 2100

National TFR converges to a long-run level (1.6-2.1) with a half-life of 50-150 years. Country
deviations from that level have standard deviation 0.05-0.15 children and **decay with a half-life
of 100-400 years**. Earlier versions made them permanent, which over 900 years compounded a
0.1-child difference into the largest single source of spread at 2500-3026: the 5-95% band for
Islam at 3026 was 22 points with a permanent deviation against 5-6 points with any half-life in
this range. No country is assumed to hold a fertility advantage for centuries.

Life expectancy rises 0.02-0.06 years per year to a cap of 90-95; under-5 mortality falls with it.

## Scenarios

| Scenario | Switching | Migration | Fertility gaps |
|---|---|---|---|
| `stabilising` (reference) | development link to 2100, then fades (half-life 150 years, floor 0.3) | WPP to 2100, then 2100 rates | converge |
| `continued_secularization` | development link throughout, +0.6 logit/century to 2300, less return | as reference | converge |
| `high_retention` | more retention, more return, −0.3 logit/century | as reference | converge |
| `rising_migration` | as reference | ×2 by 2100, ×3 by 2200, ×4 by 3030 | converge |
| `low_migration` | as reference | ×0.5 by 2100, ×0.25 by 3030 | converge |
| `changing_migration` | as reference | ×1.2-1.5, networks fade into geography by 2100, pull from ageing | converge |
| `persistent_fertility_gaps` | as reference | as reference | persist |
| `combined_dispersal` | as continued secularization | as rising migration | persist |

Run *r* uses the same parameter draws in every scenario, so a difference between two scenarios is
the assumption alone.

## Evaluation

**Point forecasts.** Every World Religion Project decade from 1970-1980 to 2000-2010, and Pew
2010-2020 when the Pew workbook is prepared, is forecast from its first year with switching fitted
only on decades that end by then (net-change evidence only: the surveys postdate every origin).
National demography inside the window is WPP 2024's estimate, so the tests measure error
conditional on fertility, mortality and net migration. The score is the total-variation distance
between forecast and observed shares, population-weighted over countries.

**Inference.** A decade-level comparison has four or five observations, and an exact paired test
on it cannot fall below p = 0.125 (2/2⁴). The comparison with persistence is therefore also made
country by country: the population-weighted mean difference in error over every country-decade,
with a 95% interval from 4,000 bootstrap resamples of countries (all of a country's decades
together). Countries in the same decade share common shocks, which this interval does not
capture, so the decade-level sign-flip test is reported beside it as the conservative bound.

## Uncertainty and predictive intervals

Three kinds are separated:

- **parameter uncertainty**: the spread of runs inside one scenario, from the drawn parameters,
  the posterior switching draws and the replicate fits (`q05`, `q95`);
- **forecast error**: what the model, so fitted, has historically got wrong, added back by the
  error model below (`pi05`, `pi95`, to 2100);
- **scenario uncertainty**: the range across scenario means.

**The error record.** From each origin 1970, 1980, 1990 and 2000 the model is run forward 40 times
with everything as it would have been fitted then, and scored against the World Religion Project
at every later decade to 2010: 10 forecasts at horizons of 10 to 40 years, about 560 to 120
country-decades each.

**The error model.** For country *c*, religion *k* and horizon *h*,

> `e = (h/10)^β · (s(1−s) + 10⁻⁴)^b · u`

where *s* is the mean forecast share and *u* a standardised error. `b` is the slope of log|e| on
log(s(1−s)) at ten years (small shares move less); `β` is the growth of the mean absolute
standardised error with horizon. A predictive draw takes one Monte Carlo run and adds
`(h/10)^β g(s) u`, with *u* resampled in two stages: one historical decade for the whole world,
then for each country the whole eight-religion error vector of one of its 15 nearest neighbours
in that decade, nearest by total-variation distance between forecast compositions (a k-nearest-
neighbour bootstrap). The first stage keeps the common shock a decade's countries shared, which
is what matters for world totals. The second gives each country many errors rather than the few
its own history supplies, without ever transplanting an error measured on a religion that was a
tiny minority onto a country where it is the majority, which a standardised error can otherwise
turn into an absurd change. Shares are clipped at zero and renormalised. On the history record
(the 8-run trial record, uncentred errors), leave one origin out, this scored better than
resampling any country (interval score 14.2 against 16.3 at 90%, 34 against 42 for shares above
one half; world-total coverage 92.5% against 87.5%), resampling within share-size classes, or
aligning errors by rank.

The errors are used as recorded, not centred. Centring them (subtracting the pooled mean
standardised error) was tested: it calibrates slightly worse out of sample (interval score 14.4
against 13.9 at 90%), and because that mean is dominated by the many small shares, it pushes the
errors of large countries in the wrong direction and moves world medians away from the model's
central path (the 2100 median Christian share 28.9% against a central path of 25.8%, against
25.9% uncentred). The record does have a consistent direction, the unaffiliated share observed
below the forecast in every origin and horizon, by 0.6 to 4.5 pp of world population, mostly
post-communist and Chinese religious revival as the World Religion Project measured it, and it is
carried into the intervals: the predictive median of the world unaffiliated share in 2100 lies
below the central path. Centring each country's neighbourhood separately was also tested and
calibrates worse (86.7% at nominal 90%). `predictive_sensitivity_centring.csv` gives the centred
intervals for comparison.

**Validation.** Leave one origin out: `b`, `β` and the resampling pool are re-estimated without
the origin being tested, and its forecasts are scored for coverage and for the interval score of
Gneiting and Raftery (2007), `IS_α(l, u; x) = (u − l) + (2/α)(l − x)⁺ + (2/α)(x − u)⁺`, against the
parameter-only intervals.

The record's longest horizon is 40 years, so the growth law is extrapolated beyond 2060, and the
intervals are conditional on WPP's national demography; predictive intervals are reported to 2100
and not beyond.

## Estimated, assumed, observed

`data/projections/parameter_provenance.csv` tags every parameter. In summary:

- **Observed:** the 2020 start state; WPP demography to 2100; WRP history; UN migrant stocks; age
  structures; the 67 survey switching cells; published fertility and migrant-composition figures.
- **Estimated from data:** switching hyperparameters and country effects; the survey-level shifts;
  the religion of migrants (κ, λ); the circulation rate; the centre of the margin softness ρ; the
  forecast-error scale `b` and growth `β`.
- **Assumption:** the fertility damping factors `phi` and `phi_region`; the age patterns of
  switching and migration; generation intensities; the survey overdispersion `α`; everything after
  2100; the scenario settings; switching strength 1.
- **Unverified:** Pew's global median ages by religion.
