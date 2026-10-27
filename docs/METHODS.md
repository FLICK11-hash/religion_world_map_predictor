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

`P[a+1](t+5) = s_a * P[a](t)`, with `s_a = 5L(a+1) / 5L(a)` from a life table, and the open group
surviving at `T85/T80`.

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
high-fertility countries. Step 5E established that history cannot identify `phi`, so it stays an
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

`z` is a development index (standardised WPP life expectancy and −log TFR, capped at the most
developed level observed). `δ`, `β_d` and `τ_u` maximise the marginal likelihood over a grid;
country effects are posterior draws by importance weighting.

Two kinds of evidence enter:

- **Net change.** A demographic-plus-migration hindcast of each historical decade, run *without*
  switching, leaves a residual. Its link to the rates is the first-order effect of switching on
  shares, which matches exact simulation within 0.05 points. The likelihood is Student-t, robust
  to source breaks. Because the hindcast already contains births, deaths, ageing and migration,
  only the unexplained part is attributed to switching, so nothing is counted twice.
- **Surveys.** 67 verified lifetime cells in 33 countries enter a binomial likelihood.

Pew's 2025 survey of 117 countries (adults 18-54) then fixes a second, "survey" level per religion
through a logit shift. The two levels disagree — for Christians 11.7 against 17.1 left per 100
raised — so every run draws a weight between them rather than the project choosing one.

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

**Who.** Each corridor draws from origin cells in proportion to persons × age propensity ×
generation propensity × a corridor mix
`m[o,d,r] ∝ share_o[r]^(−λ) · (share_d[r] + 0.01)^κ`. λ is the minority effect (minorities
emigrate more), κ destination affinity (migrants move where their religion is already common).
Both are fitted to 19 published Pew figures on the religion of migrants: κ = 0.5, λ = 0.65,
error 2.2 points against 5.9 if migrants simply mirrored their origin.

No cell can lose more than half its people in five years; full cells are capped and the remainder
redistributed by water-filling. Immigrants arrive as first generation, split by age exactly as
the emigrants were, so worldwide migration changes no religion's numbers at all.

### 6. Residual

A ridge regression on start-of-decade conditions predicts what the mechanisms miss. Its weight is
chosen out of sample by the backtest, and that weight is 0 — it never improved out-of-sample
error, so the projection runs without any machine-learned correction.

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

## Uncertainty

Three kinds are separated:

- **parameter uncertainty** — the spread of runs inside one scenario, from the drawn parameters,
  the posterior switching draws and the country noise;
- **scenario uncertainty** — the range across scenario means;
- **everything else** — measurement error in the source data and country-level change the model
  has no mechanism for.

Only the first two are simulated. The backtest shows the third dominates at country level: see
`docs/LIMITATIONS.md`.

## Estimated, assumed, observed

`data/projections/parameter_provenance.csv` tags every parameter. In summary:

- **Observed:** the 2020 start state; WPP demography to 2100; WRP history; UN migrant stocks; age
  structures; the 67 survey switching cells; published fertility and migrant-composition figures.
- **Estimated from data:** switching hyperparameters and country effects; the survey-level shifts;
  the religion of migrants (κ, λ); the circulation rate; the centre of the margin softness ρ; the
  residual weight (0).
- **Assumption:** the fertility damping factors `phi` and `phi_region`; the age patterns of
  switching and migration; generation intensities; everything after 2100; the scenario settings;
  switching strength 1.
- **Unverified:** Pew's global median ages by religion.
