from __future__ import annotations
from assets.img import Img
from assets.asset_loader import AssetLoader
from animation.animation_manager import AnimationManager
from controls.window import Window


class Renderer:
    def __init__(self, asset_loader: AssetLoader, window: Window, cell_size: int, animation_manager: AnimationManager):
        self._asset_loader = asset_loader
        self._window = window
        self._anim_mgr = animation_manager
        self._cell_size = cell_size
        import cv2
        board = asset_loader.board_img
        if board.img.shape[2] == 3:
            board.img = cv2.cvtColor(board.img, cv2.COLOR_BGR2BGRA)
        # Keep board pixel dimensions aligned to the logical 8x8 grid.
        board_px = cell_size * 8
        board.img = cv2.resize(board.img, (board_px, board_px), interpolation=cv2.INTER_AREA)
        # Reuse a pre-allocated canvas to avoid per-frame allocations.
        self._board_base = board.img.copy()
        self._canvas = Img()
        self._canvas.img = self._board_base.copy()

    def render(self, snapshot, dt: float) -> None:
        self._sync_animation(snapshot, dt)
        self._reset_canvas()
        self._draw_pieces()
        self._draw_move_hints(snapshot)
        self._draw_hud(snapshot)
        self._present()

    def _sync_animation(self, snapshot, dt: float) -> None:
        self._anim_mgr.sync_pieces(snapshot)
        self._anim_mgr.update(dt, snapshot)

    def _reset_canvas(self) -> None:
        import numpy as np

        np.copyto(self._canvas.img, self._board_base)

    def _draw_pieces(self) -> None:
        # Draw moving/jumping pieces last so they stay visible over destination occupants.
        in_transit = {"move", "jump"}
        pieces_in_z_order = sorted(
            self._anim_mgr.pieces, key=lambda pv: pv.state_name in in_transit
        )
        for pv in pieces_in_z_order:
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
                # Chess-style hint for empty destination: centered dot.
                radius = max(8, self._cell_size // 7)
                cv2.circle(self._canvas.img, (cx, cy), radius, (70, 70, 70, 255), -1)
            else:
                # Chess-style hint for capture destination: target ring.
                radius = max(12, self._cell_size // 2 - 8)
                cv2.circle(self._canvas.img, (cx, cy), radius, (30, 30, 200, 255), 4)

    def _present(self) -> None:
        self._window.show(self._canvas)
