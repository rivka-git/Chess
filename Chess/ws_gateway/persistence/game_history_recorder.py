"""Persists game/move history rows from bus events (async DB via asyncio.create_task)."""

from __future__ import annotations

import asyncio
import datetime
import logging

from ws_gateway.bus import events
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.persistence.game_repository import GameRepository
from ws_gateway.persistence.move_repository import MoveRepository

logger = logging.getLogger("ws_gateway.history")


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class GameHistoryRecorder:
    def __init__(self, game_repository: GameRepository, move_repository: MoveRepository, event_bus: EventBus) -> None:
        self._games = game_repository
        self._moves = move_repository
        self._game_ids: dict[str, int] = {}
        self._move_seq: dict[str, int] = {}
        event_bus.subscribe(events.GAME_STARTED, self._on_game_started)
        event_bus.subscribe(events.MOVE_MADE, self._on_move_made)
        event_bus.subscribe(events.GAME_ENDED, self._on_game_ended)

    def _on_game_started(self, payload: dict) -> None:
        asyncio.create_task(self._persist_game_started(payload))

    def _on_move_made(self, payload: dict) -> None:
        asyncio.create_task(self._persist_move(payload))

    def _on_game_ended(self, payload: dict) -> None:
        asyncio.create_task(self._persist_game_ended(payload))

    async def _persist_game_started(self, payload: dict) -> None:
        room_id, white, black = payload.get("room_id"), payload.get("white"), payload.get("black")
        if not room_id or not white or not black:
            return
        try:
            game_id = await self._games.create_game(room_id, white, black, _now())
            self._game_ids[room_id] = game_id
            self._move_seq[room_id] = 0
        except Exception:
            logger.exception("Failed to persist game_started for room %s", room_id)

    async def _persist_move(self, payload: dict) -> None:
        room_id = payload.get("room_id")
        game_id = self._game_ids.get(room_id)
        if game_id is None:
            return
        seq = self._move_seq[room_id] + 1
        self._move_seq[room_id] = seq
        try:
            await self._moves.add_move(
                game_id, seq, payload["color"],
                tuple(payload["start"]), tuple(payload["end"]),
                payload.get("clock_tick", 0.0),
            )
        except Exception:
            logger.exception("Failed to persist move for room %s seq %s", room_id, seq)

    async def _persist_game_ended(self, payload: dict) -> None:
        room_id = payload.get("room_id")
        game_id = self._game_ids.pop(room_id, None)
        self._move_seq.pop(room_id, None)
        if game_id is None:
            return
        try:
            await self._games.finish_game(game_id, payload.get("winner"), payload.get("reason", ""), _now())
        except Exception:
            logger.exception("Failed to persist game_ended for room %s", room_id)
