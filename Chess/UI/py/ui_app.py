"""UI application orchestration with dependency injection."""
from __future__ import annotations

import pathlib
import sys
from typing import Callable, Protocol

# Ensure Chess root and UI/py are importable when running this file directly.
_ROOT = pathlib.Path(__file__).parent.parent.parent
_UI_PY = pathlib.Path(__file__).parent
for _path in (_ROOT, _UI_PY):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from ioutils.board_parser import BoardParser
from model.board import Board


class ControllerLike(Protocol):
    def update(self, dt_ms: float) -> None: ...
    def get_snapshot(self): ...
    def move(self, x: int, y: int) -> None: ...
    def jump(self, x: int, y: int) -> None: ...


class AssetLoaderLike(Protocol):
    def load_all(self, cell_size: int) -> None: ...


class WindowLike(Protocol):
    def set_mouse_callback(self, callback) -> None: ...
    def poll_events(self, wait_ms: int = 0) -> bool: ...
    def show(self, canvas) -> None: ...
    def destroy(self) -> None: ...


class RunnerLike(Protocol):
    def start_loop(self) -> None: ...


class UIApp:
    def __init__(
        self,
        board_parser: BoardParser,
        engine_factory: Callable[[Board], object],
        controller_factory: Callable[[object], ControllerLike],
        asset_loader: AssetLoaderLike,
        geometry: object,
        animation_manager_factory: Callable[[AssetLoaderLike, object], object],
        window: WindowLike,
        mouse_handler_factory: Callable[[WindowLike, ControllerLike], object],
        renderer_factory: Callable[[AssetLoaderLike, WindowLike, int], object],
        runner_factory: Callable[[ControllerLike, WindowLike, object, object], RunnerLike],
        cell_size_px: int,
        default_board_text: str,
    ) -> None:
        self._board_parser = board_parser
        self._engine_factory = engine_factory
        self._controller_factory = controller_factory
        self._asset_loader = asset_loader
        self._geometry = geometry
        self._animation_manager_factory = animation_manager_factory
        self._window = window
        self._mouse_handler_factory = mouse_handler_factory
        self._renderer_factory = renderer_factory
        self._runner_factory = runner_factory
        self._cell_size_px = cell_size_px
        self._default_board_text = default_board_text

    def run(self, board_text: str | None = None) -> None:
        resolved_board_text = board_text if board_text is not None else self._default_board_text
        board = self._board_parser.parse(resolved_board_text)
        engine = self._engine_factory(board)
        controller = self._controller_factory(engine)

        self._asset_loader.load_all(self._cell_size_px)
        animation_manager = self._animation_manager_factory(self._asset_loader, self._geometry)
        self._mouse_handler_factory(self._window, controller)
        renderer = self._renderer_factory(
            self._asset_loader, self._window, self._cell_size_px
        )
        runner = self._runner_factory(controller, self._window, renderer, animation_manager)
        runner.start_loop()

if __name__ == "__main__":
    from ui_bootstrap import build_default_ui_app

    build_default_ui_app().run()
