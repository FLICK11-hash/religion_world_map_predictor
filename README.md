# Religious composition of countries: a cohort-component projection

A demographic simulation of how the religious composition of every country may change from 2020,
through births, deaths, ageing, religious switching and international migration. Populations are
held as persons by country (200), religion (8), migrant generation (3) and five-year age group (17),
and moved forward in five-year steps under eight scenarios. Every mechanism's contribution to every
change in share is recorded, so the components add up exactly to the simulated change.

The repository's contribution is less a forecast than an account of **what a forecast of this kind
can and cannot support**. Its historical validation shows that no version of the model can be
distinguished from assuming nothing changes, that its uncertainty bands are several times too
narrow, and that two vintages of the published figures it is scored against differ by more than two
independent models differ about the next thirty years.

**What it is not.** It is not a prediction of the religious future. The 2050 and 2100 horizons are
projections conditional on stated assumptions. 2200, 2500 and 3026 are exploratory simulations of
what those assumptions imply, and are labelled that way in every table and figure.

## Main findings

All figures are from the committed run in `results/` (the `stabilising` reference scenario, 40
Monte Carlo runs, seed 2026) unless stated. `docs/RESULTS.md` has the full tables.

**1. Most projected change in world shares comes from where people live, not from conversion.** An
exact shift-share decomposition of 2020-2100 splits each change in world share into change within
countries and change in which countries hold the population:

| Religion | Change in world share | Within countries | Population weighting | Interaction |
|---|---|---|---|---|
| Islam | +13.4 pp | +3.0 | +10.4 | +0.1 |
| Christianity | −2.2 pp | −7.9 | +6.4 | −0.8 |
| Unaffiliated | −5.8 pp | +6.3 | −12.5 | +0.5 |

The unaffiliated share rises inside countries and falls globally because the countries it is
concentrated in grow more slowly. These are properties of the projection, conditional on its
assumptions, not observations.

**2. Within the model, switching drives country-level change and migration barely moves world
shares.** Mechanism ablations on identical random draws, at 2100: switching accounts for −7.2 pp of
the Christian share, +8.1 pp of the unaffiliated share and 29 of the countries whose largest group
changes; fertility differences within countries account for +2.0 pp of the Muslim share. Migration
moves no world share by more than 0.22 pp: it relocates people, and changes world shares only
through what happens to them after they move.

**3. The model cannot be shown to beat assuming nothing changes.** Scored on four historical decades,
1970-2010, every configuration beats persistence in exactly 2 of 4 windows. An exact paired test gives
p ≥ 0.75, and with four windows no test could return p below 0.125. Extrapolating the last decade is
worse than persistence in all four windows.

**4. Its uncertainty is badly understated.** Nominal 90% intervals contain the observed share 13-19%
of the time across three historical windows. Adding measured data noise raises coverage to 67-77%,
which says most of the shortfall is measurement error the model does not represent.

**5. The data disagree about the present by more than the models disagree about the future.**
Against Pew's independent 2015 projection, this model's change in world share over 2020-2050 agrees
within 1.3 pp for every group, and in direction for six of eight (not Christianity: −0.9 here, +0.2
in Pew). Their starting points for 2020 differ by up to 8.6 pp (the unaffiliated), mostly because
Pew's 2015 baseline and its later data classify China differently. Scored country by country, Pew's 2015
projection of 2020 misses Pew's later measurement by 10.7 pp population-weighted, barely better
than freezing 2010 (10.9), and China is 69% of that.

**6. The most influential assumption is not demographic.** In a global sensitivity analysis over 23
parameters, the largest effect on the 2100 Christian share (standardised rank coefficient −0.88) is
`survey_weight`: whether switching follows the rate fitted to historical net change or the higher
rate Pew's surveys report. The model is most sensitive to a disagreement between two kinds of
evidence, which better switching measurement would settle.

## Three implementations

| | What it is | Role |
|---|---|---|
| `religion_forecast/` | the cohort-component package, 200 countries | **the project** |
| `baselines/mixed_predictor/` | a damped trend on the world's eight shares, no mechanism | baseline: what a trend alone achieves |
| `baselines/manual_predictor/` | a linear trend on seven snapshots | baseline: the floor |

The baselines forecast one world composition rather than 200 countries, so **their errors are not on
the same scale as the package's** and must not be ranked against it. `docs/COMPARABILITY.md` explains
why and gives the one legitimate comparison: each model against its own persistence baseline. By that
measure the two approaches agree that nothing is distinguishable from persistence at decadal horizons.

The mixed baseline's first evaluation leaked, tuning its parameter with knowledge of each fold's
target years, and reported a 9% advantage that vanished once corrected. The correction is kept beside
the original, with a test that tells them apart (`baselines/README.md`).

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate     # Windows: .\.venv\Scripts\activate
pip install -r requirements-lock.txt              # the exact versions everything was verified under
pip install -e .                                  # optional: adds the `religion-forecast` command

