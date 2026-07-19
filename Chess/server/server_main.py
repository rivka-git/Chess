"""Entrypoint: python -m server.server_main"""

from __future__ import annotations

import asyncio
import logging
import pathlib
import sys

_CHESS_ROOT = pathlib.Path(__file__).resolve().parent.parent
_UI_PY = _CHESS_ROOT / "UI" / "py"
for _path in (_CHESS_ROOT, _UI_PY):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from server.net.ws_server import run_server  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
