"""Entrypoint: python -m ws_gateway.main"""

from __future__ import annotations

import asyncio
import logging
import pathlib
import sys

_CHESS_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _path in (_CHESS_ROOT,):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from ws_gateway.net.ws_server import run_server  # noqa: E402


def main() -> None:
    handlers = [logging.StreamHandler()]
    try:
        _logs_dir = _CHESS_ROOT / "logs"
        _logs_dir.mkdir(exist_ok=True)
        handlers.append(logging.FileHandler(_logs_dir / "ws_gateway.log", encoding="utf-8"))
    except OSError:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
