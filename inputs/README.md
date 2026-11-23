# Published figures the model uses

These are small tables transcribed by hand from published sources, so the model can run without
anything behind a login. Each file opens with comment lines (`#`) that give its source and explain
its columns; the code skips them. Most files also record a source URL and an evidence grade on every
row (`evidence_type`): a figure read from a report's tables ranks above one read from page text,
which ranks above secondary reporting.

| File | What it holds | How the model uses it |
|---|---|---|
| `pew2020_start_state.csv` | religious composition of every country in 2020 (Pew 2025), in eight groups | the starting population when Pew's 2010-2020 workbook has not been prepared |
| `switching_lifetime_observed.csv` | 67 survey cells of lifetime switching: the share of adults raised in one religion who now identify with another, in 33 countries | evidence for the switching model (`religion_forecast/switching.py`) |
| `switching_global_targets.csv` | Pew's 2025 figures for adults 18-54 in 117 countries: people raised in a religion who have left it, per 100 | defines the "survey level" of switching that every run mixes with the level fitted to history |
| `fertility_by_religion.csv` | fertility by religious group, with the reference fertility the same source reports | within-country fertility differences between religions, from the most local figure available |
| `migrant_religion_published.csv` | the religious composition of migrants (Pew 2024), for the world, Europe, the Middle East and North Africa, India-born migrants and US foreign-born adults | fits who migrates where by religion (`religion_forecast/calibration.py`) |
| `second_generation_published.csv` | how often immigrants and their children keep the religion they were raised in (France; 33 European countries) | sets the switching ranges for first- and second-generation migrants in `config/assumptions.json` |
| `published_reference_figures.csv` | Pew's published world shares for 2010 and 2020 | a reference for checking by hand; not read by the code |

In the switching and fertility files, rows marked `verified=no` are excluded; in the migrant file,
rows taken from news reports are not used. Before the paper is submitted, every row graded as page
text or secondary reporting should be checked against the original report.
