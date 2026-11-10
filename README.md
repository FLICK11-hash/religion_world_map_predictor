# Projecting the religious composition of countries

**A probabilistic cohort-component model and its out-of-sample evaluation**

| | |
|---|---|
| Field | Statistics: applied statistics and statistical demography |
| Topic | Probabilistic population projection and forecast evaluation, applied to religious composition |
| arXiv category | `stat.AP` (Statistics: Applications) |
| MSC 2020 | 62P25 (applications of statistics to the social sciences), 91D20 (mathematical demography), 62M20 (prediction) |
| JEL | C53 (forecasting and simulation methods), J11 (demographic trends and forecasts), Z12 (religion) |
| Keywords | cohort-component projection, religious switching, international migration, empirical Bayes, forecast evaluation, predictive intervals, interval score, shift-share decomposition |

A demographic simulation of how the religious composition of every country may change from 2020,
through births, deaths, ageing, religious switching and international migration. Populations are
held as persons by country (200), religion (8), migrant generation (3) and five-year age group (17)
and moved forward in five-year steps under eight scenarios. Every mechanism's contribution to every
change in share is recorded, so the components add up exactly to the simulated change. The model
is evaluated on the decades 1970-2010 with everything fitted only on earlier data, and its
predictive intervals are built from the errors it actually made there.

## Research questions

1. Does a mechanistic projection forecast historical decades better than assuming no change?
2. How large is its forecast error, how does that error grow with horizon, and can it be turned
   into predictive intervals that are calibrated out of sample?
3. Conditional on stated assumptions, which mechanisms account for projected change to 2100, and
   how much of it is change within countries rather than in where the world's population lives?

## Main findings

All numbers are from the committed run in `results/`; `docs/RESULTS.md` has the tables.

**1. Nothing beats assuming no change at decadal horizons.** Over 558 country-decades, births and
deaths alone differ from persistence by −0.03 pp of total-variation error (95% interval −0.10 to
+0.06), so they are at most about 2% better. Switching fitted to historical net change is no better
(+0.72 pp, −0.19 to +1.70), and repeating the last decade's change is clearly worse (+1.86 pp,
+1.21 to +2.41).

**2. The model's own uncertainty bands are not forecast intervals; calibrated ones nearly are.**
The Monte Carlo bands contain the observed share about a quarter of the time at nominal 90%.
Adding the model's past errors, resampled by decade from compositionally similar countries and
scaled by horizon, gives predictive intervals that cover 86-88% of observed shares at nominal 90%
for horizons of 10 to 30 years, validated so that the error model never shares calendar years with
the forecast it is scored on, with interval scores less than half as large. They are therefore a
few points too narrow, and coarser for world totals (85% of 72 held-out world shares). Error grows
as (horizon/10)^0.27, more slowly than a random walk.

**3. To 2100 the intervals are wide, but they still separate the largest groups.** In the
reference scenario the world Muslim share rises from 25.6% in 2020 to 39.1% in 2100 (90% predictive
interval 36.7-42.4%) and the Christian share falls from 28.8% to 25.7% (22.6-28.8%), so the two
intervals no longer overlap. The unaffiliated share falls from 24.2% to 19.5% (13.9-21.8%) and the
Hindu share from 14.9% to 12.0% (9.1-14.1%). In 26 countries the largest religion is more likely
than not to change by 2100, almost all to no religion (France 89%, United Kingdom 85%, Germany 78%,
United States 42%).

**4. Most of Islam's projected growth is about where people live.** Of the Muslim share's projected
rise of 13.5 pp by 2100, 10.3 pp comes from population weighting, the faster growth of
Muslim-majority countries, and 3.3 pp from change within countries. The unaffiliated share rises
within countries (+7.3 pp) but falls in the world (−4.6 pp), because the countries where it is
concentrated grow more slowly (−12.5 pp). These are properties of the projection under its
assumptions.

