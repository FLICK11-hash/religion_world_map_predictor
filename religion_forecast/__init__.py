"""A cohort-component projection of religious populations by country.

The population of every country is held as persons by religion, generation and five-year age
group, and moved forward in five-year steps by births, deaths, religious switching and
international migration. Each mechanism's contribution to every share change is recorded, so the
components add up exactly to the simulated change.

Modules
    config       paths and the assumptions file
    sources      readers for the World Religion Project and Natural Earth
    datasets     every input loader, with a record of what was found
    engine       the cohort-component step (numpy only, reads no files)
    switching    lifetime survey matrices -> age-specific rates; hierarchical estimation
    migration    origin-destination flows that conserve people exactly
    model        run parameters, scenarios, the initial state, `simulate` and `hindcast`
    calibration  fitting switching and the religion of migrants to evidence
    projection   scenario x Monte Carlo runs
    tables       the output tables of a run
    backtest     forward-chaining history tests and interval calibration
    experiments  mechanism ablations, global sensitivity, migrant-sorting sensitivity
    report       the comparison report and the committed results folder
    checks       integrity checks on the outputs
    figures      maps and charts (vector SVG; optional matplotlib PNG)
"""
__version__ = '1.0.0'
