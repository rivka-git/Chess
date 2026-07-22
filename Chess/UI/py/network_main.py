"""Entrypoint for the networked (multiplayer) client.

Usage: python UI/py/network_main.py [--gui] [server_uri]

Home screen has two options for the same flow (network/home_flow.py):
  * default: shell/console login + Play/Room choice -- the CR-required path.
  * --gui:   tkinter login + home windows instead.
Either way the Room sub-flow uses the GUI dialog the presentation depicts, and
the server auto-registers unknown usernames so login doubles as sign-up.
"""

from __future__ import annotations

import logging
import os
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_UI_PY = pathlib.Path(__file__).resolve().parent
for _path in (_ROOT, _UI_PY):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from console.console_home import ConsoleHomeFrontend  # noqa: E402
from network.home_flow import run_home_flow  # noqa: E402
from network.home_gate import HomeGate  # noqa: E402
from network.ws_client import WsClient  # noqa: E402
from ui_network_bootstrap import build_networked_ui_app  # noqa: E402

DEFAULT_SERVER_URI = "ws://localhost:8765"


def _configure_logging() -> None:
    # Per-pid file so two client windows launched from the same folder don't
    # clobber each other's log. File only, so it doesn't fight with the
    # login/home-screen prompts on the console.
    log_path = _ROOT / "logs" / f"client-{os.getpid()}.log"
    log_path.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8")],
    )


def _build_frontend(use_gui: bool):
    if use_gui:
        from gui.gui_home import GuiHomeFrontend
        return GuiHomeFrontend()
    return ConsoleHomeFrontend()


def main() -> None:
    _configure_logging()
    args = sys.argv[1:]
    use_gui = "--gui" in args
    positional = [a for a in args if not a.startswith("--")]
    server_uri = positional[0] if positional else DEFAULT_SERVER_URI

    gate = HomeGate(WsClient(server_uri))
    frontend = _build_frontend(use_gui)
    if not run_home_flow(gate, frontend):
        print("Exiting.")
        return
    build_networked_ui_app(gate).run()


if __name__ == "__main__":
    main()
