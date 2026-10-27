# Mixed predictor: a global-aggregate trend baseline

A deliberately simple forecaster of the **world's** religious composition, eight shares with no
countries and no demographic mechanism. It exists to answer one question for the primary package:
how much does a trend fitted to the historical shares achieve on its own? It is a baseline, not a
projection, and should not be cited as a forecast of anyone's religious future.

```
python main.py                 the forecast, with the evidence for it
python main.py validate        full backtest tables
python main.py selftest        17 checks on the properties the model guarantees
python main.py methodology     audit of the validation itself, with the corrected comparison
python main.py rebuild-data    regenerate world_shares_wrp.csv from the raw WRP file
```

Standard library only, no install step. It reads one committed CSV and writes `results/`.
Rebuilding that CSV from raw WRP (`rebuild-data`) reproduces the committed file byte for byte.

**Read `docs/COMPARABILITY.md` before comparing any number here with the primary package.** This
baseline forecasts one world composition, scored after country errors cancel out; the primary
package forecasts 200 countries and scores them before. Their errors are not on the same scale.

## The model

> Fit a straight line to the **log** of each group's share, anchored on the last observation, and
> let that line **decay** with a half-life chosen by backtesting.

Working in log-share space and converting back with a softmax keeps every share strictly between
0 and 1 and summing to exactly 1 by construction, with no clipping step. One parameter, the
half-life `H`, spans the whole space between the two things the model has to beat: `H = 0`
reproduces "nothing changes" exactly and `H = ∞` is plain extrapolation.

## Design decisions

**1. A published dataset.** The hand-written baseline's own comment says its 1900–1990 rows came
from "google AI overview simply because I couldn't find reliable and easy to interpret data
anywhere else". They are internally inconsistent: Islam goes 20.0% (1920) → 13.4% (1950) → 20.0%
(1970), which did not happen, and the 1920 row matches 1990 in five of seven fields. This baseline
reads the World Religion Project (Maoz & Henderson 2013) instead, as the primary package does.

**2. A balanced country panel, and what it costs.** WRP follows the Correlates of War state system,
so the set of countries changes over time: 65 states in 1945, 194 in 2010. Summing every country
each year mixes changes in religion with changes in which countries are counted. The panel keeps
only states present in every year from 1970 to 2010: 131 countries, 89.3% of 2010 population, nine
observations. `--start-year` exposes the trade-off.

The panel has a cost that was not understood when it was built. The 10.7% it drops is dominated by
**Indonesia (240 million) and Bangladesh (147 million)**, both Muslim-majority. Bangladesh is a
genuine post-1970 state. Indonesia is not: it is **missing from the WRP files for 1980 and 1985**,
a gap in the dataset, and requiring every year excludes it entirely. So the gap between the raw
series and the panel is partly real change in the state system (Bangladesh, the post-Soviet states,
German reunification) and partly this artefact. The panel understates the world Muslim share and
probably its growth. Neither the raw sums nor this panel is a clean world series; interpolating
Indonesia's two missing years would be the obvious next step.

**3. Log-ratio instead of clip-and-renormalise.** The hand-written baseline adds a linear trend,
clips negatives to zero and renormalises. The clip is irreversible: a group that reaches zero stays
there, which is why it reports "Other" at exactly 0.00% at every horizon. Fitting in log space
removes the failure mode. `selftest` checks both halves on real data: the hand-written algorithm does
drive a group to zero by 2100, and this model does not at any horizon out to 12026.

**4. Anchor on the observation, not the regression intercept.** The first version started each
trend from the fitted intercept, a few tenths of a point from where the world actually was, and paid
that offset at every horizon. Anchoring on the last observation makes `H = 0` reproduce persistence
exactly, so the model family contains its main baseline as a special case.

**5. Report the disagreement, not one number.** The strategies disagree by up to 12.8 pp about the
Muslim share in 2100, so the output shows all of them rather than publishing one.

## Validation, and a correction

