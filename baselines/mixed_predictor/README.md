# Mixed predictor

The human–AI collaborative implementation of the religion forecasting project (HW 4-1). It is the
third of three: `manual_predictor/` was written by hand, `religion_forecast_step1/` (on the
`audit/static-review` branch) was vibe-coded, and this one was built from both.

```
python main.py                 the forecast, with the evidence for it
python main.py validate        full backtest tables
python main.py selftest        17 checks on the properties the model guarantees
python main.py rebuild-data    regenerate world_shares_wrp.csv from the raw WRP file
```

Standard library only. No numpy, no pandas, no install step. Reads one committed CSV; writes
`results/`.

| | lines of Python | dependencies | data | validated? |
|---|---|---|---|---|
| `manual_predictor` | 158 | none | 7 snapshots, 3 from an AI overview | no |
| `mixed_predictor` | 710 | none | 9 observations, published dataset | yes, 5-fold CV |
| vibe-coded model | 6,149 | numpy, pandas | WRP + UN WPP + UN stocks + Pew | yes, extensively |

## What it does

Forecasts the world's religious composition across eight groups. The model is one idea:

> Fit a straight-line trend to the **log** of each group's share, anchored on the last observation,
> and let that trend **decay** with a half-life chosen by backtesting.

Working in log-share space and converting back with a softmax means shares are strictly between 0
and 1 and sum to exactly 1 *by construction* — there is no clipping and no renormalisation hack.
The decay stops the trend running away over long horizons. One parameter, the half-life `H`, spans
the whole space between the two things it has to beat: `H = 0` reproduces "nothing changes"
exactly, `H = ∞` is plain extrapolation.

## Architectural decisions

**1. Replace the data.** The manual predictor's header says its 1900–1990 rows came from "google
AI overview simply because I couldn't find reliable and easy to interpret data anywhere else."
Those rows are internally inconsistent — Islam goes 20.0% (1920) → 13.4% (1950) → 20.0% (1970),
which did not happen, and the 1920 row is identical to 1990 in five of seven fields. The lecture's
feature-quality slide asks for *direct measurements*, not "outputs of another model." So this
version reads the World Religion Project (Maoz & Henderson 2013), the same source the vibe-coded
model uses.

**2. Use a balanced country panel.** This is the decision that most changed the answer. WRP follows
the Correlates of War state system, so countries *enter* the dataset as they gain independence: 65
states in 1945, 194 in 2010. Summing all countries in each year measures decolonisation as much as
religious change. Concretely, in the raw unbalanced series the Muslim share rises 13.0% → 22.5%
between 1950 and 2010; restricted to countries observed throughout, it rises 10.8% → 14.7%. **More
than half the apparent trend was countries arriving, not people converting.** The window starts in
1970 because that keeps 131 countries covering 89.3% of 2010 world population while still leaving
nine observations; `--start-year` exposes the trade-off (1950 gives 13 observations but only 76%
coverage). 1945 is excluded from every window — 65 states, no India at all, and a world total of
1.65bn against 2.27bn five years later. That is a coverage gap, not a measurement.

**3. Log-ratio instead of clip-and-renormalise.** The manual version adds a linear trend, clips
negatives to zero, then renormalises. The clip is irreversible: once a group hits zero it is gone
forever, which is why that model reports "Other" at exactly 0.00% at *every* horizon. Fitting in
log space removes the failure mode rather than patching it. `selftest` checks both halves of this
claim on real data: the manual algorithm does drive a group to exactly zero by 2100, and this model
does not at any horizon out to the year 12026.

**4. Anchor on the observation, not the regression intercept.** A detail that mattered more than it
looks. The first version used the fitted intercept as the starting level, which is a few tenths of
a point from where the world actually was, and that offset is paid at every horizon. It lost to the
persistence baseline in all five cross-validation folds. Anchoring on the last observation makes
`H = 0` reproduce persistence *exactly*, so the model family contains the winning baseline as a
special case. After the fix it beats persistence in 4 of 5 folds. The fix came out of validation,
not out of reasoning about the code.

**5. Nested cross-validation, not a single split.** With nine observations a single train/test
split gives one or three scored forecasts and an answer that moves if you shift the split. Instead
each cut year is held out in turn, the half-life is re-chosen on the remaining cuts, and the
held-out cut is scored. The baselines have no parameters to tune, so this removes the model's
unfair advantage rather than giving it one.

**6. Report the disagreement, not a single number.** The four strategies score within 0.3 pp of
each other in cross-validation but disagree by 12.8 pp about Islam in 2100. Publishing one of them
alone would claim a precision nine observations do not support, so the output shows all four.

