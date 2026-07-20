"""Translates incoming player clicks into controller calls and bus events."""

from __future__ import annotations

import pathlib
import sys

_CHESS_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_CHESS_ROOT) not in sys.path:
    sys.path.insert(0, str(_CHESS_ROOT))

from config import CELL_SIZE_PX  # noqa: E402
from server.bus import events  # noqa: E402
from server.bus.event_bus import EventBus  # noqa: E402


class ClickHandler:
    """Processes move/jump clicks from a single player and publishes MOVE_MADE."""

    def __init__(self, session_id: str, controller, event_bus: EventBus) -> None:
        self._session_id = session_id
        self._controller = controller
        self._event_bus = event_bus

    def handle_move(self, color: str, row: int, col: int) -> None:
        snapshot_before = self._controller.get_snapshot(viewer_color=color)
        self._controller.move_rowcol(row, col, CELL_SIZE_PX, color=color)
        self._publish_if_queued(color, snapshot_before)

    def handle_jump(self, color: str, row: int, col: int) -> None:
        self._controller.jump_rowcol(row, col, CELL_SIZE_PX, color=color)

    def _publish_if_queued(self, color: str, snapshot_before) -> None:
        snapshot_after = self._controller.get_snapshot(viewer_color=color)
        if len(snapshot_after.pending_moves) > len(snapshot_before.pending_moves):
            new_move = snapshot_after.pending_moves[-1]
            self._event_bus.publish(events.MOVE_MADE, {
                "room_id": self._session_id,
                "start": new_move.start,
                "end": new_move.end,
                "color": color,
            })
