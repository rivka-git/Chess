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
from server.game.broadcaster import broadcast_state  # noqa: E402
from server.game.click_handler import ClickHandler  # noqa: E402
from server.game.disconnect_timer import DisconnectTimer  # noqa: E402
from server.game.tick_loop import TickLoop  # noqa: E402
from server.server_config import DISCONNECT_TIMEOUT_S  # noqa: E402

_OPPONENT = {"w": "b", "b": "w"}
_COLOR_NAMES = {"w": "white", "b": "black"}


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
        self._resigned_winner: str | None = None
        self._disconnect_timers: dict[str, DisconnectTimer] = {}

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

    def color_of(self, connection) -> str | None:
        for color, conn in self._connections.items():
            if conn is connection:
                return color
        return None

    # --- snapshots ---

    def is_over(self) -> bool:
        return self._resigned_winner is not None or self._controller.get_snapshot().game_over

    def get_viewer_snapshot(self, color: str | None):
        snapshot = self._controller.get_snapshot(viewer_color=color)
        if self._resigned_winner is not None:
            # A resignation ends the game even though both kings remain on the
            # board, so the pure board snapshot wouldn't report it on its own.
            snapshot.game_over = True
        return snapshot

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

    def resign(self, color: str) -> None:
        """Ends the game with the opponent of `color` as the winner. Idempotent
        and shared by the disconnect-timeout path; publishes the same
        GAME_ENDED event as a natural king capture so ratings/history handle
        every ending uniformly."""
        if self.is_over():
            return
        winner = _OPPONENT[color]
        self._resigned_winner = winner
        self._tick_loop.stop()
        self._event_bus.publish(events.GAME_ENDED, {
            "room_id": self.session_id,
            "winner": _COLOR_NAMES[winner],
            "reason": "disconnect_timeout",
            "white": getattr(self._connections.get("w"), "username", None),
            "black": getattr(self._connections.get("b"), "username", None),
        })

    # --- disconnect handling ---

    def on_player_disconnected(self, connection) -> None:
        """Starts the auto-resign countdown for a player who dropped mid-game.
        The connection is kept seated for the countdown (so usernames stay
        resolvable and the opponent can be notified); if the game never
        started or is already over, the seat is simply freed instead."""
        color = self.color_of(connection)
        if color is None:
            return
        if not self.started or self.is_over():
            self.remove_connection(connection)
            return
        self._event_bus.publish(events.PLAYER_DISCONNECTED, {
            "room_id": self.session_id, "color": color,
            "username": getattr(connection, "username", None),
        })
        timer = DisconnectTimer(
            DISCONNECT_TIMEOUT_S,
            on_tick=lambda remaining: self._notify_countdown(_OPPONENT[color], remaining),
            on_timeout=lambda: self._resign_and_broadcast(color),
        )
        self._disconnect_timers[color] = timer
        timer.start()

    async def _notify_countdown(self, opponent_color: str, seconds_remaining: int) -> None:
        opponent = self._connections.get(opponent_color)
        if opponent is None:
            return
        try:
            await opponent.send_json({
                "type": "opponent_left", "seconds_remaining": seconds_remaining,
            })
        except Exception:
            pass

    async def _resign_and_broadcast(self, color: str) -> None:
        self.resign(color)
        await broadcast_state(self._connections, self.get_viewer_snapshot)
