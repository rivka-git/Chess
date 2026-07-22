from __future__ import annotations
import cv2
from controls.window import Window
from netcommon.coordinates import pixel_to_rowcol


class MouseHandler:
    """Owns the screen, so this is where pixels become board cells: everything
    downstream of here speaks (row, col)."""

    def __init__(self, window: Window, controller, cell_size: int):
        self._controller = controller
        self._cell_size = cell_size
        window.set_mouse_callback(self._on_mouse)

    def _on_mouse(self, event: int, x: int, y: int, flags: int, param) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            self._controller.move(*pixel_to_rowcol(x, y, self._cell_size))
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._controller.jump(*pixel_to_rowcol(x, y, self._cell_size))
