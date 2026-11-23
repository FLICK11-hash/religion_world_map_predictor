# Working on this project

A short guide for the research team. Start with [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) for what
the project is about.

## Getting set up

1. Ask Conrad to add you to the repository (send the email on your GitHub account).
2. Clone it and install the exact versions the results were made with:

   ```bash
   git clone https://github.com/FLICK11-hash/religion_world_map_predictor.git
   cd religion_world_map_predictor
   python -m venv .venv && . .venv/bin/activate      # Windows: .\.venv\Scripts\activate
   pip install -r requirements-lock.txt
   pip install -e '.[prepare]'
   ```

3. Check that everything works: `python run.py test` (28 tests, under a minute).
4. To run the model you need the input data, which is not stored in the repository:
   `python scripts/prepare_raw_data.py` and `python run.py fetch` download it. Then
   `python run.py all --quick` runs the whole pipeline in about 15 minutes without touching
   `results/`.

You don't need to run anything to read the results: they are committed in `results/`, and
`results/figures/index.html` shows every map and chart.

## Where things are

| To change | Edit |
|---|---|
| an assumption (a fertility range, the switching strength, a scenario) | `config/assumptions.json`; every number there has a `status` and a note saying where it comes from |
| a published figure the model uses (a survey cell, a fertility ratio) | the matching file in `inputs/`, with its source URL ([`inputs/README.md`](inputs/README.md)) |
| how the model works | `religion_forecast/`; [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) lists what each module does |
| the paper | the team's Google Doc in the shared Drive folder; `manuscript/manuscript.md` is the version kept with the code |

## Making a change

1. Make a branch for each piece of work: `git switch -c your-name/short-description`.
2. Keep the tests and the style check passing: `python run.py test` and `ruff check religion_forecast scripts tests run.py`.
   GitHub runs both on every push.
3. Open a pull request into `main` and say what changed and why. If the change moves a number in
   the paper, say which.
4. Update `results/` only with a full run made from committed code (`python run.py all`, about 35
   minutes on four cores). The run records the commit it was made from in `results/run_stamp.json`,
   so a run from uncommitted code is marked as such.

## Conventions

- Every number in the paper comes from a file in `results/`; [`manuscript/README.md`](manuscript/README.md)
  says which.
- An assumption is written down with its source, or marked as an assumption, in
  `config/assumptions.json`. A figure from a report is checked against the report before it is
  marked verified.
- Years after 2100 are exploratory and are always labelled that way.