## Results

Cross-validated error, leave-one-cut-out, 5 folds. Total variation distance in percentage points —
read it as "percent of the population placed in the wrong group".

| strategy | mean error (pp) | worst | beats persistence |
|---|---|---|---|
| persistence (nothing changes) | 3.299 | 4.850 | – |
| manual predictor's algorithm | 3.215 | 5.896 | 3/5 |
| adaptive per-group damping *(rejected)* | 3.095 | 5.104 | 4/5 |
| undamped log trend | 3.043 | 5.514 | 3/5 |
| **damped log trend (this model)** | **3.003** | 5.086 | **4/5** |

Two things worth being clear about. The margin over "assume nothing changes" is **9%** of the
error — real, measured, and small. And the manual predictor's *algorithm*, given the same good
data, scores 3.215: most of the gap between the hand-written version and this one is the data, not
the method.

Error grows with horizon roughly as expected, and the longest horizon any of this tests is 25
years:

| horizon | forecasts | mean error (pp) |
|---|---|---|
| 5 years | 5 | 1.54 |
| 10 years | 4 | 3.10 |
| 15 years | 3 | 5.02 |
| 20 years | 2 | 6.04 |
| 25 years | 1 | 6.68 |

### One idea that did not work

Extrapolating helps for five of the eight groups taken individually — on Islam it cuts the error
from 1.90 pp to 1.33 — but a single global half-life is chosen by a share-weighted average, which
lets the badly-behaved series set the dial for everyone. The obvious fix was to scale each group's
half-life by the R-squared of its own log trend, so clean trends keep extrapolating and wandering
ones get frozen: still one parameter, applied unevenly.

It scored **worse** (3.095 against 3.003) and is kept in the code, as the `adaptive` strategy, only
as a recorded negative result. The reason it fails is worth more than the idea was: R-squared
measures whether a line is *straight*, not whether it is *trustworthy*. Judaism scores 0.94 and
Folk/Traditional 0.87, and those are exactly the two series whose trends are artefacts — Judaism's
decline is mostly the world population tripling underneath it, and Folk/Traditional's is entangled
with China's reclassification. A straight line through a measurement artefact is still straight.
Picking which trends to trust needs knowledge about the data, which is the one thing this model
does not have.

## Accuracy is not evenly distributed

The lecture's point about sampling size — "minority = group with fewer examples… predictions for
small groups can be worse than for larger groups" — shows up directly, so the output reports error
per group rather than one average:

| group | mean share | error (pp) | error ÷ share |
|---|---|---|---|
| Unaffiliated | 12.90% | 2.69 | 0.209 |
| Islam | 17.18% | 1.59 | 0.092 |
| Hinduism | 15.47% | 1.57 | 0.101 |
| Buddhism | 7.71% | 0.47 | 0.061 |
| Folk/Traditional | 14.65% | 0.39 | 0.027 |
| Christianity | 30.78% | 0.23 | 0.007 |
| Other | 1.07% | 0.21 | 0.195 |
| Judaism | 0.24% | 0.05 | 0.195 |

Christianity, the largest group, is predicted **26× more accurately in relative terms** than
Judaism or "Other". A single headline error number hides that completely. The Unaffiliated share is the
worst case in both absolute and relative terms, for a specific reason: in WRP it rises until about
1980 and then falls, so a trend fitted at any cut before 1980 points the wrong way afterwards. That
single series is most of what stops the trend models beating persistence by more.

## The role of human guidance

An honest account, since that is what the assignment asks for.

**The human set the frame.** The goal, the eight-group structure, the horizons, the "only touch
this folder" boundary, the requirement that shares stay in [0, 100] and sum to 100, the demand for
validation and a history-vs-prediction comparison, and the instruction to keep it lightweight and
readable — all of these came from the human, before any code. The constraint that mattered most was
*"avoid copying unnecessary complexity"*: without it the obvious move is to port pieces of the
6,149-line model, and the result would have been neither simple nor clearly better.

**The human supplied the comparison.** Having two prior implementations to read is what made the
design decisions findable. Decision 3 (the clip) came from reading the manual code and noticing
that "Other" was 0.00 at every horizon. Decision 2 (the balanced panel) came from the vibe-coded
model's country mapping, which documents which historical polities it excludes and why. Neither
would have been obvious from a blank page.

