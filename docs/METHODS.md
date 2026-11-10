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

Gaps converge towards zero with a half-life of 30-80 years (`gap · 2^(−t/H)`), except in the
`persistent_fertility_gaps` scenario. An earlier version applied `e^(−t/H)`, so that the stated
half-life was in fact an e-folding time and the gaps closed about 1.4 times faster than stated. A gap carried over from a world or regional figure is read
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
  shares, which matches exact simulation within 0.05 points. The engine ages people before it
  switches them, so a cohort aged *a* at the start of a decade meets the matrices of age groups
  *a*+1 and *a*+2; an earlier version used *a* and *a*+1, which understated the effect by 10-20%
  in young populations and biased the fitted rates upwards there. The likelihood is Student-t (4
  degrees of freedom), robust to source breaks, with each decade down-weighted by 0.5 because
  decades of one source are not independent. Because the hindcast already contains births,
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
ten-dimensional integrals over each country's effects, estimated by importance sampling with 512
draws per country. Because the effects are standard normal whatever `H` is, one set of draws
serves every `H` and the estimate is a smooth function of it.

- *Proposal.* Draws from the prior are useless where the evidence is sharp: ten survey rows put
  the United States' effects within ±0.02 of their mode. Each country's draws therefore come from
  a three-part mixture: 20% the prior; 40% a multivariate t (5 degrees of freedom) centred on the
  country's posterior mode, with the inverse curvature there, inflated 1.5 times, as scale
  (**Laplace importance sampling**; the mode by damped Newton steps on finite-difference
  derivatives, all countries at once); and 40% a t matched to the importance-weighted moments of a
  pilot sample, shrunk towards the Laplace scale when the pilot's weights are few, which covers
  posteriors that are curved or skewed (two effects trading off along a ridge, as in Singapore).
  A country still left with fewer than 50 effective draws gets a second pass, with the moment
  component refitted to its weighted draws at twice the spread. Every weight carries log prior −
  log proposal, so the estimator is unbiased for every `H`.
  Across countries the effective sample size is about 300 of 512 at the median and at least 35.
  An earlier proposal, a Gaussian fitted to the weighted draws with a fixed ridge, was too wide
  for sharp posteriors and degenerated where its own weights did (an effective sample size of 1
  to 4 for South Korea and the United States). Its estimate of the log marginal likelihood moved
  by up to 24 units between adaptation rounds; the current one varies by about 0.5 between seeds.