python scripts/verify_data.py                     # is data/ the data the committed results used?
python run.py test                                # 16 tests
python run.py all --quick                         # whole pipeline, fewer runs, about ten minutes
python run.py all                                 # the full run, about an hour
```

`python run.py <stage> --help` lists each stage's options. The stages, in order:

| Stage | What it does | Writes |
|---|---|---|
| `fetch` | downloads the optional datasets, once | `data/raw/extra/` |
| `test` | unit and integration tests | — |
| `backtest` | history tests, interval calibration, migration checks | `data/validation/` |
| `project` | the scenario × Monte Carlo projection | `data/projections/` |
| `experiments` | ablations, global sensitivity, migrant sorting | `data/experiments/` |
| `checks` | integrity checks; exit code 0 means every check passed | — |
| `figures` | maps and charts as SVG, `--png` for matplotlib versions | `outputs/figures/` |
| `report` | the generated report, and `results/` with `--export` | `outputs/`, `results/` |

## Data

`data/` is git-ignored. `config/data_manifest.json` records every input: its source URL, the
SHA-256 and size of the exact file the committed results used, the stage that needs it, and its
licence where that could be stated with confidence. `python scripts/verify_data.py` compares a local
`data/` against it.

Three files are required. `python scripts/prepare_raw_data.py` downloads them; it imports geopandas,
so install `pip install -e '.[prepare]'` first.

- `WRP_national.csv`, World Religion Project v1.1, national composition 1945-2010
- `WPP2024_Demographic_Indicators_Medium.csv.gz`, UN World Population Prospects 2024
- `ne_50m_admin_0_countries.zip`, Natural Earth 1:50m boundaries

`python run.py fetch` adds the optional datasets, each used only if present: UN bilateral migrant
stocks, WPP population by age and sex, UNHCR refugee statistics, World Bank covariates and Pew's 2015
projection.

**One input needs a manual download, and its absence shapes every committed result.** The preferred
2010 and 2020 starting composition is built by `scripts/prepare_pew_panel.py` from a Pew workbook that
requires a free account. Without it the package starts from `results_step5/headline_country_shares.csv`,
a committed export of the same Pew 2020 data from an earlier model. **Every result in `results/` used
that fallback, and the Pew 2010-2020 validation window could not run.** Supplying the workbook will
change the numbers slightly and add that window.

`docs/DATA.md` gives each dataset's coverage, dates and limitations. Two that bear on the validation:
the World Religion Project is missing Indonesia, the largest Muslim-majority country, for 1980 and
1985, so the two earliest test windows omit it; and its country coverage grows over time, so the four
windows score 117, 137, 140 and 164 countries respectively.

## Reproducibility

- **Pinned environment.** `requirements-lock.txt` is what was verified: Python 3.13.16, numpy 2.5.3,
  pandas 3.0.5. `pyproject.toml` declares the ranges and three optional extras: `maps`, `prepare`,
  `legacy`.
- **Seeds.** Every stage derives its draws from `random_seed` in `config/assumptions.json`, and run *r*
  uses the same draws in every scenario, so a difference between scenarios is the assumption, not noise.
- **Determinism, demonstrated.** Re-exporting `results/` from this layout reproduces every committed
  file exactly; only the generation timestamp differs.
- **Provenance per run.** `results/run_stamp.json` records the commit a run was made at, whether the
  working tree was clean, and whether the integrity checks passed. `projection_report.json` records
  which inputs were used, which fell back and which were missing.
- **Tests.** 16 package tests, the integrity checks, the four archived Step 5D/5E suites, 17 property
  checks and 5 methodology checks in the mixed baseline. All pass.

`docs/REPRODUCIBILITY.md` has the checklist, including what remains open: no container, and no
archived snapshot of the inputs, which matters because WPP and the migrant stocks are revised.

## Layout

```
religion_forecast/      the package: engine, switching, migration, model, calibration,
                        projection, backtest, experiments, tables, report, checks, figures, cli
run.py                  entry point; the same commands install as `religion-forecast`
tests/                  unit and integration tests
config/                 assumptions.json (every non-data number) and data_manifest.json
inputs/                 published figures transcribed with citations, one evidence grade per row
scripts/                prepare_raw_data.py, prepare_pew_panel.py, verify_data.py
results/                one complete run, committed, with its commit stamp and check output
results_step5/          the Step 5D export; holds the fallback start state
baselines/              manual_predictor/, mixed_predictor/
legacy/                 archived experiments: Steps 1-6 machine learning, Steps 5D-5E cohort model
docs/                   methods, data, limitations, reproducibility, results, comparability
data/  outputs/         generated, git-ignored
```

## History

The repository began in October 2026 as coursework comparing three ways of building the same
forecasting application: by hand, by prompting an AI assistant, and collaboratively from one
specification. The prompted version is the one that grew into this package; the other two are kept
in `baselines/`, and `baselines/README.md` records the comparison.

The package itself went through two generations. Steps 1 to 6 were a machine-learning pipeline that
trained LightGBM and a neural network to predict five-year changes in each religion's share. Steps
5D and 5E replaced it with the first cohort-component model and its first history tests, because a
learned model of share changes cannot represent the mechanisms behind them, and those mechanisms
are what the questions are about. The current package, Step 7, descends directly from 5D and 5E.
`legacy/README.md` records what each step tested.

The work was kept in two unrelated git histories, one holding the baselines and the first
generation, the other the cohort model. They were merged when the repository was restructured,
without rewriting either. `git log --follow` traces any file through both, and the state of each
before the merge is tagged: `hw4-submission` and `step7-research-snapshot`.

## Documentation

- `docs/METHODS.md`: the model, equation by equation, and what is estimated rather than assumed
- `docs/DATA.md`: every dataset, with coverage, dates, licence and limitations
- `docs/COMPARABILITY.md`: why the implementations' errors cannot be ranked, and what can be compared
- `docs/LIMITATIONS.md`: what the validation does and does not support
- `docs/RESULTS.md`: findings from the committed run
- `docs/REPRODUCIBILITY.md`: the checklist and exact commands
- `docs/AUDIT_STATIC.md`: the audit of the earlier pipeline that the current model answers
- `results/comparison_report.md`: the report generated by the run itself

## Licence

The repository has no licence file yet, so until one is added the code is under default copyright.
Each dataset keeps its own terms, recorded per file in `config/data_manifest.json`. The Pew
workbooks are not redistributed.