**5. Within countries, switching drives the change.** Switching off one mechanism at a time on
identical draws, switching accounts for −8.0 pp of the world Christian share in 2100 and +9.3 pp of
the unaffiliated share, and for the change of largest religion in about 42 countries.
Within-country fertility differences add 2.4 pp to the Muslim share. Migration moves no world share
by more than about a third of a point, and makes countries slightly more religiously mixed.

**6. The switching estimator is checked, not assumed.** Switching rates come from an empirical
Bayes model fitted to six decades of net change and 48 survey rows. Its hyperparameters are
estimated to within standard errors of 0.1-0.2 on the logit scale, and that uncertainty is carried
into every run. In a simulation study under the real design, the 90% intervals cover the true values
in 85-95% of replications. The level fitted to history and the level Pew's 2025 surveys report are
12.8 and 17.1 Christians leaving per 100 raised; every run draws a weight between them.

**What it is not.** It is not a prediction of the religious future. The intervals are conditional
on the UN's national demography (WPP 2024), which is not uncertain in the model. 2200, 2500 and 3026
are exploratory simulations of stated long-run assumptions, labelled that way everywhere and
without predictive intervals.

## Repository

| | |
|---|---|
| `religion_forecast/` | the model: engine, switching, migration, estimation, projection, evaluation, figures |
| `manuscript/` | the working draft of the paper, with a map from each number to its source file |
| `results/` | one complete run, committed, with its figures, report, commit stamp and check output |
| `docs/` | methods, data, results, limitations, reproducibility |
| `previous_grad_assignment/` | the two simpler programs from the course exercise the project began as |
| `PROJECT_OVERVIEW.md` | a short overview for collaborators: aims, what the code does, findings, open problems |

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate     # Windows: .\.venv\Scripts\activate
pip install -r requirements-lock.txt              # the exact versions everything was verified under
pip install -e .                                  # optional: adds the `religion-forecast` command

python scripts/verify_data.py                     # is data/ the data the committed results used?
python run.py test                                # 28 tests
python run.py all --quick                         # whole pipeline, fewer runs; results/ is left alone
python run.py all                                 # the full run, about 35 minutes on 4 cores; rewrites results/
```

To look at the committed results without running anything, open `results/figures/index.html` and
`results/comparison_report.md`.

| Stage | What it does | Writes |
|---|---|---|
| `fetch` | downloads the optional datasets, once | `data/raw/extra/` |
| `test` | unit and integration tests | – |
| `backtest` | history tests, country-level inference, the forecast-error record and its calibration, migration checks | `data/validation/` |
| `project` | the scenario × Monte Carlo projection with predictive intervals to 2100 | `data/projections/` |
| `recovery` | simulation study: does the switching estimator recover known hyperparameters under the real design | `data/validation/` |
| `experiments` | mechanism ablations, global sensitivity, migrant sorting | `data/experiments/` |
| `checks` | integrity checks; exit code 0 means every check passed | – |
| `figures` | maps and charts as SVG, `--png` for matplotlib versions | `outputs/figures/` |
| `report` | the run report, and `results/` with `--export` | `outputs/`, `results/` |

## Data

`data/` is git-ignored. `config/data_manifest.json` records every input with its source, the
SHA-256 of the exact file the committed results used and, for text files, a hash of the content
that is independent of platform. `python scripts/verify_data.py` checks a local `data/` against it.

Three files are required and `python scripts/prepare_raw_data.py` downloads them (install
`pip install -e '.[prepare]'` first): the World Religion Project national file, UN World Population
Prospects 2024 indicators, and Natural Earth boundaries. `python run.py fetch` adds the optional
datasets: UN bilateral migrant stocks, WPP population by age and sex, UNHCR refugee statistics and
Pew's 2015 projection.

**The Pew 2010-2020 workbook needs a free account, and the committed run did not have it.** Without
it the model starts from `inputs/pew2020_start_state.csv`, the same Pew 2020 composition but no 2010,
so the Pew 2010-2020 decade is neither fitted nor tested. With the workbook in `data/raw/`, run
`python scripts/prepare_pew_panel.py` and then `python run.py all`. `docs/DATA.md` describes every
dataset and its limitations.

## Reproducibility

- **Pinned environment.** `requirements-lock.txt`: Python 3.13.16, numpy 2.5.3, pandas 3.0.5.
- **Seeds.** Every stage derives its draws from `random_seed` in `config/assumptions.json`; run *r*
  uses the same draws in every scenario, so a difference between scenarios is the assumption.
- **Parallel runs.** Monte Carlo runs and replicate fits use every core (`--workers N` or
  `RELIGION_FORECAST_WORKERS` to change it); each run has its own random streams, so results do not
  depend on the number of processes, which a test checks.
- **Provenance per run.** `results/run_stamp.json` records the commit, whether the code was clean,
  and whether the integrity checks passed; `projection_report.json` records which inputs were used.
- **Tests and lint.** 28 tests in `tests/test_model.py` and `ruff` (settings in `pyproject.toml`),
  run on every push by `.github/workflows/tests.yml`, plus the integrity checks of `run.py checks`.

`docs/REPRODUCIBILITY.md` has the checklist and what remains open (a container, an archived
snapshot of the inputs).

## Layout

```
religion_forecast/      the package
  engine.py               the cohort-component step (numpy only, reads no files)
  switching.py            lifetime matrices, the hierarchical model and its estimation
  migration.py            origin-destination flows that conserve people exactly
  model.py                run parameters, scenarios, the initial state, simulate, hindcast
  calibration.py          the evidence switching and the religion of migrants are fitted to
  errors.py               the forecast-error record, error model and predictive draws
  recovery.py             simulation study of the switching estimator
  projection.py tables.py the Monte Carlo projection and its output tables
  backtest.py             history tests, inference, calibration of the intervals
  experiments.py          ablations, global sensitivity, migrant sorting
  report.py checks.py     the run report and integrity checks
  figures/                maps and charts
