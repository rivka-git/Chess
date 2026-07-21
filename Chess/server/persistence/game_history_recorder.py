"""Subscribes to the game lifecycle events and persists them as game/move
history rows. A separate concern from MoveLogSubscriber (which only prints
human-readable log lines): this one is the single place responsible for
writing history to SQLite. A player's own move history is not stored
separately -- it's just MoveRepository.get_moves_for_player(username), a
query over these same rows."""

from __future__ import annotations

import datetime

from server.bus import events
from server.bus.event_bus import EventBus
from server.persistence.game_repository import GameRepository
from server.persistence.move_repository import MoveRepository


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class GameHistoryRecorder:
    def __init__(
        self, game_repository: GameRepository, move_repository: MoveRepository, event_bus: EventBus
    ) -> None:
        self._games = game_repository
        self._moves = move_repository
        self._game_ids: dict[str, int] = {}
        self._move_seq: dict[str, int] = {}
        event_bus.subscribe(events.GAME_STARTED, self._on_game_started)
        event_bus.subscribe(events.MOVE_MADE, self._on_move_made)
        event_bus.subscribe(events.GAME_ENDED, self._on_game_ended)

    def _on_game_started(self, payload: dict) -> None:
        room_id, white, black = payload.get("room_id"), payload.get("white"), payload.get("black")
        if not room_id or not white or not black:
            return
        self._game_ids[room_id] = self._games.create_game(room_id, white, black, _now())
        self._move_seq[room_id] = 0

    def _on_move_made(self, payload: dict) -> None:
        room_id = payload.get("room_id")
        game_id = self._game_ids.get(room_id)
        if game_id is None:
            return
        seq = self._move_seq[room_id] + 1
        self._move_seq[room_id] = seq
        self._moves.add_move(
            game_id,
            seq,
            payload["color"],
            tuple(payload["start"]),
            tuple(payload["end"]),
            payload.get("clock_tick", 0.0),
        )

    def _on_game_ended(self, payload: dict) -> None:
        room_id = payload.get("room_id")
        game_id = self._game_ids.pop(room_id, None)
        self._move_seq.pop(room_id, None)
        if game_id is None:
            return
        self._games.finish_game(game_id, payload.get("winner"), payload.get("reason", ""), _now())
