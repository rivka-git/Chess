"""A ControllerLike implementation that talks to a server-hosted GameSession
over WebSocket instead of driving a local GameEngine directly."""

from __future__ import annotations

import threading

from adapter.controller import GameSnapshot
from config import CELL_SIZE_PX
from netcommon.coordinates import pixel_to_rowcol
from netcommon.messages import wire_to_snapshot


def _empty_snapshot() -> GameSnapshot:
    return GameSnapshot(clock=0.0, board=[])


class RemoteController:
    """Satisfies the `ControllerLike` protocol used throughout UI/py."""

    def __init__(self, ws_client) -> None:
        self._ws = ws_client
        self._lock = threading.Lock()
        self._latest_snapshot: GameSnapshot = _empty_snapshot()
        self.role: str | None = None
        self.room_id: str | None = None
        self._ws.start(self._on_message)

    # --- ControllerLike ---

    def move(self, x: int, y: int) -> None:
        row, col = pixel_to_rowcol(x, y, CELL_SIZE_PX)
        self._ws.send({"type": "move_click", "row": row, "col": col})

    def jump(self, x: int, y: int) -> None:
        row, col = pixel_to_rowcol(x, y, CELL_SIZE_PX)
        self._ws.send({"type": "jump_click", "row": row, "col": col})

    def update(self, dt_ms: float) -> None:
        # The server owns the clock and pushes state on its own tick;
        # there is nothing for the client to send here.
        pass

    def get_snapshot(self) -> GameSnapshot:
        with self._lock:
            return self._latest_snapshot

    # --- wiring ---

    def _on_message(self, message: dict) -> None:
        msg_type = message.get("type")
        if msg_type == "state":
            snapshot = wire_to_snapshot(message["snapshot"])
            with self._lock:
                self._latest_snapshot = snapshot
        elif msg_type == "role_assigned":
            self.role = message.get("role")
            self.room_id = message.get("room_id")
