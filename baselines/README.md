# Baselines

Two independent implementations of the same question as the primary package, kept as methodological
comparisons. Neither is a forecast to cite. Both use only the Python standard library.

| | `manual_predictor/` | `mixed_predictor/` |
|---|---|---|
| Forecasts | the world composition, 7 groups | the world composition, 8 groups |
| Data | 7 snapshots from non-primary sources | WRP, balanced panel of 131 countries, 1970-2010 |
| Method | linear trend on shares, negatives clipped to zero | damped linear trend on log-shares |
| Validation | none | nested forward-chaining against persistence and four alternatives |
| Tests | none | 17 property checks, 5 methodology checks |
| Run | `python manual_predictor/main.py` | `python mixed_predictor/main.py` |

## What they contribute

They answer a question the primary package cannot answer about itself: **how much is achieved
without any demographic mechanism at all?** The answer, under a leakage-free evaluation, is that no
trend model is distinguishable from assuming nothing changes, which is also what the primary
package's own backtests find. Two very different approaches reaching the same conclusion is the
strongest evidence in this repository about how predictable religious composition is at decadal
horizons.

They also record a methodological lesson. The mixed baseline's first evaluation leaked: it tuned
its one parameter with knowledge of each fold's target years, and reported a 9% advantage that
vanished once corrected. The correction, the leaking original and a test that tells them apart are
all kept (`python mixed_predictor/main.py methodology`).

## Do not compare their errors with the primary package's

Both report errors in percentage points, and the numbers are not on the same scale. These
baselines forecast one world composition, scored after country-level errors cancel; the primary
package forecasts 200 countries and scores them before. The only legitimate comparison is each
model's error relative to its own persistence baseline. `../docs/COMPARABILITY.md` explains why and
gives that comparison.

## Origin

All three implementations were written in October 2026, as coursework comparing ways of building
the same application: by hand, by prompting an AI assistant, and collaboratively from one specification. The
prompted version grew into the primary package. The two kept here are the other two. The state of
the repository when that comparison was submitted is tagged `hw4-submission`.
