"""EventBus subscribers: concerns that react to game events without the
game/session code needing to know they exist."""

from __future__ import annotations

import logging

from server.bus import events
from server.bus.event_bus import EventBus

logger = logging.getLogger("server.movelog")


class MoveLogSubscriber:
    """Writes a human-readable log line for each move-lifecycle event."""

    def __init__(self, event_bus: EventBus) -> None:
        event_bus.subscribe(events.GAME_STARTED, self._on_game_started)
        event_bus.subscribe(events.MOVE_MADE, self._on_move_made)
        event_bus.subscribe(events.PIECE_CAPTURED, self._on_piece_captured)
        event_bus.subscribe(events.PIECE_PROMOTED, self._on_piece_promoted)
        event_bus.subscribe(events.GAME_ENDED, self._on_game_ended)

    def _on_game_started(self, payload: dict) -> None:
        logger.info(
            "Game started: room=%s white=%s black=%s",
            payload.get("room_id"), payload.get("white"), payload.get("black"),
        )

    def _on_move_made(self, payload: dict) -> None:
        logger.info(
            "Move: room=%s %s -> %s",
            payload.get("room_id"), payload.get("start"), payload.get("end"),
        )

    def _on_piece_captured(self, payload: dict) -> None:
        logger.info(
            "Capture: room=%s at %s captured=%s",
            payload.get("room_id"), payload.get("position"), payload.get("captured_token"),
        )

    def _on_piece_promoted(self, payload: dict) -> None:
        logger.info(
            "Promotion: room=%s at %s -> %s",
            payload.get("room_id"), payload.get("position"), payload.get("new_token"),
        )

    def _on_game_ended(self, payload: dict) -> None:
        logger.info(
            "Game ended: room=%s winner=%s reason=%s",
            payload.get("room_id"), payload.get("winner"), payload.get("reason"),
        )
