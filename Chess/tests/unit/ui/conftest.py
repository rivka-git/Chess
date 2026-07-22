"""Pytest configuration for UI unit tests."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
for _path in (ROOT, ROOT / "UI" / "py"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
