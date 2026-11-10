# What the evaluation supports, and what it does not

Written against the committed run in `results/`. Every number comes from a file there.

## 1. No version of the model beats assuming nothing changes

Scored on four World Religion Project decades, 1970-2010, with everything fitted only on earlier
decades, no mechanistic variant can be distinguished from persistence, and the best of them is
at most about 2% better. Country by country, over 558 country-decades, the
population-weighted difference in total-variation error from persistence is
−0.02 pp for births and deaths alone (95% interval −0.10 to +0.06) and
+0.48 pp with full-strength switching (−0.19 to +1.15). A naive trend, the last decade's change
repeated, is clearly worse (+1.71 pp, +1.03 to +2.25). The decade-level sign-flip test
agrees, though with four decades it cannot fall below p = 0.125.

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

## 2. The model's own bands are not forecast intervals; the predictive intervals are

The Monte Carlo bands (`q05`, `q95`) contain the observed share 19-20% of the time at
nominal 90%, at every horizon. They describe parameter uncertainty only. The predictive intervals
(`pi05`, `pi95`) add the forecast errors the model actually made, and in leave-one-origin-out tests
they cover 89-92% at nominal 90% for horizons of 10 to 40 years, with interval scores about
half as large.

What that does and does not establish:

- **Calibration is shown to 40 years.** The error record's longest horizon is 2010 − 1970. The
  error growth law `(h/10)^β` is extrapolated from there to 80 years (2100). Beyond 2100 no
  predictive interval is given.
- **The record is the World Religion Project's.** Its errors include its own measurement noise and
  category changes between rounds, which is appropriate if the future will be measured as noisily,
  and conservative if Pew's later rounds are more consistent.
- **The intervals carry the record's direction.** In 1970-2010 the unaffiliated share was observed
  below the forecast in every decade, mostly in post-communist and East Asian countries, and the
  intervals inherit that: the predictive median of the world unaffiliated share in 2100 lies below
  the central path, because China's compositional neighbours in the record moved that way. Whether
  that era's revival, as one source measured it, says anything about the twenty-first century is
  not something the record can settle; centring the errors removes it but calibrates slightly
  worse and distorts large countries (`predictive_sensitivity_centring.csv`).
- **The record's model is the history-fitted one.** Surveys of religious switching postdate every
  origin, so the error record uses switching fitted to net change alone, while the projection also
  uses the surveys. The intervals assume the projection errs as much as the history-fitted model did.
- **Conditional on WPP.** National fertility, mortality and net migration come from the WPP 2024
  medium variant and are not uncertain in the model. Uncertainty in national demography, the main
  driver of world totals through population weighting, is therefore missing from every interval.
- **World totals rest on few decades.** Common shocks are resampled from four decades (three when
  one is held out), so the world-level intervals are coarse; their coverage was 90% at
  nominal 90%.

## 3. The level of religious switching is the most consequential and least certain input

Surveys and historical net change both inform switching. An earlier version of this project
reported that they disagree strongly (11.7 against 17.1 Christians leaving per 100 raised); most of
that disagreement was an error in the survey likelihood, corrected in this revision. The two levels
now stand at 13.0 against 17.1 for Christians, and every run draws a weight between them.

The history tests do not favour switching: full-strength switching, fitted to net change, is no
better than persistence out of sample. Fitted to net change alone, the model prefers a country
spread larger than its prior range, and with it forecasts worse, because the extra spread
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
the switching strength, the age patterns of switching and migration, the generation intensities
and `α`. The Pew 2010 median ages by religion used for the within-country age tilt are marked
unverified in `config/assumptions.json` and must be checked against the report before citation:
the tilt's strength `psi` is the most influential parameter for the Muslim world share in 2050
(standardised rank coefficient +0.71).

## 9. Known artefacts

- Five French overseas departments have no Natural Earth geometry of their own and borrow a
  neighbour's coordinates for distance calculations.
- The World Religion Project's country coverage grows over time (117 to 164 countries scored per
  test decade), and Indonesia is missing in 1980 and 1985, so the earliest windows omit the largest
  Muslim-majority country.
