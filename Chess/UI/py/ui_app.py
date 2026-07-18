"""Entry point for the Kung-Fu Chess GUI application."""
from __future__ import annotations
import sys
import pathlib

# Allow imports from Chess root and UI/py
_ROOT = pathlib.Path(__file__).parent.parent.parent   # Chess/
_UI_PY = pathlib.Path(__file__).parent                # UI/py/
for p in (_ROOT, _UI_PY):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from assets.asset_loader import AssetLoader
from adapter.controller import Controller
from controls.window import Window
from controls.mouse_handler import MouseHandler
from render.renderer import Renderer
from loop.ui_runner import UIRunner
from animation.animation_manager import AnimationManager
from geometry.board_geometry import BoardGeometry
from engine.game_engine import GameEngine
from ioutils.board_parser import TextBoardParser
from config import CELL_SIZE_PX

DEFAULT_BOARD = """Board:
bR bN bB bQ bK bB bN bR
bP bP bP bP bP bP bP bP
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
wP wP wP wP wP wP wP wP
wR wN wB wQ wK wB wN wR
"""


class UIApp:
    def run(self, board_text: str = DEFAULT_BOARD) -> None:
        board = TextBoardParser().parse(board_text)
        engine = GameEngine.from_board(board)
        controller = Controller(engine)

        loader = AssetLoader()
        loader.load_all(CELL_SIZE_PX)

        geometry = BoardGeometry(CELL_SIZE_PX)
        animation_manager = AnimationManager(loader, geometry)

        window = Window()
        MouseHandler(window, controller)
        renderer = Renderer(loader, window, CELL_SIZE_PX, animation_manager)
        runner = UIRunner(controller, window, renderer)
        runner.start_loop()


if __name__ == "__main__":
    UIApp().run()
