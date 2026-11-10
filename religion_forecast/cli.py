#!/usr/bin/env python3
"""Single entry point for the religious-composition projection.

    python run.py all                 the whole pipeline (about an hour), then results/ is rewritten
    python run.py all --quick         fewer Monte Carlo runs (about fifteen minutes); results/ is
                                      left alone, so committed results are never replaced by a check
    python run.py <stage> [options]   one stage; `python run.py <stage> --help` for its options

After `pip install -e .` the same commands are available as `religion-forecast <stage>`.

Stages, in pipeline order:
    fetch        download the optional datasets into data/raw/extra (once; needs internet)
                 the three core inputs come from scripts/prepare_raw_data.py
    test         unit and integration tests
    backtest     forward-chaining history tests, country-level inference, the forecast-error
                 record and its predictive-interval calibration, migration checks
    project      the scenario x Monte Carlo projection
    recovery     simulation study: does the switching estimator recover known hyperparameters
                 under the real design, and do its intervals cover them
    experiments  mechanism ablations, global sensitivity, migrant-sorting sensitivity
    checks       integrity checks on the outputs (exit code 0 = all passed)
    figures      maps and charts as SVG (add --png for the matplotlib versions)
    report       the comparison report (outputs/), and results/ with --export

Before any of this the three core inputs must be in data/raw (see README.md):
WRP_national.csv, WPP2024_Demographic_Indicators_Medium.csv.gz, ne_50m_admin_0_countries.zip.
"""
from __future__ import annotations

import subprocess
import sys
import time

from religion_forecast import config

HERE = config.PROJECT


def _run_tests(argv: list[str]) -> int:
    return subprocess.call([sys.executable, str(HERE / 'tests' / 'test_model.py'), *argv], cwd=HERE)


def _stage(name: str, argv: list[str]) -> int:
    if name == 'test':
        return _run_tests(argv)
    from importlib import import_module
    module = {'fetch': 'fetch', 'backtest': 'backtest', 'project': 'projection', 'recovery': 'recovery',
              'experiments': 'experiments', 'checks': 'checks', 'report': 'report'}.get(name)
    if module:
        return import_module(f'religion_forecast.{module}').main(argv) or 0
    if name == 'figures':
        png = '--png' in argv
        rest = [a for a in argv if a != '--png']
        code = import_module('religion_forecast.figures.svg').main(rest) or 0
        if png:
            code = import_module('religion_forecast.figures.mpl').main(rest) or code
        return code
    raise SystemExit(f'unknown stage: {name}')


STAGES = ['fetch', 'test', 'backtest', 'project', 'recovery', 'experiments', 'checks', 'figures', 'report']
ALL_STAGES = ['test', 'backtest', 'project', 'recovery', 'experiments', 'checks', 'figures', 'report']


def main(argv: list[str] | None = None) -> int:
    # Arguments are split by hand rather than with a sub-parser: everything after the stage name
    # belongs to that stage, including flags the pipeline itself also understands. `backtest
    # --quick` must reach the backtest, not be eaten here.
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    stage, rest = argv[0], argv[1:]
    if stage not in STAGES + ['all']:
        print(f'unknown stage: {stage}\n\n{__doc__}', file=sys.stderr)
        return 2
    if stage != 'all':
        return _stage(stage, rest)

    unknown = [a for a in rest if a not in ('--quick', '--png')]
    if unknown:
        print(f'`all` takes only --quick and --png; got {unknown}. Run one stage to pass it options.',
              file=sys.stderr)
        return 2
    quick = {'project': ['--quick'], 'experiments': ['--runs', '4', '--sensitivity-runs', '24'],
             'backtest': ['--error-runs', '8'], 'recovery': ['--quick']} if '--quick' in rest else {}
    t0 = time.time()
    for name in ALL_STAGES:
        extra = list(quick.get(name, []))
        if name == 'report' and '--quick' not in rest:
            extra.append('--export')
        if name == 'figures' and '--png' in rest:
            extra.append('--png')
        print(f'\n=== {name} {" ".join(extra)} ===', flush=True)
        code = _stage(name, extra)
        if code:
            print(f'{name} failed with exit code {code}', file=sys.stderr)
            return code
    where = 'outputs/comparison_report.md (results/ unchanged: quick runs are not exported)' if '--quick' in rest \
        else 'outputs/comparison_report.md; committed copies: results/'
    print(f'\nPipeline finished in {(time.time() - t0) / 60:.0f} min. Report: {where}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
