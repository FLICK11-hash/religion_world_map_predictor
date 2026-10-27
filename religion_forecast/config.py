"""Paths and model assumptions, in one place.

Every other module imports its directories from here, so the project can be moved or run from any
working directory. Nothing outside `PROJECT` is read or written.

Layout (relative to PROJECT)
    config/assumptions.json  every non-data number, each tagged with how it was obtained
    inputs/                  small published figures transcribed with citations (tracked in git)
    data/raw/                downloaded source data (git-ignored)
    data/processed/          cleaned panels from the data-preparation scripts (git-ignored)
    data/projections/        projection output of one run (git-ignored)
    data/validation/         backtest output (git-ignored)
    data/experiments/        ablation, sensitivity and coverage output (git-ignored)
    outputs/figures/         figures (git-ignored)
    results/                 small copies of a run, committed so a reader can check the numbers
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parent
PROJECT = PACKAGE.parent

CONFIG = PROJECT / 'config'
INPUTS = PROJECT / 'inputs'
DATA = PROJECT / 'data'
RAW = DATA / 'raw'
PROCESSED = DATA / 'processed'
PROJECTIONS = DATA / 'projections'
VALIDATION = DATA / 'validation'
EXPERIMENTS = DATA / 'experiments'
FIGURES = PROJECT / 'outputs' / 'figures'
FIGURES_PNG = PROJECT / 'outputs' / 'figures_png'
RESULTS = PROJECT / 'results'
LEGACY_RESULTS = PROJECT / 'results_step5'

# Optional downloads (fetch.py). `data/raw/step7` is where earlier versions put them; it is still
# read so that an existing download does not have to be repeated.
RAW_EXTRA = RAW / 'extra'
RAW_EXTRA_ALT = RAW / 'step7'

ASSUMPTIONS = CONFIG / 'assumptions.json'


def extra_dirs() -> list[Path]:
    """Directories searched for the optional downloaded datasets, newest convention first."""
    return [d for d in (RAW_EXTRA, RAW_EXTRA_ALT) if d.exists()] or [RAW_EXTRA]


def find_extra(pattern: str) -> list[Path]:
    """Files matching `pattern` in any optional-download directory, sorted by name."""
    return sorted(p for d in extra_dirs() for p in d.glob(pattern))


def load_assumptions(path: Path | None = None) -> dict[str, Any]:
    """The assumptions file as a dict. Every leaf with a `status` field says how it was obtained:
    observed, estimated, assumption or unverified (see parameter_provenance.csv in the results)."""
    return json.loads((path or ASSUMPTIONS).read_text(encoding='utf8'))
