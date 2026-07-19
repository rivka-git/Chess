"""Entrypoint for the networked (multiplayer) client.

Usage: python UI/py/network_main.py [server_uri]

M2 stub: the server auto-assigns White/Black by connection order, no home
screen yet (that arrives in Milestone 3 and will prompt for a username
before calling build_networked_ui_app(...).run()).
"""

from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_UI_PY = pathlib.Path(__file__).resolve().parent
for _path in (_ROOT, _UI_PY):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from ui_network_bootstrap import build_networked_ui_app  # noqa: E402

DEFAULT_SERVER_URI = "ws://localhost:8765"


def main() -> None:
    server_uri = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SERVER_URI
    build_networked_ui_app(server_uri).run()


if __name__ == "__main__":
    main()
