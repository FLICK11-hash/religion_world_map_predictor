# What the evaluation supports, and what it does not

Written against the committed run in `results/`. Every number comes from a file there.

## 1. No version of the model beats assuming nothing changes

Scored on four World Religion Project decades, 1970-2010, with everything fitted only on earlier
decades, no mechanistic variant can be distinguished from persistence, and the best of them is
at most about 2% better. Country by country, over 558 country-decades, the
population-weighted difference in total-variation error from persistence is
−0.03 pp for births and deaths alone (95% interval −0.10 to +0.06) and
+0.72 pp with full-strength switching (−0.19 to +1.70). A naive trend, the last decade's change
repeated, is clearly worse (+1.86 pp, +1.21 to +2.41), and so is the demographic forecast plus the
last decade's unexplained change (+1.71 pp). The decade-level sign-flip test agrees, though with
four decades it cannot fall below p = 0.125.

Two cautions. The country bootstrap treats countries as independent within a decade, and they
share common shocks, so its intervals are too narrow and the conclusion "indistinguishable" holds
a fortiori; a bound such as "at most a few percent better" is less secure. And every history test
is conditional on national demography: the WPP 2024 *estimates* for each historical window are
used, not the projections available at the time, so real-time forecast error was larger.

**Information that postdates the history windows.** Besides WPP's estimates, three inputs of the
history runs were measured after the windows they are used in: the religion-of-migrants
parameters κ and λ, fitted to 2020 bilateral stocks and Pew's 2020 migrant composition; the
religion-specific fertility ratios, measured in the 2010s and applied from each origin; and the
migrant stocks that seed the migration network (1990 onwards, the UN stock nearest the origin).
None of them is fitted to the shares being forecast, and the switching evidence of each fold ends
before its window, but the history tests are retrospective, not real-time, in these respects too.

## 2. The model's own bands are not forecast intervals; the predictive intervals nearly are

The Monte Carlo bands (`q05`, `q95`) contain the observed share about a quarter of the time at
nominal 90% (23-25% of shares observed above zero, at every horizon). They describe parameter
uncertainty only. The predictive intervals (`pi05`, `pi95`) add the forecast errors the model
actually made. Validated so that the error model never shares calendar years with the forecast it
is scored on, they cover 86-88% of shares observed above zero at nominal 90% for horizons of 10 to
30 years (87% pooled; 86% in the stricter real-time variant), with interval scores less than half
as large as the parameter-only bands'.

What that does and does not establish:

- **The intervals are a few points too narrow.** An earlier validation, which left out only the
  origin being tested and so kept the decades a forecast was scored on in the error model's pool,
  reported 89-92%. The honest figure is lower. No correction is applied, because any correction
  estimated on four decades would have to be validated on the same four decades.
- **Calibration is shown to 30 years.** With four decades, every 40-year forecast overlaps every
  other entry of the record, so it cannot be validated out of sample. The error growth law
  `(h/10)^β` is extrapolated from there to 80 years (2100). Beyond 2100 no predictive interval is
  given.
- **World totals are coarser.** Common shocks are resampled from four decades (fewer when the
  scored decades are left out), and the world-level intervals covered 85% of 72 held-out world
  shares (75% at 30 years, and 75% of 48 in real time).
- **Zeros flatter small shares.** A quarter of the record's cells are groups recorded at exactly
  zero; they fall inside any interval reaching zero, which the clipping of shares at zero makes
  common. Coverage over all cells (87.6-90.1%) is therefore higher than over cells above zero,
  which is the figure quoted.
- **The record is the World Religion Project's.** Its errors include its own measurement noise and
  category changes between rounds, which is appropriate if the future will be measured as noisily,
  and conservative if Pew's later rounds are more consistent.
- **The intervals carry the record's direction.** In 1970-2010 the unaffiliated share was observed
  below the forecast in every decade, mostly in post-communist and East Asian countries, and the
  intervals inherit that: the predictive median of the world unaffiliated share in 2100 (17.8%) lies
  below the central path (19.5%), because China's compositional neighbours in the record moved that
  way. Whether that era's revival, as one source measured it, says anything about the twenty-first
  century is not something the record can settle; centring the errors removes it but calibrates no
  better and distorts large countries (`predictive_sensitivity_centring.csv`).
- **The record's model is the history-fitted one.** Surveys of religious switching postdate every
  origin, so the error record uses switching fitted to net change alone, while the projection also
  uses the surveys. The intervals assume the projection errs as much as the history-fitted model did.
- **Errors are added to every run.** The errors were measured from the mean of the history runs, so
  adding them to every projection run counts the history runs' own spread twice. That spread is
  5-10% of the predictive width, and adding the errors to the mean path only calibrates worse (85%).
  At long horizons the projection's own spread is larger than the history runs' was, and the
  intervals include it.
- **Conditional on WPP.** National fertility, mortality and net migration come from the WPP 2024
  medium variant and are not uncertain in the model. Uncertainty in national demography, the main
  driver of world totals through population weighting, is therefore missing from every interval.

## 3. The level of religious switching is the most consequential and least certain input

