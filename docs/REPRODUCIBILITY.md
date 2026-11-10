# Reproducibility

## Exact commands

From the repository root:

```bash
python -m venv .venv && . .venv/bin/activate          # Windows: .\.venv\Scripts\activate
pip install -r requirements-lock.txt   # the exact versions everything was verified under

pip install -e '.[prepare]'           # prepare_raw_data.py imports geopandas, even to download CSVs
python scripts/prepare_raw_data.py   # downloads WRP, WPP 2024 and Natural Earth
# download data/raw/pew_2010_2020.xlsx by hand (free Pew account), then:
python scripts/prepare_pew_panel.py  # writes data/processed/pew_harmonized.csv

python run.py fetch               # the optional datasets, once
python scripts/verify_data.py     # compare data/ against the committed checksums
python run.py all                 # test, backtest, project, recovery, experiments, checks, figures, report
```

`python run.py all` takes about two hours on four cores and rewrites `results/`.
`python run.py all --quick` takes about forty minutes, is for checking the plumbing, and leaves
`results/` alone, so a quick check can never replace committed results. The projection saves its
runs to `data/projections/runs.pkl`; `python run.py project --tabulate-only` rebuilds every table
and predictive interval from them in a few minutes, for example after the error model changes.
Individual stages:

```bash
python run.py test
python run.py backtest                     # --quick: point forecasts and inference only
python run.py project --runs 40            # --scenarios stabilising,high_retention to narrow it
python run.py project --tabulate-only      # tables and intervals again from the saved runs
python run.py recovery --reps 20           # simulation study of the switching estimator
python run.py experiments --only ablation  # ablation | sensitivity | sorting
python run.py checks                       # exit code 0 = every check passed
python run.py figures                      # --png also draws the matplotlib maps
python run.py report --export              # writes results/
```

## Checklist

| | Item | How it is met |
|---|---|---|
| ☑ | Fixed seeds | `random_seed` in `config/assumptions.json` (2026). Every stage derives its draws from it. Run *r* uses the same draws in every scenario. |
| ☑ | Parallel and deterministic | Monte Carlo runs, replicate fits and history fits use every core (`--workers N`, or `RELIGION_FORECAST_WORKERS`). Each run draws from its own streams, so results do not depend on the number of processes; `test_integration_reproducible_and_exact` checks one process against two. |
| ☑ | One entry point | `run.py`, with one subcommand per stage and `all` for the pipeline. After `pip install -e .` the same commands run as `religion-forecast <stage>`. |
| ☑ | Pinned environment | `requirements-lock.txt` pins the exact versions everything was verified under (Python 3.13.16, numpy 2.5.3, pandas 3.0.5). `pyproject.toml` declares the ranges and two optional extras: `maps` and `prepare`. Core needs only numpy, pandas, openpyxl and requests. |
| ☑ | Centralised configuration | `config/assumptions.json` holds every non-data number with a `status` field; `religion_forecast/config.py` holds every path. No module computes a path from its own location. |
| ☑ | Documented data sources | `docs/DATA.md`: coverage, dates, licence, access route and limitation for each; `inputs/*.csv` carry a citation and an evidence grade per row. |
| ☑ | Data provenance recorded per run | `data/projections/projection_report.json` lists every input with `used`, `fallback` or `missing` and a detail string; `parameter_provenance.csv` tags every parameter observed / estimated / assumption / unverified. |
| ☑ | Automated tests and lint | `tests/test_model.py`, 28 tests, and `ruff` with the settings in `pyproject.toml`, both run in CI. Unit tests use synthetic data and read no files: among them a stationary life table, the survey likelihood against its closed form, the first-order switching effect against two engine steps for young and old populations, the importance-sampling estimator against a brute-force reference, the optimiser reaching its own optimum, the bounded minority effect, migration volume under soft margins, half-lives, the non-overlapping validation rule, and recovery of a planted forecast-error model and of a planted improvement over persistence. Integration tests use the real inputs and skip cleanly if absent. Run by `run.py test`, and first in `run.py all`. |
| ☑ | Data validation checks | `run.py checks`: shares non-negative and summing to 100%, components adding up to the simulated change, migration conserving people by religion, probabilities in range, diversity in range, start state reported, map coverage, and the switching estimator (replicates agreeing within half a standard error, no degenerate importance sampling, recovery of known hyperparameters). Non-zero exit if any fails. |
| ☑ | Estimator checked by simulation | `run.py recovery` refits the switching model to evidence simulated from known hyperparameters with the real design, and reports bias, RMSE and interval coverage (`estimator_recovery.csv`). |
| ☑ | Reproducible experiment commands | the table above; each stage writes its own report JSON with a UTC timestamp and its settings. |
| ☑ | Figures regenerable | `run.py figures` rebuilds every map and chart from the output CSVs. No figure contains a number that is not in a CSV. |
| ☑ | Committed results | `results/` holds small copies of one run plus the report, the git commit it was produced at (and whether the code was clean, ignoring `results/` itself), and the captured output of `run.py checks`. |
| ☑ | Determinism tested | `test_integration_reproducible_and_exact` asserts that two runs with the same seed give identical output and that the component accounting is exact. |
| ☑ | Installable package | `pip install -e .` installs `religion_forecast` and a `religion-forecast` command, which runs from any directory. |
| ☑ | History preserved | the repository's two former histories are merged, not rewritten; `git log --follow` traces every file. The pre-restructure states are tagged `archive/pre-merge-main` and `archive/pre-merge-research`; the archived experiments removed from the working tree are recoverable from them. |
| ☐ | Containerised environment | not provided. The dependency set is small and version-tolerant; a Dockerfile would still be an improvement. |
| ☑ | Input checksums committed | `config/data_manifest.json` records the source URL, size and SHA-256 of every input the committed results used; `python scripts/verify_data.py` checks a local `data/` against it and exits non-zero on a required mismatch. |
| ☐ | Archived input snapshot | not provided. WRP and Natural Earth are stable; WPP and the UN migrant stocks are revised, so a rerun after a revision will differ. The committed checksums show whether a fresh download matches; an archived copy (for example on Zenodo) would remove the dependence on live URLs. |

## What is not deterministic across machines

- Floating-point summation order can differ between BLAS builds, so shares may differ in the last
  few decimal places. The integrity checks use tolerances of 1e-6 percentage points, far above
  that.
- `run.py fetch` downloads from live URLs. If a source is revised, the manifest hash changes and
  the results will differ; that is the intended signal.
- The matplotlib figures depend on the installed matplotlib and geopandas versions. The SVG
  figures, which the results use, are produced by the package itself and do not.

## Known gap in this environment

The committed run was produced without `data/processed/pew_harmonized.csv`, because the Pew
workbook needs an account. It therefore starts from `inputs/pew2020_start_state.csv`, the same Pew
2020 data, and omits the Pew 2010-2020 backtest window. Supplying the workbook and re-running will change
the numbers slightly and add that window. Every report states which start state it used.
