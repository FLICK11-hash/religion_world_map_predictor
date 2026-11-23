# Projecting the religious composition of countries

**A probabilistic cohort-component model of every country's religions to 2100, and an honest test
of how well it can forecast.** Applied statistics and statistical demography (arXiv `stat.AP`).

![Largest religion in each country in 2100, reference scenario](results/figures/dominant_2100.svg)

The model follows the population of 200 countries by religion (8 groups), migrant generation and
age, and moves it forward in five-year steps through births, deaths, religious switching and
migration. Every change in a country's religious make-up is attributed exactly to the mechanism
that caused it. The model is tested on the decades 1970-2010 with everything fitted only on earlier
data, and its uncertainty intervals are built from the errors it made there.

**New here?** Read [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) first, a short overview for
collaborators. The paper draft is [`manuscript/manuscript.md`](manuscript/manuscript.md), and the
team's files are in the
[shared Google Drive folder](https://drive.google.com/drive/folders/1sqJtRGLf7Vcu7QMQzK11AN-7bmgUzlXe?usp=drive_link).

## Main findings

- **Nothing beats "no change" over a decade.** Over 558 country-decades, births and deaths alone
  are at most about 2% more accurate than assuming nothing changes. Switching fitted to past change
  makes forecasts slightly worse, and repeating the last decade's change is clearly worse.
- **The model's own uncertainty is far too narrow, but honest intervals can be built.** Its Monte
  Carlo bands contain the truth about a quarter of the time at nominal 90%. Intervals built from
  its past errors contain 86-88% of held-out observations at 10 to 30 years.
- **Islam becomes the world's largest religion by 2100.** Its share rises from 25.6% to 39.1% (90%
  interval 36.7-42.4%) while Christianity's falls from 28.8% to 25.7% (22.6-28.8%). About three
  quarters of Islam's rise is the faster population growth of Muslim-majority countries.
- **Within countries, religious switching drives the change.** In 26 countries the largest religion
  is more likely than not to change by 2100, almost all to no religion: France 89%, United Kingdom
  85%, Germany 78%, United States 42%.

These are projections under stated assumptions, conditional on the UN's population projections.
The maps for 2200, 2500 and 3026 are exploratory. [`docs/RESULTS.md`](docs/RESULTS.md) has the
tables and [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) what they do and do not support.

## See the results without running anything

| | |
|---|---|
| [`results/comparison_report.md`](results/comparison_report.md) | the run report, every table in one page |
| [`results/figures/`](results/figures) | every map and chart; download it and open `index.html` to hover over countries |
| [`results/projection/`](results/projection) | world and country shares by year and scenario, with intervals |
| [`results/validation/`](results/validation) | history tests, interval calibration and the estimator check |
| [`results/experiments/`](results/experiments) | what each mechanism contributes, and which assumptions matter |

## Run it

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .\.venv\Scripts\activate
pip install -r requirements-lock.txt               # the exact versions the results were made with
pip install -e '.[prepare]'
python scripts/prepare_raw_data.py                 # downloads the three core datasets
python run.py fetch                                # the optional datasets
python run.py test                                 # 28 tests, under a minute
python run.py all --quick                          # the whole pipeline in about 15 minutes; results/ untouched
python run.py all                                  # the full run, about 35 minutes on 4 cores; rewrites results/
```

The Pew 2010-2020 workbook needs a free Pew account and is not in the committed run. With it in
`data/raw/`, run `python scripts/prepare_pew_panel.py` before `python run.py all`. Every stage, the
code layout and the reproducibility checklist are in
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md); every dataset is described in
[`docs/DATA.md`](docs/DATA.md).

## Repository

| Folder | Contents |
|---|---|
| `religion_forecast/` | the model and its evaluation (Python package) |
| `results/` | one complete committed run: report, figures and tables |
| `manuscript/` | the paper draft and its figures |
| `docs/` | methods, results, limitations, data, reproducibility |
| `config/`, `inputs/` | every assumption, and the published figures the model uses, with sources |
| `scripts/`, `tests/` | data preparation and the test suite |
| `previous_grad_assignment/` | the two simpler programs from the course exercise the project began as |

## About

The project began in October 2026 as a graduate course exercise and has since been developed as a
research project. Earlier versions of the model remain in the git history (tags
`archive/pre-merge-main` and `archive/pre-merge-research`). Most of the code and documentation was
written with an AI coding assistant under the author's direction; every
reported number is regenerated by the code from documented inputs.

Citation metadata is in [`CITATION.cff`](CITATION.cff). There is no licence file yet, so the code is
under default copyright; each dataset keeps its own terms (`config/data_manifest.json`).
