"""Pytest configuration for importing UI/py modules (adapter, network, ...)."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "UI" / "py"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
