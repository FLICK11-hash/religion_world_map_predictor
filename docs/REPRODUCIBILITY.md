# Reproducibility

## Exact commands

From `religion_forecast_step1/religion_forecast_step1/`:

```bash
python -m venv .venv && . .venv/bin/activate          # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt

python prepare_raw_data.py        # downloads WRP, WPP 2024 and Natural Earth; writes a SHA-256 manifest
# download data/raw/pew_2010_2020.xlsx by hand (free Pew account), then:
python prepare_pew_panel.py       # writes data/processed/pew_harmonized.csv

python run.py fetch               # the optional datasets, once
python run.py all                 # test, backtest, project, experiments, checks, figures, report
```

`python run.py all` takes about an hour on four cores; `--quick` takes about ten minutes and is
for checking the plumbing, not for results. Individual stages:

```bash
python run.py test
python run.py backtest                     # add --quick to skip ablations and interval calibration
python run.py project --runs 40            # --scenarios stabilising,high_retention to narrow it
python run.py experiments --only ablation  # ablation | sensitivity | sorting
python run.py checks                       # exit code 0 = every check passed
python run.py figures                      # --png also draws the matplotlib maps
python run.py report --export              # writes results/
```

## Checklist

| | Item | How it is met |
|---|---|---|
| ☑ | Fixed seeds | `random_seed` in `config/assumptions.json` (2026). Every stage derives its draws from it. Run *r* uses the same draws in every scenario. |
| ☑ | One entry point | `run.py`, with one subcommand per stage and `all` for the pipeline. |
| ☑ | Pinned environment | `requirements.txt`. Core needs only numpy, pandas, openpyxl and requests; matplotlib and geopandas are optional and used by one figure path. |
| ☑ | Centralised configuration | `config/assumptions.json` holds every non-data number with a `status` field; `religion_forecast/config.py` holds every path. No module computes a path from its own location. |
| ☑ | Documented data sources | `docs/DATA.md`: coverage, dates, licence, access route and limitation for each; `inputs/*.csv` carry a citation and an evidence grade per row. |
| ☑ | Data provenance recorded per run | `data/projections/projection_report.json` lists every input with `used`, `fallback` or `missing` and a detail string; `parameter_provenance.csv` tags every parameter observed / estimated / assumption / unverified. |
| ☑ | Automated tests | `tests/test_model.py`, 15 tests. Unit tests use synthetic data and read no files; integration tests use the real inputs and skip cleanly if absent. Run by `run.py test`, and first in `run.py all`. |
| ☑ | Data validation checks | `run.py checks`: shares non-negative and summing to 100%, components adding up to the simulated change, migration conserving people by religion, probabilities in range, diversity in range, start state reported, map coverage. Non-zero exit if any fails. |
| ☑ | Reproducible experiment commands | the table above; each stage writes its own report JSON with a UTC timestamp and its settings. |
| ☑ | Figures regenerable | `run.py figures` rebuilds every map and chart from the output CSVs. No figure contains a number that is not in a CSV. |
| ☑ | Committed results | `results/` holds small copies of one run plus the report, the git commit it was produced at, and the captured output of `run.py checks`. |
| ☑ | Determinism tested | `test_integration_reproducible_and_exact` asserts that two runs with the same seed give identical output and that the component accounting is exact. |
| ☐ | Containerised environment | not provided. The dependency set is small and version-tolerant; a Dockerfile would still be an improvement. |
| ☐ | Archived input snapshot | not provided. WRP and Natural Earth are stable; WPP and the UN migrant stocks are revised, so a rerun after a revision will differ. The SHA-256 manifests (`data/step1_manifest.json`, `data/raw/extra/manifest.json`) record exactly which files a run used. |

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
workbook needs an account. It therefore starts from the Step 5D export of the same Pew 2020 data
and omits the Pew 2010-2020 backtest window. Supplying the workbook and re-running will change
the numbers slightly and add that window. Every report states which start state it used.
