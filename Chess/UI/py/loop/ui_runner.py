from __future__ import annotations
import time
from controls.window import Window
from render.renderer import Renderer


class UIRunner:
    def __init__(self, controller, window: Window, renderer: Renderer, target_fps: int = 60):
        self._controller = controller
        self._window = window
        self._renderer = renderer
        self._frame_duration = 1.0 / target_fps

    def start_loop(self) -> None:
        last = time.perf_counter()
        while True:
            now = time.perf_counter()
            dt = now - last
            last = now

            self._controller.update(dt * 1000.0)
            snapshot = self._controller.get_snapshot()
            self._renderer.render(snapshot, dt)

            # Use waitKey as both the event pump and the frame pacer
            elapsed = time.perf_counter() - now
            wait_ms = max(1, int((self._frame_duration - elapsed) * 1000))
            if not self._window.poll_events(wait_ms):
                break

        self._window.destroy()
