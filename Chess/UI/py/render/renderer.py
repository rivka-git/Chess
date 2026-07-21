from __future__ import annotations
from assets.img import Img
from assets.asset_loader import AssetLoader
from controls.window import Window


class Renderer:
    def __init__(self, asset_loader: AssetLoader, window: Window, cell_size: int, overlay_provider=None):
        self._asset_loader = asset_loader
        self._window = window
        self._cell_size = cell_size
        # Optional callable returning a HudOverlay each frame (room id +
        # disconnect countdown). None in the local single-player build.
        self._overlay_provider = overlay_provider
        import cv2
        board = asset_loader.board_img
        if board.img.shape[2] == 3:
            board.img = cv2.cvtColor(board.img, cv2.COLOR_BGR2BGRA)
        board_px = cell_size * 8
        board.img = cv2.resize(board.img, (board_px, board_px), interpolation=cv2.INTER_AREA)
        self._board_base = board.img.copy()
        self._canvas = Img()
        self._canvas.img = self._board_base.copy()

    def render(self, snapshot, pieces: list) -> None:
        self._reset_canvas()
        self._draw_pieces(pieces)
        self._draw_move_hints(snapshot)
        self._draw_hud(snapshot)
        self._draw_overlay(snapshot)
        self._present()

    def _reset_canvas(self) -> None:
        import numpy as np
        np.copyto(self._canvas.img, self._board_base)

    def _draw_pieces(self, pieces: list) -> None:
        in_transit = {"move", "jump"}
        for pv in sorted(pieces, key=lambda pv: pv.state_name in in_transit):
            sprite = pv.get_sprite()
            try:
                sprite.draw_on(self._canvas, pv.px, pv.py)
            except ValueError:
                pass

    def _draw_hud(self, snapshot) -> None:
        canvas = self._canvas
        canvas.put_text(f"t={int(snapshot.clock)}ms", 4, 20, 0.5, color=(255, 255, 255, 255))
        if snapshot.game_over:
            h, w = canvas.img.shape[:2]
            canvas.put_text("GAME OVER", w // 4, h // 2, 2.0, color=(0, 0, 255, 255), thickness=3)

    def _draw_overlay(self, snapshot) -> None:
        if self._overlay_provider is None:
            return
        overlay = self._overlay_provider()
        if overlay is None:
            return
        canvas = self._canvas
        width = canvas.img.shape[1]
        if overlay.room_id:
            text = f"Room: {overlay.room_id}"
            x = max(4, width // 2 - len(text) * 9)
            canvas.put_text(text, x, 30, 0.7, color=(0, 220, 220, 255), thickness=2)
        if overlay.countdown_seconds is not None and not snapshot.game_over:
            text = f"Opponent left! Auto-resign in {overlay.countdown_seconds}s"
            x = max(4, width // 2 - len(text) * 7)
            canvas.put_text(text, x, 60, 0.8, color=(0, 0, 255, 255), thickness=2)

    def _draw_move_hints(self, snapshot) -> None:
        import cv2

        selected = snapshot.selected_position
        if selected is not None:
            row, col = selected
            x1 = col * self._cell_size
            y1 = row * self._cell_size
            x2 = x1 + self._cell_size - 1
            y2 = y1 + self._cell_size - 1
            cv2.rectangle(self._canvas.img, (x1, y1), (x2, y2), (30, 180, 255, 255), 3)

        for row, col in snapshot.legal_targets:
            cx = col * self._cell_size + self._cell_size // 2
            cy = row * self._cell_size + self._cell_size // 2
            if snapshot.board[row][col] is None:
                radius = max(8, self._cell_size // 7)
                cv2.circle(self._canvas.img, (cx, cy), radius, (70, 70, 70, 255), -1)
            else:
                radius = max(12, self._cell_size // 2 - 8)
                cv2.circle(self._canvas.img, (cx, cy), radius, (30, 30, 200, 255), 4)

    def _present(self) -> None:
        self._window.show(self._canvas)
