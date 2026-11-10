# Project overview for collaborators

This is a research project in applied statistics and statistical demography (arXiv `stat.AP`). It
asks how the religious composition of every country is likely to change over this century. Its
main concern, though, is a prior question: how well can that be forecast at all, and how wide is
honest uncertainty about it? The best-known projections of the world's religions, Pew Research
Center's of 2015, are deterministic: they give one path, no intervals, and no test against what
later happened. This project builds a probabilistic version of that kind of model and evaluates it
out of sample. It asks three things. Does a mechanistic projection forecast past decades better
than assuming nothing changes? How large is its forecast error, and can that error be turned into
predictive intervals that hold up out of sample? And which mechanisms account for the change it
projects to 2100: fertility, religious switching, migration, or differences in population growth
between countries? A full working-paper draft is in `manuscript/manuscript.md`.

The code (`religion_forecast/`) is a cohort-component simulation. It holds the population of 200
countries as persons by religion (8 groups), migrant generation (3) and five-year age group (17),
and moves them forward in five-year steps. Deaths come from life tables fitted to the UN's World
Population Prospects 2024, and births from religion-specific fertility taken from the most local
published evidence. Religious switching comes from lifetime rates estimated by an empirical Bayes
hierarchical model, fitted to six decades of historical net change and to 48 survey rows. Each run
draws the model's hyperparameters from their approximate posterior, and a simulation study under
the real design checks the estimator. Migration is a set of origin-destination flows that match the
UN's net migration, with a religious mix in each corridor calibrated to Pew's figures on migrants.
Every change in a country's religious shares is attributed exactly to the step that caused it.
Around the simulation sit the history tests, which forecast the decades 1970-2010 with every
parameter fitted only to earlier data, and a model of the errors those forecasts made, which turns
them into predictive intervals. There are also mechanism ablations, a shift-share decomposition and
a global sensitivity analysis. `python run.py all` runs everything in about 35 minutes on four
cores. `results/` holds one committed run with its figures, report and integrity checks, and
`docs/METHODS.md` gives the mathematics.

The findings so far are sobering about prediction but still informative about the century. Over
558 country-decades, no version of the model is distinguishable from assuming no change. Births
and deaths alone come out at −0.03 percentage points of error (95% interval −0.10 to +0.06), so at
most about 2% better than no change. Switching fitted to historical change makes forecasts slightly
worse (+0.72), and repeating the last decade's change is clearly worse (+1.86, 1.21 to 2.41). The
model's own Monte Carlo bands contain the truth about a quarter of the time at nominal 90%. The
intervals built from its past errors contain 86-88% of held-out observations at horizons of 10 to
30 years, which is close to nominal but a few points too narrow, and they are coarser for world
totals (85%). With those intervals, and conditional on the UN's demography, the world Muslim share
rises from 25.6% in 2020 to 39.1% in 2100 (90% interval 36.7-42.4%), and the Christian share falls
to 25.7% (22.6-28.8%). About three quarters of Islam's rise is the faster population growth of
Muslim-majority countries, not change within them. Within countries, switching drives the change:
it is worth about 8 points of the world Christian share by 2100. In 26 countries the largest
religion is more likely than not to change by 2100, almost always to no religion: France 89%, the
United Kingdom 85%, Germany 78%, the United States 42%. `docs/RESULTS.md` and
`docs/LIMITATIONS.md` give the tables, and what they do and do not support.

Help is most useful in four areas:

- **Data that needs an account or a person.**
  - Pew's 2010-2020 workbook would add a test decade: run `scripts/prepare_pew_panel.py`, then
    `python run.py all`.
  - Pew's file of migrants by country of origin would let the minority effect on emigration be
    estimated rather than bounded by assumption.
  - DHS fertility by religion for sub-Saharan Africa.
  - Pew's 2010 median ages by religion need checking. One of the most influential inputs depends on
    them, and they are still marked unverified.
- **Methods.** The intervals need better calibration, ideally with the UN's probabilistic population
  projections, so they carry the national demographic uncertainty they now leave out. The gap
  between the switching level fitted to history (12.8 Christians leaving per 100 raised) and Pew's
  survey level (17.1) needs closing.
- **The draft.** References marked [verify] must be checked, and a licence and target journal
  chosen.

To get started, read `README.md` and `docs/METHODS.md`, run `python run.py test` (28 tests, under a
minute) and `python run.py all --quick` (about 15 minutes), and browse
`results/figures/index.html`.