run.py                  entry point; the same commands install as `religion-forecast`
config/                 assumptions.json (every non-data number) and data_manifest.json
inputs/                 published figures transcribed with citations, one evidence grade per row
scripts/                prepare_raw_data.py, prepare_pew_panel.py, verify_data.py
tests/                  unit and integration tests
results/                one complete run, committed
manuscript/             the paper draft
docs/                   methods, data, results, limitations, reproducibility
previous_grad_assignment/  the course-exercise programs, kept as a record
data/  outputs/         generated, git-ignored
```

## History

The project began in October 2026 as a graduate course exercise in which the same forecasting
question was implemented three ways: by hand, by prompting an AI coding assistant, and jointly
with one. The AI-generated version grew into this model and has since been developed as a research
project; the other two are kept in `previous_grad_assignment/`. Earlier generations of the model, a
machine-learning pipeline and a first cohort model, were removed from the working tree in this
revision and remain in the git history at the tags `archive/pre-merge-main` and
`archive/pre-merge-research`.

**Use of AI tools.** Most of the code and documentation was written with an AI coding assistant
(Claude, by Anthropic), under the author's direction. Every reported number is regenerated by the
code from documented inputs, and the corrections recorded in `docs/` came from auditing that work
rather than accepting it.

## How to cite

`CITATION.cff` holds the citation metadata (GitHub shows it as "Cite this repository"). There is no
archived release or DOI yet; a tagged release deposited on Zenodo would provide both.

## Licence

The repository has no licence file yet, so until one is added the code is under default copyright.
Each dataset keeps its own terms, recorded per file in `config/data_manifest.json`. The Pew
workbooks are not redistributed.

## Documentation

- `PROJECT_OVERVIEW.md`: what the project is and where help is needed, for collaborators
- `docs/METHODS.md`: the model, its estimation and the error model, equation by equation
- `docs/RESULTS.md`: findings of the committed run
- `docs/LIMITATIONS.md`: what the evaluation does and does not support
- `docs/DATA.md`: every dataset, with coverage, licence and limitations
- `docs/REPRODUCIBILITY.md`: the checklist and exact commands
- `results/comparison_report.md`: the report generated by the run itself
- `manuscript/manuscript.md`: the paper draft
