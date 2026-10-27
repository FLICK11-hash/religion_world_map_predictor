#!/usr/bin/env python3
"""Single entry point for the religious-composition projection.

    python run.py all                 the whole pipeline (about an hour)
    python run.py all --quick         the same, with fewer Monte Carlo runs (about ten minutes)
    python run.py <stage> [options]   one stage; `python run.py <stage> --help` for its options

After `pip install -e .` the same commands are available as `religion-forecast <stage>`.

Stages, in pipeline order:
    fetch        download the optional datasets into data/raw/extra (once; needs internet)
                 the three core inputs come from scripts/prepare_raw_data.py
    test         unit and integration tests
    backtest     forward-chaining history tests, interval calibration, migration checks
    project      the scenario x Monte Carlo projection
    experiments  mechanism ablations, global sensitivity, migrant-sorting sensitivity
    checks       integrity checks on the outputs (exit code 0 = all passed)
    figures      maps and charts as SVG (add --png for the matplotlib versions)
    report       the comparison report, and results/ for committing

Before any of this the three core inputs must be in data/raw (see README.md):
WRP_national.csv, WPP2024_Demographic_Indicators_Medium.csv.gz, ne_50m_admin_0_countries.zip.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from religion_forecast import config

HERE = config.PROJECT


def _run_tests(argv: list[str]) -> int:
    return subprocess.call([sys.executable, str(HERE / 'tests' / 'test_model.py'), *argv], cwd=HERE)


def _stage(name: str, argv: list[str]) -> int:
    if name == 'test':
        return _run_tests(argv)
    from importlib import import_module
    module = {'fetch': 'fetch', 'backtest': 'backtest', 'project': 'projection',
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


STAGES = ['fetch', 'test', 'backtest', 'project', 'experiments', 'checks', 'figures', 'report']
ALL_STAGES = ['test', 'backtest', 'project', 'experiments', 'checks', 'figures', 'report']


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
             'backtest': ['--quick']} if '--quick' in rest else {}
    t0 = time.time()
    for name in ALL_STAGES:
        extra = list(quick.get(name, []))
        if name == 'report':
            extra.append('--export')
        if name == 'figures' and '--png' in rest:
            extra.append('--png')
        print(f'\n=== {name} {" ".join(extra)} ===', flush=True)
        code = _stage(name, extra)
        if code:
            print(f'{name} failed with exit code {code}', file=sys.stderr)
            return code
    print(f'\nPipeline finished in {(time.time() - t0) / 60:.0f} min. '
          f'Report: outputs/comparison_report.md; committed copies: results/')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
