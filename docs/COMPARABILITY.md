# Comparing the model with its baselines

This repository contains two forecasting frameworks that both report their errors in percentage
points. Those numbers are **not comparable**, and a reader who sets them side by side will reach a
wrong conclusion. This page explains why, and states the one comparison that is legitimate.

## What each one measures

| | Primary package (`religion_forecast/`) | Trend baseline (`baselines/mixed_predictor/`) |
|---|---|---|
| Unit forecast | 200 countries × 8 religions | one world composition, 8 shares |
| Countries | all with WPP demography | balanced panel of 131, those present in every WRP year 1970-2010 |
| Coverage of 2010 population | full | 89.3% |
| Mechanism | births, deaths, ageing, switching, migration | none: a trend fitted to the shares |
| Error metric | population-weighted total variation **across countries** | total variation of the **single world** composition |
| Test design | four decadal windows, 1970-2010, forward-chaining | every (cut, later year) pair, 5-25 years ahead |
| What is tuned | switching strength, residual weight | trend half-life |
| Tuning procedure | earlier windows only | nested forward-chaining (corrected; see below) |

## Why the numbers cannot be ranked against each other

**Aggregation removes error.** The world composition is a population-weighted sum of country
compositions. If a model overstates the Muslim share in one country and understates it by the same
number of people in another, the world error is zero while the country-level error is not. The
trend baseline is scored after that cancellation; the primary package before it. Lower world-level
error is therefore expected even from a worse model, and says nothing about which forecasts better.

**They predict different populations.** The trend baseline keeps only states present in every WRP
year from 1970 to 2010, which drops 63 states holding 10.7% (733 million) of the 2010 population.
The two largest are **Indonesia (240 million) and Bangladesh (147 million)**, both Muslim-majority,
followed by reunified Germany and the post-Soviet states. Bangladesh is a genuine post-1970 state.
Indonesia is not: it is simply **missing from the WRP files for 1980 and 1985**, a gap in the
dataset, so any panel requiring every year excludes the world's largest Muslim-majority country.
The balanced panel therefore understates the world Muslim share, and its trend.

**They pool different horizons.** The primary package scores ten-year windows. The trend baseline
averages 5- to 25-year forecasts, where the longest horizons have the largest errors and the fewest
instances.

**The baselines themselves differ.** Even "nothing changes" scores differently under each design.
Over comparable periods persistence scores 3.49 pp at a ten-year horizon in the mixed design and
5.96 pp for 1990-2000 in the primary design. A gap that large between two forms of the *same*
null forecast is a measure of the design, not of any model.

## The comparison that is legitimate

Each model's error **relative to its own persistence baseline**, under its own design. That ratio
is dimensionless and asks the same question of both: does the model beat assuming nothing changes?

Both frameworks give the same answer, and it is the most robust finding in the repository:

| | Beats its persistence baseline | Exact paired test, two-sided |
|---|---|---|
| Primary package, best variant | 2 of 4 windows | p = 0.75 |
| Primary package, as used for the forecast (switching strength 1) | 2 of 4 windows | p = 0.875 |
| Trend baseline, damped trend (corrected evaluation) | 2 of 4 folds | p = 1.0 |
| Trend baseline, best variant (undamped trend) | 3 of 4 folds | p = 0.25 |

With four test windows the smallest p-value a two-sided paired test can produce is 0.125, so
neither framework can show significant skill over persistence at the 5% level regardless of the
data. Two quite different approaches converge on the same result: **at decadal horizons, the
historical record does not let any of these models be distinguished from assuming nothing
changes.** That is a statement about the evidence, not a failure of either approach, and it
is the right frame for reading every projection in this repository.

The p-values are computed by `sign_flip_test` in `baselines/mixed_predictor/validate.py`, applied
to the per-window errors in `results/validation_by_window.csv` and to the folds of
`python baselines/mixed_predictor/main.py methodology`.

## The primary package's windows are not like-for-like either

Its four decadal test windows score different sets of countries: 117 for 1970-1980, 137 for
1980-1990, 140 for 1990-2000 and 164 for 2000-2010, because a country is scored only where WRP
observes it at both ends. The WRP gap above means **Indonesia is absent from both the 1970-1980 and
the 1980-1990 windows**. An average over all four windows therefore mixes four different
populations, and the two earliest omit the largest Muslim-majority country. That is worth bearing
in mind when reading the 1980-1990 window, where full-strength switching does worst, though nothing
here shows the omission is what causes that error.

## A correction to the trend baseline's original result

The trend baseline originally reported beating persistence by 9% of the error in 4 of 5 folds. That
result came from a leaking cross-validation: when each fold was held out, its half-life was tuned on
later folds, which are scored on the held-out fold's own target years. 14 of 15 test targets entered
the tuning objective. Under leakage-free nested forward-chaining the advantage disappears (2.962 pp
against 2.977 pp). The original procedure is kept, unchanged, so the correction can be reproduced;
`python main.py methodology` demonstrates the leak by perturbing only post-cut data and showing that
the original procedure's chosen half-life moves while the corrected one's does not.

The primary package was audited the same way and does not have this flaw. Its training windows
must end before each test window starts, and its tuning uses only windows already scored.

## A comparison the primary package's documentation used to make

Earlier versions of `docs/RESULTS.md` said the mechanistic model "beats nothing changes by about
3% of the error". That figure is correct for the two 1990-2010 windows with switching at full
strength (4.487 pp against 4.623 pp). Over all four windows the same configuration is worse than
persistence (4.797 pp against 4.406 pp), largely because of the 1980-1990 window. The sentence has
been corrected to report both.
