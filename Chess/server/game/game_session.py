"""A single active game: seats players, delegates clicks and ticking."""

from __future__ import annotations

import pathlib
import sys

_CHESS_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_CHESS_ROOT) not in sys.path:
    sys.path.insert(0, str(_CHESS_ROOT))

from engine.controller import Controller  # noqa: E402
from engine.game_engine import GameEngine  # noqa: E402
from ioutils.board_parser import TextBoardParser  # noqa: E402
from netcommon.defaults import DEFAULT_BOARD_TEXT  # noqa: E402
from server.bus import events  # noqa: E402
from server.bus.event_bus import EventBus  # noqa: E402
from server.game.click_handler import ClickHandler  # noqa: E402
from server.game.tick_loop import TickLoop  # noqa: E402


class GameSession:
    """A single active game: one board + up to two seated players."""

    def __init__(self, session_id: str, event_bus: EventBus, board_text: str | None = None) -> None:
        self.session_id = session_id
        self.started = False
        board = TextBoardParser().parse(board_text or DEFAULT_BOARD_TEXT)
        self._controller = Controller(GameEngine.from_board(board))
        self._connections: dict[str, object] = {}
        self._click_handler = ClickHandler(session_id, self._controller, event_bus)
        self._tick_loop = TickLoop(session_id, self._controller, self._connections, event_bus)
        self._event_bus = event_bus

    # --- seating ---

    def seat_next(self, connection) -> str | None:
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
        self._click_handler.handle_move(color, row, col)

    def handle_jump_click(self, color: str, row: int, col: int) -> None:
        self._click_handler.handle_jump(color, row, col)

    # --- lifecycle ---

    def start(self) -> None:
        self.started = True
        self._event_bus.publish(events.GAME_STARTED, {
            "room_id": self.session_id,
            "white": getattr(self._connections.get("w"), "username", None),
            "black": getattr(self._connections.get("b"), "username", None),
        })
        self._tick_loop.start()
