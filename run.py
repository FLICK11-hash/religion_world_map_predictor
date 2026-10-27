#!/usr/bin/env python3
"""Entry point for the religious-composition projection. See `python run.py --help`.

The command-line logic lives in religion_forecast/cli.py so that it also installs as the
`religion-forecast` command. This file keeps `python run.py <stage>` working from a checkout.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from religion_forecast.cli import main  # noqa: E402

if __name__ == '__main__':
    raise SystemExit(main())
