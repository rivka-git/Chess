"""Concrete wiring for a networked (multiplayer) UI, parallel to ui_bootstrap.py's
build_default_ui_app(). The only difference from the local build is what
controller_factory produces: a RemoteController talking to a WebSocket
server instead of a Controller wrapping a local GameEngine. UIRunner,
Renderer, AnimationManager, MouseHandler, and SoundEventDetector are shared
unchanged, since they only ever depend on the ControllerLike protocol."""

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
from ioutils.board_parser import TextBoardParser
from loop.ui_runner import UIRunner
from network.remote_controller import RemoteController
from network.ws_client import WsClient
from render.renderer import Renderer
from ui_app import UIApp
from ui_config import DEFAULT_BOARD_TEXT


def build_networked_ui_app(server_uri: str) -> UIApp:
    sounds_dir = pathlib.Path(__file__).resolve().parents[1] / "sounds"
    sound_effects = SoundEffects(sounds_dir)

    def controller_factory(_local_engine) -> SoundEventDetector:
        # UIApp.run() always builds a local engine via engine_factory and
        # passes it in here; a networked client has no use for it.
        ws_client = WsClient(server_uri)
        return SoundEventDetector(RemoteController(ws_client), sound_effects, CELL_SIZE_PX)

    return UIApp(
        board_parser=TextBoardParser(),
        engine_factory=lambda board: None,
        controller_factory=controller_factory,
        asset_loader=AssetLoader(),
        geometry=BoardGeometry(CELL_SIZE_PX),
        animation_manager_factory=AnimationManager,
        window=Window(),
        mouse_handler_factory=MouseHandler,
        renderer_factory=Renderer,
        runner_factory=UIRunner,
        cell_size_px=CELL_SIZE_PX,
        default_board_text=DEFAULT_BOARD_TEXT,
    )
