"""Headless render tests: OpenCV image ops (resize/putText) run without a
display, so we only fake the Window (whose show() calls imshow)."""

import numpy as np

from adapter.controller import GameSnapshot
from assets.img import Img
from render.renderer import Renderer


class FakeWindow:
    def __init__(self):
        self.shown = None

    def show(self, canvas):
        self.shown = canvas


class FakeAssetLoader:
    def __init__(self):
        self.board_img = Img()
        self.board_img.img = np.zeros((40, 40, 3), dtype=np.uint8)


def _snapshot(game_over=False):
    return GameSnapshot(clock=123.0, board=[[None] * 8 for _ in range(8)], game_over=game_over)


def test_local_build_canvas_is_board_only():
    renderer = Renderer(FakeAssetLoader(), FakeWindow(), cell_size=10)
    renderer.render(_snapshot(), pieces=[])
    assert renderer._canvas.img.shape[:2] == (80, 80)  # 8*10, no panel


def test_networked_build_canvas_includes_panel_width():
    logged = ["1. w e2->e4", "2. b e7->e5"]
    window = FakeWindow()
    renderer = Renderer(
        FakeAssetLoader(), window, cell_size=10,
        panel_width=40, move_log_provider=lambda: logged,
    )
    renderer.render(_snapshot(), pieces=[])
    assert renderer._canvas.img.shape[1] == 80 + 40
    assert window.shown is renderer._canvas  # it presented without error


def test_render_with_game_over_and_overlay_does_not_crash():
    from render.hud_overlay import HudOverlay
    renderer = Renderer(
        FakeAssetLoader(), FakeWindow(), cell_size=10,
        overlay_provider=lambda: HudOverlay(room_id="abc123", countdown_seconds=5),
        panel_width=40, move_log_provider=lambda: [],
    )
    renderer.render(_snapshot(game_over=True), pieces=[])  # must not raise