The original evaluation was a "leave-one-cut-out" cross-validation: hold each cut out, choose the
half-life on the others, score the held-out one. It reported that the damped model beat
persistence by 9% of the error in 4 of 5 folds, and that result was presented here as real.

**It was leakage.** The "others" included cuts *after* the held-out one, and those later cuts are
scored on the held-out fold's own target years. Scoring a year requires knowing it, so each fold's
half-life was chosen with knowledge of its own answers: 14 of 15 test targets also entered the
tuning objective. `python main.py methodology` demonstrates this directly, by altering only data
after each cut. The original procedure's chosen half-life moves in 3 of 5 folds; a sound procedure
cannot let that happen.

The corrected evaluation is **nested forward-chaining**: at each cut the half-life is chosen by an
inner backtest on years up to that cut only. The same perturbation moves it in 0 of 4 folds. The
earliest cut cannot be tuned from its own past, so it is dropped rather than given a half-life
chosen with hindsight. Total variation in percentage points, read as "percent of the world placed
in the wrong group":

| Strategy | Corrected error (pp) | Beats persistence | Exact paired test, p | Original, leaking (pp) |
|---|---|---|---|---|
| persistence (nothing changes) | 2.977 | – | – | 3.299 |
| hand-written baseline's algorithm | 2.544 | 3 of 4 | 0.375 | 3.215 |
| undamped log trend | 2.425 | 3 of 4 | 0.250 | 3.043 |
| damped log trend | 2.962 | 2 of 4 | 1.000 | 3.003 |
| adaptive per-group damping | 2.953 | 2 of 4 | 1.000 | 3.095 |

Four things follow.

- **The damped model's advantage was the leak.** Chosen from the past alone, the half-life is zero
  in 3 of 4 folds, which is persistence, and the margin vanishes.
- **No strategy is distinguishable from persistence.** With four usable folds the smallest p-value
  an exact two-sided paired test can produce is 0.125, so none can be shown to beat persistence at
  the 5% level whatever the data say.
- **The ranking is unstable.** It reverses between the leaking and the corrected design, and again
  when forecasts are compared one horizon at a time. A ranking that flips with the evaluation is
  itself evidence that there is no real difference to find.
- **Nine global observations cannot separate any of these from assuming nothing changes.** That is
  the result. It matches what the primary package finds by an entirely different route.

The original procedure is kept unchanged, as `cross_validated_comparison`, so the correction can be
reproduced. The corrected one is `nested_forward_comparison`; the test is `sign_flip_test`. Results
are in `results/methodology_*.csv`.

### An idea that did not work

Extrapolation helps five of the eight groups taken individually, but a single half-life is chosen by
a share-weighted average, so the badly behaved series set it for everyone. Scaling each group's
half-life by the R² of its own trend was meant to fix that with no extra parameters. It scored worse
than plain damping under the original evaluation (3.095 against 3.003), and under the corrected one it
is indistinguishable from both damping and persistence (2.953, p = 1.0). It is kept as the `adaptive`
strategy, as a recorded negative result. R²
measures whether a line is straight, not whether it is trustworthy: Judaism scores 0.94 and
Folk/Traditional 0.87, and those are exactly the two series whose trends are artefacts. Judaism's
decline is mostly the world population tripling underneath it; Folk/Traditional is entangled with
China's reclassification. Choosing which trends to trust needs knowledge about the data that a trend
model does not have.

## Accuracy is not evenly distributed

Error per group, over all backtest forecasts. This table is descriptive: it uses the half-life chosen
on the full sample, so it is not an out-of-sample estimate.

| Group | Mean share | Error (pp) | Error ÷ share |
|---|---|---|---|
| Unaffiliated | 12.90% | 2.69 | 0.209 |
| Islam | 17.18% | 1.59 | 0.092 |
| Hinduism | 15.47% | 1.57 | 0.101 |
| Buddhism | 7.71% | 0.47 | 0.061 |
| Folk/Traditional | 14.65% | 0.39 | 0.027 |
| Christianity | 30.78% | 0.23 | 0.007 |
| Other | 1.07% | 0.21 | 0.195 |
| Judaism | 0.24% | 0.05 | 0.195 |

