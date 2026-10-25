# Religious composition of countries: a cohort-component projection

A demographic simulation of how the religious composition of every country may change, from 2020
to 3030, through births, deaths, religious switching and international migration. Country
populations are held as persons by religion, generation and five-year age group and moved forward
in five-year steps. Every mechanism's contribution to every share change is recorded, so the
components add up exactly to the simulated change.

The model is validated by forward-chaining backtests on historical decades, against a persistence
baseline and against an independent published projection, and its uncertainty is checked by
measuring how often its intervals actually contain the truth.

**What it is not.** It is not a prediction of the religious future. The 2050 and 2100 horizons are
demographic projections conditional on stated assumptions; 2200, 2500 and 3026 are exploratory
scenario simulations and are labelled as such everywhere. The headline negative result of the
validation is that the model's own uncertainty bands are several times too narrow to be read as
forecast intervals — see `docs/LIMITATIONS.md`.

## Install and run

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
python run.py all                                  # the whole pipeline, about an hour
python run.py all --quick                          # fewer Monte Carlo runs, about ten minutes
```

On Windows, with the virtual environment the project already uses:

```powershell
cd religion_forecast_step1\religion_forecast_step1
.\.venv\Scripts\python.exe run.py all
```

Each stage can be run on its own, and `python run.py <stage> --help` lists its options:

| Stage | What it does | Writes |
|---|---|---|
| `fetch` | downloads the optional datasets (once, needs internet) | `data/raw/extra/` |
| `test` | unit and integration tests | — |
| `backtest` | history tests, interval calibration, migration checks | `data/validation/` |
| `project` | the scenario × Monte Carlo projection | `data/projections/` |
| `experiments` | mechanism ablations, global sensitivity, migrant sorting | `data/experiments/` |
| `checks` | integrity checks on the outputs (exit code 0 = all passed) | — |
| `figures` | maps and charts as SVG (`--png` also draws the matplotlib versions) | `outputs/figures/` |
| `report` | the comparison report, and `results/` for committing | `outputs/`, `results/` |

### Input data

Three files must be in `data/raw/` before anything else. `python prepare_raw_data.py` downloads
them and records a SHA-256 for each:

- `WRP_national.csv` — World Religion Project, national religious composition 1945-2010
- `WPP2024_Demographic_Indicators_Medium.csv.gz` — UN World Population Prospects 2024
- `ne_50m_admin_0_countries.zip` — Natural Earth admin-0 boundaries

One more is behind a free Pew account and cannot be downloaded automatically:
`data/raw/pew_2010_2020.xlsx`. With it, `python prepare_pew_panel.py` writes
`data/processed/pew_harmonized.csv`, which is the preferred 2020 start state and the only way to
include the Pew 2010-2020 decade in the backtests. Without it the model falls back to the 2020
start state exported in `results_step5/`, and says so in every report.

`python run.py fetch` then adds the optional datasets: UN bilateral migrant stocks, WPP population
by age and sex, UNHCR refugee statistics, Pew's 2015 projection. Each is used only if present, and
`data/projections/projection_report.json` records exactly which were found.

## Layout

```
run.py                      one entry point for every stage
config/assumptions.json     every non-data number, each tagged with how it was obtained
inputs/                     published figures transcribed with citations (tracked in git)
religion_forecast/          the package
  config.py                   paths and the assumptions file
  sources.py  datasets.py     readers and loaders
  engine.py                   the cohort-component step (numpy only, reads no files)
  switching.py  migration.py  the two social mechanisms
  model.py                    run parameters, scenarios, `simulate`, `hindcast`
  calibration.py              fitting switching and the religion of migrants to evidence
  projection.py  tables.py    the Monte Carlo run and its output tables
  backtest.py                 history tests and interval calibration
  experiments.py              ablations, global sensitivity, migrant sorting
  report.py  checks.py        the written report and the integrity checks
  figures/                    maps and charts
tests/                      unit and integration tests
results/                    small copies of one run, committed so a reader can check the numbers
legacy/                     earlier pipelines, superseded (see legacy/README.md)
docs/                       methods, data, limitations, reproducibility
data/  outputs/             everything a run generates (git-ignored)
```

## Documentation

- [`docs/METHODS.md`](../../docs/METHODS.md) — the model, equation by equation, and what is
  estimated as against assumed
- [`docs/DATA.md`](../../docs/DATA.md) — every dataset: coverage, dates, licence, limitations,
  and what still needs a manual download
- [`docs/LIMITATIONS.md`](../../docs/LIMITATIONS.md) — what the validation does and does not
  support
- [`docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md) — the checklist and the exact commands
- [`docs/RESULTS.md`](../../docs/RESULTS.md) — findings from the committed run
- `results/comparison_report.md` — the report generated by the run itself

## Reproducibility

Every stage takes its seed from `config/assumptions.json` (`random_seed`, default 2026) and run *r*
uses the same parameter draws in every scenario, so a difference between two scenarios is the
assumption and not sampling noise. Re-running `python run.py all` on the same inputs reproduces
`results/` exactly; `tests/test_model.py` includes a reproducibility test that asserts it for a
short run.
