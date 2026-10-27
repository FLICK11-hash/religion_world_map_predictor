# Naive linear-trend baseline

The simplest possible version of the question: seven snapshots of the world's religious
composition, an average annual change per group, and a straight-line extrapolation.

```
python main.py
```

Standard library only. It prints the average annual change per group and then the projected
composition for 2100, 2500 and 3026, as raw dictionaries.

## What it is for

It is the simplest reference forecast in the repository, the floor against which the trend baseline
and the cohort-component model are read. It is useful precisely because its failures are easy to
see. It was written by hand, which is why its folder is named `manual_predictor`.

## Its data

Recorded in the file's own header, and none of it is a primary demographic source:

- **2024** from `ar.inspiredpencil.com`, an image-aggregation site
- **2007** from `age-of-the-sage.org`, a general-interest reference site
- **1900 to 1990** from a search engine's AI-generated overview, "simply because I couldn't find
  reliable and easy to interpret data anywhere else"

The AI-generated rows are internally inconsistent. The Muslim share goes 20.0% in 1920, down to
13.4% in 1950 and back to 20.0% in 1970, which did not happen, and the 1920 row is identical to the
1990 row in five of its seven fields.

## Its method, and the failure built into it

Annual change in each share is averaged over the six intervals, added linearly, and any negative
share is set to zero before rescaling so the shares sum to one. Setting a share to zero is
irreversible: once a group reaches zero it can never recover, so the projection always ends with
whichever group grew fastest taking everything.

| Year | Christianity | Islam | Other | Judaism |
|---|---|---|---|---|
| 2100 | 26.5% | 32.2% | 0.00% | 0.165% |
| 2500 | 9.2% | 46.8% | 0.00% | 0.036% |
| 3026 | 0.7% | 54.0% | 0.00% | 0.000% |

"Other" is exactly zero at every horizon, and Judaism reaches exactly zero by 3026. These are
products of the clip, not of any process in the world.

## What it showed

Given the same good data, this method is not worse than the more elaborate trend models. In the
corrected, leakage-free evaluation in `../mixed_predictor/` its averaging algorithm scores 2.544 pp
against 2.977 pp for persistence, beating it in 3 of 4 folds; neither it nor anything else is
statistically distinguishable from persistence. Most of what was wrong with this baseline was its
data, not its arithmetic. See `../../docs/COMPARABILITY.md`.

## Structure

158 lines, all at module level, with no functions. That keeps it short, and it is also why it has
no tests: there is nothing for a test to call without rewriting it first.
