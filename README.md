# Projecting the religious composition of countries

[![tests](https://github.com/FLICK11-hash/religion_world_map_predictor/actions/workflows/tests.yml/badge.svg)](https://github.com/FLICK11-hash/religion_world_map_predictor/actions/workflows/tests.yml)

**A probabilistic cohort-component model of every country's religions to 2100, and an honest test
of how well it can forecast.** Applied statistics and statistical demography (arXiv `stat.AP`).

![World religious composition 2020-2100 with 90% predictive intervals](manuscript/figures/world_projection_2100.png)

The model follows the population of 200 countries by religion (8 groups), migrant generation and
age, and moves it forward in five-year steps through births, deaths, religious switching and
migration. Every change in a country's religious make-up is attributed exactly to the mechanism
that caused it. The model is tested on five decades, 1970-2020 (the World Religion Project for
1970-2010 and Pew's estimates for 2010-2020), with everything fitted only on earlier data, and its
uncertainty intervals are built from the errors it made there.

**New here?** Read [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) first, a short overview for
collaborators, and [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to set up and make changes. The paper draft is [`manuscript/manuscript.md`](manuscript/manuscript.md), and the
team's files are in the
[shared Google Drive folder](https://drive.google.com/drive/folders/1sqJtRGLf7Vcu7QMQzK11AN-7bmgUzlXe?usp=drive_link).

## Main findings

- **Nothing beats "no change" over a decade.** Over 758 country-decades, births and deaths alone
  are at most about 2% more accurate than assuming nothing changes. Switching fitted to past change
  does not help (slightly worse in 1970-2010, slightly better in 2010-2020, neither distinguishable
  from no change), and repeating the last decade's change is clearly worse.
- **The model's own uncertainty is far too narrow, but honest intervals can be built.** Its Monte
  Carlo bands contain the truth about a quarter of the time at nominal 90%. Intervals built from
  its past errors contain 85-88% of held-out observations at 10 to 30 years and 78% at 40 years.
- **Islam becomes the world's largest religion by 2100.** Its share rises from 25.6% to 39.2% (90%
  interval 36.6-43.2%) while Christianity's falls from 28.8% to 26.1% (22.8-29.3%). About three
  quarters of Islam's rise is the faster population growth of Muslim-majority countries.
- **Within countries, religious switching drives the change.** In 32 countries the largest religion
  is more likely than not to change by 2100, almost all to no religion: France 86%, United Kingdom
  83%, Germany 76%, United States 56%.

These are projections under stated assumptions, conditional on the UN's population projections.
The maps for 2200, 2500 and 3026 are exploratory. [`docs/RESULTS.md`](docs/RESULTS.md) has the
tables and [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) what they do and do not support. One of the
run's integrity checks fails: in the simulation study the estimator puts the spread of switching
between countries about 10% too low (`results/integrity_checks.txt`, check 9c).

## The projected maps

Each map shows the largest religion in every country in one year, under the reference scenario
(`stabilising`). The colour is the most frequent result across the 40 Monte Carlo runs, so it
reflects parameter uncertainty only; how likely a change really is, once the model's past forecast
errors are included, is in [`results/figures/prob_dominant_change_2100.svg`](results/figures/prob_dominant_change_2100.svg)
and `results/projection/dominant_change.csv`. Grey means no estimate.

World shares in the same scenario (percent of world population; 2050 and 2100 with their 90%
predictive intervals in [`docs/RESULTS.md`](docs/RESULTS.md)):

| Religion | 2020 | 2050 | 2100 | 2200 | 2500 | 3026 |
|---|---|---|---|---|---|---|
| Islam | 25.6 | 31.7 | 39.2 | 43.7 | 44.1 | 42.0 |
| Christianity | 28.8 | 27.8 | 26.1 | 22.9 | 21.1 | 19.8 |
| Unaffiliated | 24.2 | 20.7 | 19.1 | 22.6 | 27.6 | 32.2 |
| Hinduism | 14.9 | 14.5 | 12.0 | 8.5 | 5.2 | 3.9 |
| Buddhism | 4.1 | 3.1 | 1.7 | 0.8 | 0.4 | 0.3 |
| Folk/Traditional | 1.4 | 1.3 | 1.0 | 0.9 | 1.0 | 1.1 |
| Other | 0.8 | 0.7 | 0.5 | 0.4 | 0.3 | 0.4 |
| Judaism | 0.2 | 0.2 | 0.2 | 0.3 | 0.3 | 0.4 |

Number of countries (of 200) in which each religion is the largest:

| Largest religion | 2020 | 2050 | 2100 | 2200 | 2500 | 3026 |
|---|---|---|---|---|---|---|
| Christianity | 122 | 117 | 94 | 57 | 29 | 19 |
| Islam | 54 | 54 | 55 | 61 | 80 | 98 |
| Unaffiliated | 11 | 18 | 41 | 74 | 88 | 80 |
| Buddhism | 8 | 6 | 6 | 4 | 1 | 1 |
| Hinduism | 3 | 3 | 3 | 3 | 2 | 2 |
| Judaism | 1 | 1 | 1 | 1 | 0 | 0 |
| Folk/Traditional | 1 | 1 | 0 | 0 | 0 | 0 |

### 2050

![Largest religion by country, 2050](results/figures/dominant_2050.svg)

Thirty years out, the map is almost the one of 2020: the largest religion changes in only 7
countries. In the United Kingdom, France, Australia, Belgium and Estonia people with no religion
overtake Christians, and in Singapore and Mongolia they overtake Buddhists. The world already looks different
in its totals: the Muslim share rises from 25.6% to 31.7%, four fifths of it because the populations
of Muslim-majority countries grow faster.

### 2100

![Largest religion by country, 2100](results/figures/dominant_2100.svg)

By 2100 the largest religion has changed in 31 countries, 27 of them from Christianity to no
religion, among them the United States, Brazil, Germany, the United Kingdom, France, Italy, Spain,
Argentina, Canada and Australia. Mongolia and Singapore change from Buddhism and Taiwan from folk
religion to no religion, and North Macedonia changes from Christianity to Islam. Islam becomes the
largest religion in the world (39.2%, 90% interval 36.6-43.2%), ahead of Christianity (26.1%,
22.8-29.3%). Once past forecast errors are included, 32 countries have a better-than-even chance of
changing (France 86%, United Kingdom 83%, Germany 76%, United States 56%). In the United States and
Brazil it is close to a coin toss: no religion ends about a point ahead of Christianity, with
intervals that overlap almost entirely. This is the last year with predictive intervals: beyond 2100 there are no UN
population projections and every input becomes a stated assumption.

### 2200 (exploratory)

![Largest religion by country, 2200](results/figures/dominant_2200.svg)

If switching continues at the assumed pace and slows only gradually, people with no religion become
the largest group in much of the Americas and Europe, including the United States, Brazil and
Mexico, and the unaffiliated lead in 74 countries against 57 for Christianity. Islam becomes the
largest religion in 61 countries, adding Ethiopia, Benin, Cyprus, Malta, Montenegro and Singapore.
Islam reaches 43.7% of the world.

### 2500 (exploratory)

![Largest religion by country, 2500](results/figures/dominant_2500.svg)

The map now reflects the long-run assumptions more than any current trend: fertility converging
across countries, switching fading towards a floor, and migration continuing at 2100 rates. Islam
is the largest religion in 80 countries, including Russia, Italy, Greece, Sweden and much of East
Africa (Ethiopia, Tanzania, Mozambique); the unaffiliated lead in 88. Christianity remains the
largest in 29 countries, mostly in central, eastern and southern Africa and the Pacific.

### 3026 (exploratory)

![Largest religion by country, 3026](results/figures/dominant_3026.svg)

A thousand years from today, under the same assumptions, the world divides between two groups:
Islam is the largest religion in 98 countries and the unaffiliated in 80, with 42% and 32% of the
world's population. Christianity remains the largest in 19 countries, among them the Philippines,
DR Congo, Angola, Zambia and Zimbabwe; Hinduism in India and Nepal, and Buddhism in Cambodia. This
map shows what a fixed set of long-run assumptions implies after a millennium, not what will happen:
the eight scenarios disagree by up to 66 percentage points on the world Muslim and unaffiliated shares by then
([`results/figures/world_composition_long_run.svg`](results/figures/world_composition_long_run.svg)).

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

`python run.py all` stops if an integrity check fails, before the figures and the report. To finish
such a run, use `python run.py figures` and `python run.py report --export`; the failure stays
recorded in `results/integrity_checks.txt` and `results/run_stamp.json`, as in the committed run.

Pew's country data for 2010 and 2020 (the Global Religious Futures dataset, free Pew account) is used
in the committed run but is not redistributed. Put it in `data/raw/` and run
`python scripts/prepare_pew_panel.py` before `python run.py all`; this adds the 2010-2020 test
decade. After the run, `python scripts/benchmark_pew2026.py` compares it with Pew's own 2026
projections. Every stage, the
code layout and the reproducibility checklist are in
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md); every dataset is described in
[`docs/DATA.md`](docs/DATA.md).

## Repository

| Folder | Contents |
|---|---|
| `religion_forecast/` | the model and its evaluation (Python package) |
| `results/` | one complete committed run: report, figures and tables |
| `manuscript/` | the paper draft and its figures, including PNG versions of every map above |
| `docs/` | methods, results, limitations, data, reproducibility |
| `config/`, `inputs/` | every assumption, and the published figures the model uses, with sources ([`inputs/README.md`](inputs/README.md)) |
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
