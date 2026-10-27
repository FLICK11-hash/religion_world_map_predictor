"""Compatibility shim for the archived Step 5D/5E scripts.

Four legacy scripts do `import wrp_history as H`. That module was renamed to
religion_forecast/sources.py without changes: the two files are byte-identical
(compare against commit b3f3302^). Re-exporting it under its old name lets the
archived scripts import again without editing any of them.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from religion_forecast.sources import *  # noqa: E402,F401,F403
from religion_forecast import sources as _sources  # noqa: E402

__all__ = [n for n in dir(_sources) if not n.startswith('_')]