Surveys and historical net change both inform switching. An earlier version of this project
reported that they disagree strongly (11.7 against 17.1 Christians leaving per 100 raised); most of
that disagreement was an error in the survey likelihood, since corrected. The two levels now stand
at 12.8 against 17.1 for Christians, and every run draws a weight between them; that weight is the
most influential single assumption for the Christian and unaffiliated world shares (section 8 of
`RESULTS.md`).

The estimator itself has been checked by simulation under the real design: its 90% Laplace
intervals cover the true hyperparameters in 85-95% of 20 replications, and it estimates the
overall level δ about half a standard error too low (bias −0.08 ± 0.04), so the history-fitted level
is, if anything, slightly conservative. Twenty replications pin coverage down only to about ±8
points. In 4 of the 20, one country's importance sample had fewer than ten effective draws, which
adds Monte Carlo noise there without biasing the estimator.

The history tests do not favour switching: full-strength switching, fitted to net change, is no
better than persistence out of sample (+0.72 pp, not significant). Fitted to net change alone, the
model puts the country spread at the upper end of its prior range in every fold, and with it forecasts worse, because the extra spread
reproduces country trends in the historical residuals that do not continue. The projection uses
switching at full strength because surveys observe it directly; that is a judgement, and the
history tests cannot settle it.

The survey evidence itself is thin: 67 cells from 48 survey rows in 33 countries, a third of them
read from report text or secondary reporting rather than tables (`inputs/switching_lifetime_observed.csv`,
column `evidence_type`). The Dirichlet-multinomial concentration `α = 100` caps how much any one row
counts; it is an assumption, chosen because 30 and 100 fit equally well and 300 worse.

## 4. Measurements move more than projections

Pew's 2015 report and its 2025 data disagree about the world's composition in 2020 by more than
most of the change any projection makes over thirty years, largely because China's folk religion
and unaffiliated populations are classified differently (`benchmark_vs_pew2015.csv`,
`benchmark_pew2015_skill.csv`). No projection of this quantity can be more accurate than the
measurements it is scored against, and any statement about China inherits the disagreement. The
Folk/Other split of Pew data is a World Religion Project proxy.

## 5. Where the fertility evidence runs out

Religion-specific fertility is published for few countries. By 2020 population, most of the world
takes its within-country fertility differences from regional or global ratios, damped because a
ratio measured across countries mostly reflects where each group lives (`fertility_evidence.csv`).
History tests cannot identify the damping factors, which stay assumptions with stated ranges. The
clearest gap is sub-Saharan Africa: DHS surveys cross-tabulate fertility by religion, but only in
country reports that could not be reached from the build environment.

## 6. Migration

- The religion of migrants is calibrated to 19 published aggregate figures, not observed by
  corridor; Pew's country-level migrant file needs an account. Only one of the figures describes
  emigrants of one origin (India), so the minority effect is weakly identified: unbounded, it
  drained small minorities in high-emigration countries (Christians in Pakistan, 1.3% to 0.4% by
  2050, in an earlier version). It is now bounded at 3-6 times an origin's average propensity, an
  assumption with a stated range rather than an estimate. Country results for small minorities in
  emigration countries (Christians in Pakistan, Bangladesh and Turkey; Hindus in Bangladesh) depend
  on it, and origin-level migrant data are the evidence that would settle it.
- Some projected corridors are much larger than the corresponding 2020 stocks, notably from
  Pakistan into the United Kingdom (`migration_corridor_concentration.csv`). WPP 2024 keeps South
  Asian emigration high while Gulf net immigration falls to almost zero after 2030, and the model
  respects WPP's national margins. A cap on corridor shares was tested and fits the 1990-2020
  corridors worse at every setting, so it is not applied; country results for such destinations
  should be read with this in mind.
- Gross churn is understated, because circulation is calibrated on foreign-born stocks and a
  returning emigrant counts as foreign-born. Stocks are right; flows are not.

## 7. Mechanisms the model does not have

- **Religious intermarriage.** Children take their mother's religion.
- **Mortality differences between religions.** Not modelled; no dataset here supports a figure.
- **Sub-national variation.** Countries are homogeneous units, a strong simplification for India,
  Nigeria or Indonesia.
- **Conflict, persecution, state policy and sudden displacement.** Refugees are inside the UN
  stocks, but there is no shock process.
- **Religiosity as distinct from affiliation.** The model tracks identification only.

## 8. What is assumed rather than estimated

Everything after 2100: the long-run fertility level and its convergence, the life-expectancy
ceiling, post-2100 migration and the fade of switching. The 2200, 2500 and 3026 results show what
a stated set of assumptions implies; they are labelled exploratory everywhere and carry no
predictive interval. Within the horizon, the main assumptions are the fertility damping factors,
the switching strength, the bound on the minority effect in emigration, the age patterns of
switching and migration, the generation intensities and `α`. The Pew 2010 median ages by religion
used for the within-country age tilt are marked unverified in `config/assumptions.json` and must
be checked against the report before citation: the tilt's strength `psi` is the most influential
parameter for the Muslim world share in 2050 (standardised rank coefficient +0.69, against a
placebo noise floor of 0.15).

## 9. Known artefacts

- Five French overseas departments have no Natural Earth geometry of their own and borrow a
  neighbour's coordinates for distance calculations.
- The World Religion Project's country coverage grows over time (117 to 164 countries scored per
  test decade), and Indonesia is missing in 1980 and 1985, so the earliest windows omit the largest
  Muslim-majority country.
