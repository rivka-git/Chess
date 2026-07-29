"""Reacts to GAME_ENDED by updating both players' ratings via ELO (async DB)."""

from __future__ import annotations

import asyncio
import logging

from ws_gateway.bus import events
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.persistence.player_repository import PlayerRepository
from ws_gateway.rating.elo import calculate_new_ratings

logger = logging.getLogger("ws_gateway.rating")

_WINNER_TO_RESULT = {"white": "white", "black": "black", None: "draw"}


class RatingService:
    def __init__(self, player_repository: PlayerRepository, event_bus: EventBus) -> None:
        self._players = player_repository
        self._event_bus = event_bus
        event_bus.subscribe(events.GAME_ENDED, self._on_game_ended)

    def _on_game_ended(self, payload: dict) -> None:
        asyncio.create_task(self._update_ratings(payload))

    async def _update_ratings(self, payload: dict) -> None:
        white_username, black_username = payload.get("white"), payload.get("black")
        if not white_username or not black_username:
            return
        try:
            white = await self._players.get_by_username(white_username)
            black = await self._players.get_by_username(black_username)
        except Exception:
            logger.exception("Failed to fetch players for rating update")
            return
        if white is None or black is None:
            logger.warning("Cannot update ratings: unknown player(s) %r/%r", white_username, black_username)
            return
        result = _WINNER_TO_RESULT.get(payload.get("winner"), "draw")
        new_white, new_black = calculate_new_ratings(white.rating, black.rating, result)
        try:
            await self._players.update_rating(white_username, new_white)
            await self._players.update_rating(black_username, new_black)
        except Exception:
            logger.exception("Failed to write updated ratings")
            return
        self._event_bus.publish(events.ELO_UPDATED, {
            "room_id": payload.get("room_id"),
            "white": {"username": white_username, "old_rating": white.rating, "new_rating": new_white},
            "black": {"username": black_username, "old_rating": black.rating, "new_rating": new_black},
        })
