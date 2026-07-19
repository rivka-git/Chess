"""Concrete wiring for the UI dependency graph."""
from __future__ import annotations

import pathlib

from adapter.controller import Controller
from animation.animation_manager import AnimationManager
from audio.sound_effects import SoundEffects
from assets.asset_loader import AssetLoader
from config import CELL_SIZE_PX
from controls.mouse_handler import MouseHandler
from controls.window import Window
from engine.game_engine import GameEngine
from geometry.board_geometry import BoardGeometry
from ioutils.board_parser import TextBoardParser
from loop.ui_runner import UIRunner
from render.renderer import Renderer
from ui_app import UIApp
from ui_config import DEFAULT_BOARD_TEXT


def build_default_ui_app() -> UIApp:
    sounds_dir = pathlib.Path(__file__).resolve().parents[1] / "sounds"
    sound_effects = SoundEffects(sounds_dir)
    return UIApp(
        board_parser=TextBoardParser(),
        engine_factory=GameEngine.from_board,
        controller_factory=lambda engine: Controller(engine, sound_effects=sound_effects),
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
