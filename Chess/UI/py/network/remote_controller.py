"""A ControllerLike implementation that talks to a server-hosted GameSession
over WebSocket instead of driving a local GameEngine directly."""

from __future__ import annotations

import logging
import threading

from adapter.controller import GameSnapshot
from config import CELL_SIZE_PX
from netcommon.coordinates import pixel_to_rowcol
from netcommon.messages import wire_to_snapshot
from network.move_log import MoveLog

logger = logging.getLogger("client.remote")


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
        self.opponent_left_seconds: int | None = None
        self.move_log = MoveLog()
        self._sound_detector = None
        self._ws.set_message_handler(self._on_message)

    # --- ControllerLike ---

    def move(self, x: int, y: int) -> None:
        row, col = pixel_to_rowcol(x, y, CELL_SIZE_PX)
        if not self._is_on_board(row, col):
            return  # click landed on the side panel, not the board
        self._ws.send({"type": "move_click", "row": row, "col": col})

    def jump(self, x: int, y: int) -> None:
        row, col = pixel_to_rowcol(x, y, CELL_SIZE_PX)
        if not self._is_on_board(row, col):
            return
        self._ws.send({"type": "jump_click", "row": row, "col": col})

    def _is_on_board(self, row: int, col: int) -> bool:
        with self._lock:
            board = self._latest_snapshot.board
        if not board:
            return True  # board not known yet -- don't drop the click
        return 0 <= row < len(board) and 0 <= col < len(board[0])

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
                prev = self._latest_snapshot
                self._latest_snapshot = snapshot
            self.move_log.observe(prev, snapshot)
            if self._sound_detector is not None:
                self._sound_detector.on_new_snapshot(prev, snapshot)
        elif msg_type == "role_assigned":
            self.role = message.get("role")
            self.room_id = message.get("room_id")
        elif msg_type == "opponent_left":
            self.opponent_left_seconds = message.get("seconds_remaining")
            logger.info("Opponent disconnected -- auto-resign in %ss", self.opponent_left_seconds)