Relative to its size, Christianity is predicted about 26 times more accurately than Judaism or
Other; a single average hides that. Unaffiliated is the worst case in absolute and relative terms,
because in WRP it rises until about 1980 and then falls, so any trend fitted before 1980 points the
wrong way afterwards.

## The forecast

It barely moves after about 2030. That means **no information, not no change**. The selected
half-life is short because nine observations cannot settle it, and the strategies, indistinguishable
from one another in validation, disagree by up to 12.8 pp about the Muslim share in 2100. The flat row
is the middle of an interval wide enough to contain both "nothing changes" and "Islam reaches 30.8%".
This model has no births, deaths, migration or conversion; a flat answer is what a trend fitted to
nine aggregates can support, not a claim about the world. The rows for 2500 and 3026 are printed only
for comparison with the other implementations.

## Limitations

- **Nine observations, four usable folds.** No comparison here can reach conventional significance.
- **89.3% of the world**, and not a random 89.3%: the excluded population is dominated by Indonesia
  and Bangladesh, so the panel understates the Muslim share.
- **No mechanism.** It extrapolates a shape and cannot represent why shares change.
- **WRP's known problems are inherited**, most visibly China, where the Unaffiliated reversal after
  1980 is substantially a reclassification between "non-religious" and folk religion.
- **Judaism's −17% per decade is mostly the denominator**: the world population tripled. Extrapolating
  it treats arithmetic as a tendency.
- **WRP's per-row reliability codes** (`sourcereliab`, `recreliab`, `reliabilevel`) are not used.

## How it was built

This baseline is one of three implementations of the same question, written in October 2026 to
compare ways of building it: one by hand (`../manual_predictor/`), one by prompting an AI
assistant, which became the primary package, and this one, written collaboratively from a single
specification with both earlier versions as reference. That origin is why the repository holds
three, and the record is kept because it bears on how much to trust each.

The specification set the constraints: shares in [0, 100] summing to 100, validation against a
baseline, a history-versus-forecast comparison, no unnecessary dependencies, and *"avoid copying
unnecessary complexity"*, without which the obvious move was to port pieces of the larger model.
The earlier versions supplied the evidence for several decisions: the clip (decision 3) was found by
reading the hand-written code and noticing that Other was 0.00 at every horizon. The anchoring flaw
(decision 4) was found only by running the backtest; it was invisible by inspection.

The validation was where the build was least careful, and the correction above is the most
important thing in this file. The leaking cross-validation was written, described as rigorous and
reported, and the error was found only in a later audit. Writing a validation is not the same as
validating, and that applies to the method as much as to the model.

## Datasheet

- **Who collected it.** Zeev Maoz (UC Davis) and Errol A. Henderson (Penn State), the World
  Religion Project, distributed with the Correlates of War project.
- **Citation.** Maoz, Z. and Henderson, E. A. (2013). "The World Religion Dataset, 1945–2010:
  Logic, Estimates, and Trends." *International Interactions* 39(3), 265–291.
- **Purpose.** Built for the quantitative study of religion in international relations, not for
  forecasting; this is a secondary use it was not designed for.
- **Coverage.** National estimates every five years, 1945–2010, for members of the Correlates of War
  state system.
- **Method.** Compiled from censuses, surveys and denominational records, with interpolation and
  estimation where those were missing.
- **What is used here.** Count columns per denomination, summed into eight groups with the same
  mapping as the primary package, aggregated over the balanced panel and converted to shares. The
  derivation is `data.py`; `world_shares_wrp.csv` carries its own provenance header.
- **Descriptive statistics.** 9 years × 8 groups from 131 countries, covering 6.10 bn of the 6.83 bn
  people WRP records for 2010. Shares range from 0.22% (Judaism, 2010) to 31.6% (Christianity, 1975).
- **Known gaps.** 1945 is excluded everywhere: 65 states, India absent, a world total of 1.65 bn
  against 2.27 bn five years later. Indonesia is missing for 1980 and 1985. Country coverage changes
  over time. China's classification changes within the series.
