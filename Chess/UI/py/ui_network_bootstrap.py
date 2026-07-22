"""Concrete wiring for a networked (multiplayer) UI, parallel to ui_bootstrap.py's
build_default_ui_app(). The only difference from the local build is what
controller_factory produces: a RemoteController talking to a WebSocket
server instead of a Controller wrapping a local GameEngine. UIRunner,
Renderer, AnimationManager, MouseHandler, and SoundEventDetector are shared
unchanged, since they only ever depend on the ControllerLike protocol.

Takes an already-connected HomeGate that has already driven login and the
Play/Room seating exchange (see console/login_prompt.py and
network/home_gate.py) before this GUI app is ever built. RemoteController is
only constructed once UIApp.run() actually calls controller_factory, so the
handoff of buffered post-seating messages happens right here, immediately
after RemoteController takes over the connection."""

from __future__ import annotations

import pathlib

from adapter.sound_event_detector import SoundEventDetector
from animation.animation_manager import AnimationManager
from assets.asset_loader import AssetLoader
from audio.sound_effects import SoundEffects
from config import CELL_SIZE_PX
from controls.mouse_handler import MouseHandler
from controls.window import Window
from geometry.board_geometry import BoardGeometry
from core.ioutils.board_parser import TextBoardParser
from loop.ui_runner import UIRunner
from network.remote_controller import RemoteController
from render.hud_overlay import overlay_from_controller
from render.renderer import Renderer
from ui_app import UIApp
from netcommon.defaults import DEFAULT_BOARD_TEXT

MOVE_LOG_PANEL_WIDTH_PX = 280


def build_networked_ui_app(home_gate) -> UIApp:
    sounds_dir = pathlib.Path(__file__).resolve().parents[1] / "sounds"
    sound_effects = SoundEffects(sounds_dir)
    # UIApp.run() builds the controller before the renderer, so this holder is
    # populated by controller_factory in time for renderer_factory to read it.
    holder: dict = {}

    def controller_factory(_local_engine) -> SoundEventDetector:
        remote = RemoteController(home_gate.ws_client)
        home_gate.handoff(remote._on_message)
        detector = SoundEventDetector(remote, sound_effects)
        remote._sound_detector = detector
        holder["remote"] = remote
        return detector

    def move_log_lines():
        remote = holder.get("remote")
        return [] if remote is None else remote.move_log.lines()

    def renderer_factory(asset_loader, window, cell_size):
        return Renderer(
            asset_loader, window, cell_size,
            overlay_provider=lambda: overlay_from_controller(holder.get("remote")),
            panel_width=MOVE_LOG_PANEL_WIDTH_PX,
            move_log_provider=move_log_lines,
        )

    return UIApp(
        board_parser=TextBoardParser(),
        engine_factory=lambda board: None,
        controller_factory=controller_factory,
        asset_loader=AssetLoader(),
        geometry=BoardGeometry(CELL_SIZE_PX),
        animation_manager_factory=AnimationManager,
        window=Window(),
        mouse_handler_factory=lambda window, controller: MouseHandler(
            window, controller, CELL_SIZE_PX
        ),
        renderer_factory=renderer_factory,
        runner_factory=UIRunner,
        cell_size_px=CELL_SIZE_PX,
        default_board_text=DEFAULT_BOARD_TEXT,
    )