- *Search.* A coarse grid with prior draws; adaptation at its best point; the grid again; then
  Nelder-Mead from the three best grid points, in unbounded coordinates (a scaled logit of
  `(δ, β_d, log τ_u)` on the prior box `δ ∈ [−1.5, 1.5]`, `β_d ∈ [−0.5, 2.4]`, `τ_u ∈ [0.4, 2.0]`,
  the range of the project's original search grid, on which the hyperprior is flat). Finally the
  proposal is re-centred on the current optimum and the search restarted from it until the optimum
  moves by less than 0.02, because a country's posterior moves with `H` and a proposal fitted at a
  grid point can miss a sharp posterior at the optimum. An earlier version clipped the search at
  the bounds, which made the objective flat beyond them; one replicate stalled at `τ_u = 2.0`,
  1.5 log-likelihood units below its own optimum.
- *Uncertainty in H.* The curvature of the estimated log marginal likelihood at the optimum gives
  the Laplace approximation of the hyperparameters' posterior under the flat hyperprior, truncated
  to the box. The curvature is the quadratic term of a least-squares quadratic fitted to 27 points
  about one standard error from the optimum: the estimate carries Monte Carlo error, and a narrow
  finite-difference stencil made the standard errors vary four-fold between replications of the
  same design. Every Monte Carlo run draws its own `H` from it, draws each country's effects from
  their posterior at that `H`, and recalibrates the survey-level shifts there, so the projection
  carries the estimation uncertainty of the hyperparameters instead of conditioning on their
  estimate (Kass and Steffey 1989). The standard errors are in `projection_report.json`.
- *Replicates.* Some Monte Carlo error remains, so the projection uses **three replicate fits**
  with independent draws, run *r* using replicate *r* mod 3; their spread is small beside the
  standard errors (reported in `projection_report.json`).
- *Checking the estimator.* `run.py recovery` simulates evidence from known hyperparameters with
  exactly the real design (the same countries, decades, exposure bases, survey rows and sample
  sizes), refits, and reports bias, root mean squared error and the coverage of the 90% Laplace
  intervals (`estimator_recovery.csv`).

Fits to historical net change alone, used in the history tests, prefer a larger country spread
(`τ_u` near 3); with it full-strength switching forecasts worse, because the extra spread
reproduces country trends in the historical residuals that do not persist. The bound is therefore
kept, and folds that reach it are flagged in `switching_fit_by_fold.csv`.

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
- `turnover` (0-0.0003 per year) is calibrated on stocks: simulating 1990-2020 from the UN 1990
  foreign-born stocks, the world total of the UN 2020 stocks is matched with no extra circulation
  and the country errors are smallest near 0.0002, and the range spans the two. Gross-flow estimates imply
  about 0.0016, several times higher, because many migrants return and this model counts a returning
  emigrant as foreign-born. Gross churn is therefore understated while stocks are right.

**Where.** The kernel is `K = (1 − ω)·UN bilateral stock + ω·gravity`, with gravity
`distance^−1.5 × (1 + 2·land border) × (1 + 0.5·same continent)`. Flows are fitted to the margins
by Sinkhorn scaling with softness `ρ`: `a = (E / K b)^ρ`, `b = (I / Kᵀa)^ρ`. At `ρ = 1` both WPP
margins hold exactly, but WPP's projected margins conflict with the network — it keeps Pakistan
emitting 0.5-1 million people a year while Gulf net immigration falls to almost zero after 2030 —
and exact margins then force those emigrants into whichever countries have positive net
immigration. Each run draws `ρ` from 0.5 to 1; the 1990-2020 corridor test fits best near 0.75.
The power updates also shrink the total: at `ρ = 0.75` an earlier version moved about a fifth fewer
people than requested, everywhere, not only where the margins conflict. The world total of flows
is therefore restored to the requested total, so `ρ` moves people between corridors and countries
without changing how many migrate; how far each run's net migration departs from WPP's is
reported (`migration_net_gap_to_wpp_mean` in `projection_report.json`).

After 2100 there is no WPP: `E_c = rate_c(2095-2100) × multiplier × pop_c`, and destinations keep
their 2100 attraction, falling as they grow (congestion θ).

A cap on corridors (no origin may supply more than *c* times its share of a destination's migrant
stock) was tested on 1990-2020 for *c* of 1.5, 2, 3 and 4 and fits the observed corridors worse at
every margin softness; observed arrivals were more concentrated by origin than the uncapped model
simulates. It is therefore not applied. The projection's largest corridors relative to 2020
stocks are listed in `migration_corridor_concentration.csv`.

**Who.** Each corridor draws from origin cells in proportion to persons × age propensity ×
generation propensity × a corridor mix `m[o,d,r] ∝ σ_o[r] · (share_d[r] + 0.01)^κ`. κ is
destination affinity (migrants move where their religion is already common), and `σ` the
minority effect: a religion's emigration propensity per person, proportional to `share_o[r]^(−λ)`,
normalised to a population mean of 1 in each origin and **bounded at `c` times that mean**. Without
the bound the propensity grows without limit as a minority shrinks: an earlier version had
Christians make up 14.5% of Pakistan-born migrants, against 1.3% of Pakistan, and drained them
from 1.3% to 0.4% of Pakistan by 2050, which no census shows. The one origin-country figure
available, Christians 16% of India-born migrants against 2% of India (Pew 2024), is reproduced at
11% with `c = 3` and 17% with `c = 6`, against 20% unbounded; each run draws `c` from 3 to 6.
κ and λ are fitted, at `c = 4.5`, to the 19 published Pew figures on the religion of migrants:
κ = 0.4, λ = 0.55, error 3.0 points against 5.9 if migrants simply mirrored their origin (2.2
unbounded, at the price of the implausible origin compositions above).
Pew's migrant file by country of origin, which needs an account, would identify `c` directly.

No cell can lose more than half its people in five years. Within a religion, cells that reach
the limit are capped and the rest of that religion's emigrants are spread over its cells with
room (water-filling); if all of a religion's cells in an origin are full, its corridors shrink
and the shortfall is reported (`migration_shortfall_persons_mean`), not moved to other
religions. Immigrants arrive as first generation, split by age exactly as
the emigrants were, so worldwide migration changes no religion's numbers at all.

## After 2100

National TFR converges to a long-run level (1.6-2.1) with a half-life of 50-150 years. Country
deviations from that level have standard deviation 0.05-0.15 children and **decay with a half-life
of 100-400 years**. Earlier versions made them permanent, which over 900 years compounded a
0.1-child difference into the largest single source of spread at 2500-3026: the 5-95% band for
Islam at 3026 was 22 points with a permanent deviation against 5-6 points with any half-life in
this range. No country is assumed to hold a fertility advantage for centuries.

Life expectancy rises 0.02-0.06 years per year to a cap of 90-95, and a country already above the
cap in 2100 keeps its level (an earlier version cut it to the cap in 2105, by up to three years in
Japan and Hong Kong); under-5 mortality falls with it. The convergence of the national TFR uses
the same half-life form as the fertility gaps.

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
The baselines are persistence (no change), a naive trend (the previous decade's observed change
repeated) and a hybrid (births, deaths and migration plus the previous decade's unexplained
change). Switching at strength 0 is the demography-and-migration forecast itself and is not
listed separately.
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
  the switching hyperparameters (Laplace draws), the posterior country effects and the replicate
  fits (`q05`, `q95`);
- **forecast error**: what the model, so fitted, has historically got wrong, added back by the
  error model below (`pi05`, `pi95`, to 2100);
- **scenario uncertainty**: the range across scenario means.

**The error record.** From each origin 1970, 1980, 1990 and 2000 the model is run forward 40 times
with everything as it would have been fitted then, and scored against the World Religion Project
at every later decade to 2010: 10 forecasts at horizons of 10 to 40 years, about 560 to 120
country-decades each. The history runs have the projection's structure: the development index
follows each period's WPP life expectancy and fertility, and the fertility gaps start converging
at the origin. (An earlier version froze both at the origin, so the error record described a
different model from the one its errors were added to.)

**The error model.** For country *c*, religion *k* and horizon *h*,

> `e = (h/10)^β · (s(1−s) + 10⁻⁴)^b · u`

where *s* is the mean forecast share and *u* a standardised error. `b` is the slope of log|e| on
log(s(1−s)) at ten years (small shares move less), over cells observed above zero: a quarter of
the record's cells are groups recorded at exactly zero, whose error equals the forecast by
construction and would pull `b` upwards. `β` is the growth of the mean absolute standardised error
with horizon. A predictive draw takes one Monte Carlo run and adds `(h/10)^β g(s) u`, with *s*
the mean of the runs as when the errors were measured, with *u* resampled in two stages: one historical decade for the whole world,
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

Adding the recorded errors to every run, rather than to the mean path, counts the record's own
parameter spread twice, since the errors were measured from the mean. In the record that spread is
5-10% of the predictive width; the validation scores both versions.

**Validation.** For each forecast in the record, `b`, `β` and the resampling pool are re-estimated
from the entries that share **no calendar years** with it, and the forecast is scored for
coverage and for the interval score of Gneiting and Raftery (2007),
`IS_α(l, u; x) = (u − l) + (2/α)(l − x)⁺ + (2/α)(x − u)⁺`, against the parameter-only intervals.
Excluding the overlapping entries matters: an earlier leave-one-origin-out design kept, for a
1970→1990 forecast, the 1980-1990 error block, which is the very shock being scored, and was a few
points optimistic for countries and more for world totals. A *real-time* variant uses only
entries that ended by the forecast's origin. Coverage is reported over all cells, over cells
observed above zero (a group recorded at zero is inside any interval reaching zero, which the
clipping makes common), and by forecast share. With four decades, no 40-year forecast has a
non-overlapping entry left, so calibration is checked to 30 years; where a refit has no horizon
beyond ten years, `β` falls back to 0.5 (random-walk growth).

The growth law is extrapolated beyond the validated horizons, and the intervals are conditional on
WPP's national demography; predictive intervals are reported to 2100 and not beyond.

## Estimated, assumed, observed

`data/projections/parameter_provenance.csv` tags every parameter. In summary:

- **Observed:** the 2020 start state; WPP demography to 2100; WRP history; UN migrant stocks; age
  structures; the 67 survey switching cells; published fertility and migrant-composition figures.
- **Estimated from data:** switching hyperparameters and country effects; the survey-level shifts;
  the religion of migrants (κ, λ); the circulation rate; the centre of the margin softness ρ; the
  forecast-error scale `b` and growth `β`.
- **Assumption:** the fertility damping factors `phi` and `phi_region`; the bound `c` on the
  minority effect; the age patterns of switching and migration; generation intensities; the survey
  overdispersion `α`; everything after 2100; the scenario settings; switching strength 1.
- **Unverified:** Pew's global median ages by religion.
