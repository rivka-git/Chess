from __future__ import annotations
import cv2
from controls.window import Window


class MouseHandler:
    def __init__(self, window: Window, controller):
        self._controller = controller
        window.set_mouse_callback(self._on_mouse)

    def _on_mouse(self, event: int, x: int, y: int, flags: int, param) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            self._controller.move(x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._controller.jump(x, y)
