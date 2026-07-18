from __future__ import annotations
import cv2
from assets.img import Img

WINDOW_NAME = "Kung-Fu Chess"


class Window:
    def __init__(self):
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_AUTOSIZE, cv2.WINDOW_AUTOSIZE)
        self._closed = False

    def set_mouse_callback(self, callback) -> None:
        cv2.setMouseCallback(WINDOW_NAME, callback)

    def poll_events(self, wait_ms: int = 0) -> bool:
        """Return False if the window was closed. wait_ms is passed to waitKey."""
        key = cv2.waitKey(wait_ms) & 0xFF
        if key == 27:  # ESC
            self._closed = True
        if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
            self._closed = True
        return not self._closed

    def show(self, canvas: Img) -> None:
        cv2.imshow(WINDOW_NAME, canvas.img)

    def destroy(self) -> None:
        cv2.destroyAllWindows()
