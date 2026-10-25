# What the validation supports, and what it does not

Written against the committed run in `results/`. Every number here comes from a file in that
folder or in `data/validation/`.

## 1. The intervals are not forecast intervals

This is the most important finding and it is a negative one.

The model reports 5-95% bands from its Monte Carlo over drawn parameters. Running that same Monte
Carlo on historical decades and asking how often the observed share actually fell inside the band
gives:

| Nominal | Covered (1980-90) | Covered (1990-2000) | Covered (2000-10) |
|---|---|---|---|
| 50% | 8.7% | 5.4% | 8.2% |
| 80% | 16.2% | 10.6% | 14.4% |
| 90% | 19.4% | 13.4% | 17.1% |

A 90% interval that contains the truth 13-19% of the time is not a 90% interval. The median
interval is 0.04-0.10 percentage points wide, while the median absolute error is 1.7 points for
Christianity and 0.6 for the unaffiliated. To cover the error actually made, the intervals would
have to be **2.7 to 19 times wider**, depending on the group.

Widening each interval by the per-religion data-noise scale the switching fit estimates lifts
coverage to 67-77%. So most of the shortfall is not the model being wrong about its parameters —
it is variation in the historical measurements, and country-level change the model has no
mechanism for.

**What follows.** Read the published bands as *the spread of model outputs under parameter
uncertainty*, which is what they are, and not as a probability that the truth lies inside. For an
honest near-term country-level error bar, use the out-of-sample numbers in
`data/validation/interval_calibration_windows.csv`: at a ten-year horizon the 90th percentile of
absolute error is 7.3 points for Christianity, 5.4 for the unaffiliated, 5.5 for Folk/Traditional,
3.7 for Islam and under 1 point for the smaller groups.

## 2. The model beats "nothing changes" by very little

On the WRP decades, population-weighted total-variation error, in percentage points:

| Model | 1990-2010 | all 1970-2010 |
|---|---|---|
| Persistence (no change) | 4.623 | 4.406 |
| Births and deaths only | 4.579 | 4.378 |
| + migration | 4.580 | 4.381 |
| + switching at full strength | 4.487 | 4.797 |
| Extrapolate the last decade | 6.829 | 5.854 |

The best mechanistic model improves on persistence by 0.14 points on an error of 4.6 — about 3%.
Switching helps on the recent decades and hurts on the early ones, where the fit had only two or
three decades to learn from and chose the largest country spread the grid allows. The projection
uses full-strength switching anyway, because surveys observe switching directly and the history
tests cannot settle it; that is a judgment and is recorded as one in
`data/validation/validation_report.json` (`used_by_forecast`).

Extrapolating recent change is far worse than any mechanistic model. That is the clearest positive
result of the backtests.

## 3. The underlying measurements move more than the projections do

Pew's 2015 report and Pew's 2025 report disagree about the world Christian share **in 2020** by
2.3 points (31.1% against 28.8%). Scored country by country, Pew's own ten-year-ahead projection
of 2020 differs from Pew's later measurement of 2020 by 10.7 points population-weighted — and
freezing 2010 unchanged scores 11.0, almost the same. **China contributes 69% of that difference**
and Vietnam 6%; it is a reclassification between folk religion and the unaffiliated, not a
forecasting failure.

Two consequences. First, no projection of this quantity can be more accurate than the measurements
it is scored against. Second, any country-level statement about China here inherits the
disagreement, and the Folk/Other split for Pew data is in any case a WRP-based proxy.

## 4. Where the fertility evidence runs out

Published fertility by religious group now covers, by 2020 population: 24% from country figures,
21% from regional figures, 55% from one global ratio per religion damped by an assumed factor.

The global tier is the weakest link. A global ratio mostly measures where each group lives, not
how many children its members have relative to their neighbours, and history cannot identify the
damping factor (Step 5E found the error flat in it). The country figures that do exist changed
real results — Israel's Jewish fertility is above Muslim fertility, which the global ratios had
backwards — which is reason to expect the remaining 55% to be carrying errors of the same kind.

The clearest gap is sub-Saharan Africa: the DHS surveys do cross-tabulate fertility by religion,
but only inside the full country reports, which could not be reached from the build environment.

## 5. What is assumed rather than estimated

Everything after 2100. The long-run fertility level, the speed of convergence, the life-expectancy
ceiling, the post-2100 migration rule and the fade of switching are all stated assumptions, and
`data/experiments/sensitivity_coefficients.csv` shows which of them the long-run results actually
turn on. The 2500 and 3026 columns exist to show what a set of assumptions implies, not what will
happen, and are labelled that way in every table and figure.

Within the projection horizon the main assumptions are the two fertility damping factors, the
switching strength, the age patterns of switching and migration, and the generation intensities.

## 6. Mechanisms the model does not have

- **Religious intermarriage.** Children take their mother's religion. In countries with high
  intermarriage this understates mixing.
- **Mortality differences between religions.** Not modelled; no dataset here supports a figure.
- **Sub-national variation.** Countries are homogeneous units. For large, religiously regionalised
  countries (India, Nigeria, Indonesia) this is a strong simplification.
- **Conflict, persecution, state policy and sudden displacement.** Refugees are inside the UN
  stocks, but there is no shock process, so the model cannot produce a Syria-shaped event.
- **Religiosity as distinct from affiliation.** The model tracks identification only.

## 7. Known artefacts

- Some migration corridors are probably too large. Pakistan supplies 32% of the United Kingdom's
  simulated arrivals in 2020-2050 against 8% of its 2020 foreign-born, because WPP's projected
  margins keep South Asian emigration high while Gulf net immigration falls to almost zero after
  2030. Softening the margin fit reduced this from 46% but did not remove it.
- Gross migration churn is understated by about a factor of four, because the circulation rate was
  calibrated on foreign-born stocks and the model counts a returning emigrant as foreign-born.
  Stocks are right; flows are not.
- Five French overseas departments have no Natural Earth geometry of their own and borrow a
  neighbour's coordinates for distance calculations.