**The AI found the problems.** The 1920/1990 duplicate rows, the Islam reversal in the AI-sourced
data, the decolonisation artefact in the raw WRP totals, and the anchoring flaw in decision 4 were
all turned up by writing code and looking at what came out — mostly by running the backtest and not
liking the answer. The anchoring flaw in particular was invisible by inspection and only showed up
as "loses 5/5 folds".

**Validation, not argument, settled the design.** Every claim in this file that takes the form "X
is better than Y" has a number behind it from `python main.py validate`, and the properties claimed
for the model are checked by `python main.py selftest` rather than asserted here. That split — the
human asking for validation, the AI building it and then having to accept what it said — is the
part of the collaboration that actually changed the output. The first version of this model was
worse than assuming nothing changes, and only the backtest knew.

## Limitations

- **Nine observations.** Everything here rests on nine five-year snapshots of one dataset. The
  cross-validation has five folds, the 25-year horizon is scored by exactly one forecast, and the
  half-life is barely identified — folds chose 20, 5, 5, 5, 5. Treat the error table as indicative.
- **89.3% of the world, not 100%.** The balanced panel excludes countries that gained independence
  after 1970, which is most of the remaining 10.7%. Those are disproportionately in sub-Saharan
  Africa, the fastest-growing and most Christian-and-Muslim region, so the panel probably
  understates both of those trends.
- **No mechanism.** This model knows nothing about births, deaths, migration or conversion. It
  extrapolates a shape. The vibe-coded model has all four and beats persistence by about 3% of the
  error — *less* than this model's 9%, on different data and a different metric, which should be
  read as "neither has much skill at this" rather than as this one winning.
- **It inherits WRP's known problems.** Most visibly China: the Unaffiliated reversal after 1980 is
  substantially a reclassification between "non-religious" and Chinese folk religion, not 300
  million people changing their minds. A trend model cannot tell those apart.
- **Judaism's trend is not what it looks like.** −17% per decade is mostly the denominator: the
  world's population tripled over the window. Extrapolating it to 0.19% by 2100 treats an
  arithmetic fact as a tendency, and small groups are also where WRP's measurement is thinnest.
- **The forecast is nearly flat, and that means "no information", not "no change".** With the
  selected half-life the composition stops moving after about 2030. Read with the strategy table
  below it: four approaches score within 0.30 pp of each other in cross-validation and yet
  disagree by up to 11.8 pp about Islam in 2100. The flat row is the middle of an interval wide
  enough to contain both "nothing changes" and "Islam reaches 30.8%", so it carries almost no
  information either way. It is not a claim that the world's religious composition will hold
  still; it is what a trend fitted to nine global aggregates, with no demographic mechanism
  underneath it, is able to support. The "beyond validated range" rows for 2500 and
  3026 exist only so this can be compared with the other two implementations, which report them.
- **Intended use.** This is coursework comparing three ways of building the same small application.
  It is not a research instrument and should not be cited as a projection of anyone's religious
  future.

## Datasheet

Following the lecture's "Datasheets for datasets" slide.

- **Who collected it.** Zeev Maoz (UC Davis) and Errol A. Henderson (Penn State), the World
  Religion Project, distributed with the Correlates of War project.
- **Citation.** Maoz, Z. and Henderson, E. A. (2013). "The World Religion Dataset, 1945–2010:
  Logic, Estimates, and Trends." *International Interactions* 39(3), 265–291.
- **What purpose.** Built for quantitative study of religion in international relations, not for
  forecasting. Using it to forecast is a secondary use it was not designed for.
- **When and where.** National-level estimates every five years, 1945–2010, for members of the
  Correlates of War state system.
- **How.** Compiled from national censuses, surveys and denominational records, with interpolation
  and estimation where those were missing. WRP ships per-row reliability codes
  (`sourcereliab`, `recreliab`, `reliabilevel`) which this model does **not** currently use — an
  obvious next improvement.
- **What is used here.** The count columns for each denomination, summed into eight groups using
  the same mapping as the vibe-coded model, aggregated across the balanced panel, converted to
  shares. The derivation is `data.py`; `world_shares_wrp.csv` carries its own provenance header and
  is regenerable with `python main.py rebuild-data`.
- **Descriptive statistics of what the model sees.** 9 years × 8 groups = 72 numbers, from 131
  countries, covering 6.10bn of the 6.83bn people WRP records for 2010. Shares range from 0.22%
  (Judaism, 2010) to 31.6% (Christianity, 1975). Every row sums to 1.
- **Known gaps.** 1945 excluded (65 states, India absent). Country coverage grows over time, hence
  the balanced panel. China's religious classification changes within the series.
