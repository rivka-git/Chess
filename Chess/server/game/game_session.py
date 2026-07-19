"""Owns one GameEngine/Controller pair per active game and runs the
authoritative server-side tick loop that advances the clock and broadcasts
state -- clients only ever send clicks and receive pushed state."""

from __future__ import annotations

import asyncio
import logging
import pathlib
import sys

_CHESS_ROOT = pathlib.Path(__file__).resolve().parents[2]
_UI_PY = _CHESS_ROOT / "UI" / "py"
for _path in (_CHESS_ROOT, _UI_PY):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from adapter.controller import Controller  # noqa: E402
from config import CELL_SIZE_PX  # noqa: E402
from engine.game_engine import GameEngine  # noqa: E402
from ioutils.board_parser import TextBoardParser  # noqa: E402
from ui_config import DEFAULT_BOARD_TEXT  # noqa: E402

from netcommon.coordinates import rowcol_to_pixel_center  # noqa: E402
from netcommon.messages import snapshot_to_wire  # noqa: E402
from server.bus import events  # noqa: E402
from server.bus.event_bus import EventBus  # noqa: E402
from server.server_config import TICK_MS  # noqa: E402

logger = logging.getLogger("server.session")


class GameSession:
    """A single active game: one board + up to two seated players."""

    def __init__(self, session_id: str, event_bus: EventBus, board_text: str | None = None) -> None:
        self.session_id = session_id
        self.started = False
        self._event_bus = event_bus
        board = TextBoardParser().parse(board_text or DEFAULT_BOARD_TEXT)
        self._controller = Controller(GameEngine.from_board(board))
        self._connections: dict[str, object] = {}
        self._tick_task: asyncio.Task | None = None

    # --- seating ---

    def seat_next(self, connection) -> str | None:
        """Seat a newly connected player. Returns "w"/"b", or None if full."""
        if "w" not in self._connections:
            self._connections["w"] = connection
            return "w"
        if "b" not in self._connections:
            self._connections["b"] = connection
            return "b"
        return None

    def is_full(self) -> bool:
        return "w" in self._connections and "b" in self._connections

    def remove_connection(self, connection) -> None:
        for color, conn in list(self._connections.items()):
            if conn is connection:
                del self._connections[color]

    # --- snapshots ---

    def get_viewer_snapshot(self, color: str | None):
        return self._controller.get_snapshot(viewer_color=color)

    # --- input ---

    def handle_move_click(self, color: str, row: int, col: int) -> None:
        self._dispatch_click(color, row, col, is_jump=False)

    def handle_jump_click(self, color: str, row: int, col: int) -> None:
        self._dispatch_click(color, row, col, is_jump=True)

    def _dispatch_click(self, color: str, row: int, col: int, is_jump: bool) -> None:
        snapshot_before = self._controller.get_snapshot(viewer_color=color)
        x, y = rowcol_to_pixel_center(row, col, CELL_SIZE_PX)
        if is_jump:
            self._controller.jump(x, y, color=color)
        else:
            self._controller.move(x, y, color=color)
            self._publish_move_if_queued(color, snapshot_before)

    def _publish_move_if_queued(self, color: str, snapshot_before) -> None:
        snapshot_after = self._controller.get_snapshot(viewer_color=color)
        if len(snapshot_after.pending_moves) > len(snapshot_before.pending_moves):
            new_move = snapshot_after.pending_moves[-1]
            self._event_bus.publish(events.MOVE_MADE, {
                "room_id": self.session_id,
                "start": new_move.start,
                "end": new_move.end,
                "color": color,
            })

    # --- lifecycle ---

    def start(self) -> None:
        self.started = True
        self._event_bus.publish(events.GAME_STARTED, {
            "room_id": self.session_id,
            "white": getattr(self._connections.get("w"), "username", None),
            "black": getattr(self._connections.get("b"), "username", None),
        })
        self._tick_task = asyncio.create_task(self._tick_loop())

    async def _tick_loop(self) -> None:
        while True:
            await asyncio.sleep(TICK_MS / 1000)
            snapshot_before = self._controller.get_snapshot()
            self._controller.update(TICK_MS)
            snapshot_after = self._controller.get_snapshot()
            self._publish_tick_events(snapshot_before, snapshot_after)
            await self._broadcast()
            if snapshot_after.game_over:
                break

    def _publish_tick_events(self, before, after) -> None:
        if _count_pieces(after) < _count_pieces(before):
            self._event_bus.publish(events.PIECE_CAPTURED, {"room_id": self.session_id})
        if _has_promotion(before, after):
            self._event_bus.publish(events.PIECE_PROMOTED, {"room_id": self.session_id})
        if not before.game_over and after.game_over:
            self._event_bus.publish(events.GAME_ENDED, {
                "room_id": self.session_id,
                "winner": _winner_color(after),
                "reason": "king_captured",
            })

    async def _broadcast(self) -> None:
        for color, connection in list(self._connections.items()):
            snapshot = self.get_viewer_snapshot(color)
            try:
                await connection.send_json({"type": "state", "snapshot": snapshot_to_wire(snapshot)})
            except Exception:
                logger.exception("Failed to broadcast state to %s", color)


def _count_pieces(snapshot) -> int:
    return sum(1 for row in snapshot.board for piece in row if piece is not None)


def _has_promotion(before, after) -> bool:
    for row_b, row_a in zip(before.board, after.board):
        for piece_b, piece_a in zip(row_b, row_a):
            if piece_b is None or piece_a is None:
                continue
            if (
                piece_b.token in {"wP", "bP"}
                and piece_a.token in {"wQ", "bQ"}
                and piece_b.token[0] == piece_a.token[0]
            ):
                return True
    return False


def _winner_color(snapshot) -> str | None:
    tokens = {piece.token for row in snapshot.board for piece in row if piece is not None}
    if "wK" in tokens and "bK" not in tokens:
        return "w"
    if "bK" in tokens and "wK" not in tokens:
        return "b"
    return None
