"""Log subscribers for game and activity events."""

from __future__ import annotations

import logging

from ws_gateway.bus import events
from ws_gateway.bus.event_bus import EventBus

logger = logging.getLogger("ws_gateway.movelog")
activity_logger = logging.getLogger("ws_gateway.activity")


class MoveLogSubscriber:
    def __init__(self, event_bus: EventBus) -> None:
        event_bus.subscribe(events.GAME_STARTED, self._on_game_started)
        event_bus.subscribe(events.MOVE_MADE, self._on_move_made)
        event_bus.subscribe(events.PIECE_CAPTURED, self._on_piece_captured)
        event_bus.subscribe(events.PIECE_PROMOTED, self._on_piece_promoted)
        event_bus.subscribe(events.GAME_ENDED, self._on_game_ended)

    def _on_game_started(self, payload: dict) -> None:
        logger.info("Game started: room=%s white=%s black=%s", payload.get("room_id"), payload.get("white"), payload.get("black"))

    def _on_move_made(self, payload: dict) -> None:
        logger.info("Move: room=%s %s -> %s", payload.get("room_id"), payload.get("start"), payload.get("end"))

    def _on_piece_captured(self, payload: dict) -> None:
        logger.info("Capture: room=%s", payload.get("room_id"))

    def _on_piece_promoted(self, payload: dict) -> None:
        logger.info("Promotion: room=%s", payload.get("room_id"))

    def _on_game_ended(self, payload: dict) -> None:
        logger.info("Game ended: room=%s winner=%s reason=%s", payload.get("room_id"), payload.get("winner"), payload.get("reason"))


class ActivityLogSubscriber:
    def __init__(self, event_bus: EventBus) -> None:
        event_bus.subscribe(events.LOGIN_SUCCEEDED, self._on_login)
        event_bus.subscribe(events.MATCH_FOUND, self._on_match_found)
        event_bus.subscribe(events.ROOM_CREATED, self._on_room_created)
        event_bus.subscribe(events.ROOM_JOINED, self._on_room_joined)
        event_bus.subscribe(events.PLAYER_DISCONNECTED, self._on_player_disconnected)

    def _on_login(self, payload: dict) -> None:
        activity_logger.info("Login: username=%s rating=%s", payload.get("username"), payload.get("rating"))

    def _on_match_found(self, payload: dict) -> None:
        activity_logger.info("Match found: room=%s white=%s black=%s", payload.get("room_id"), payload.get("white"), payload.get("black"))

    def _on_room_created(self, payload: dict) -> None:
        activity_logger.info("Room created: room=%s by=%s", payload.get("room_id"), payload.get("username"))

    def _on_room_joined(self, payload: dict) -> None:
        activity_logger.info("Room joined: room=%s username=%s as=%s", payload.get("room_id"), payload.get("username"), payload.get("role"))

    def _on_player_disconnected(self, payload: dict) -> None:
        activity_logger.info("Player disconnected: room=%s username=%s color=%s", payload.get("room_id"), payload.get("username"), payload.get("color"))
