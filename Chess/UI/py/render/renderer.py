from __future__ import annotations
import copy
from assets.img import Img
from assets.asset_loader import AssetLoader
from animation.animation_manager import AnimationManager
from controls.window import Window


class Renderer:
    def __init__(self, asset_loader: AssetLoader, window: Window, cell_size: int, animation_manager: AnimationManager):
        self._asset_loader = asset_loader
        self._window = window
        self._anim_mgr = animation_manager
        import cv2
        board = asset_loader.board_img
        if board.img.shape[2] == 3:
            board.img = cv2.cvtColor(board.img, cv2.COLOR_BGR2BGRA)
        # Resize board to exact cell_size * 8 so pixel↔cell mapping is exact
        board_px = cell_size * 8
        board.img = cv2.resize(board.img, (board_px, board_px), interpolation=cv2.INTER_AREA)
        # Pre-allocate canvas once
        self._board_base = board.img.copy()
        self._canvas = Img()
        self._canvas.img = self._board_base.copy()

    def render(self, snapshot, dt: float) -> None:
        self._anim_mgr.sync_pieces(snapshot)
        self._anim_mgr.update(dt, snapshot)

        # Reset canvas to board background
        import numpy as np
        np.copyto(self._canvas.img, self._board_base)

        # Draw stationary pieces first, then in-transit ones on top, so an
        # arriving piece is always visible over whatever already sits on
        # its destination square instead of being hidden underneath it.
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

        canvas = self._canvas

        # HUD: clock and game-over
        canvas.put_text(f"t={int(snapshot.clock)}ms", 4, 20, 0.5, color=(255, 255, 255, 255))
        if snapshot.game_over:
            h, w = canvas.img.shape[:2]
            canvas.put_text("GAME OVER", w // 4, h // 2, 2.0, color=(0, 0, 255, 255), thickness=3)

        self._window.show(canvas)
