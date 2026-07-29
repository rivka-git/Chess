"""Matches waiting players by rating range.

Works with any queue that implements the async interface:
  add(username, rating, connection) / remove(username) /
  find_match(rating) / expired()
"""

from __future__ import annotations

import uuid

from ws_gateway.bus import events
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.game.seating import seat_and_notify
from ws_gateway.game.session_manager import SessionManager


class MatchmakerService:
    def __init__(self, queue, session_manager: SessionManager, event_bus: EventBus) -> None:
        self._queue = queue
        self._sessions = session_manager
        self._event_bus = event_bus

    async def handle_find_match(self, connection) -> None:
        rating = connection.player.rating
        opponent = await self._queue.find_match(rating)
        if opponent is None:
            await self._queue.add(connection.username, rating, connection)
            await connection.send_json({"type": "searching_match"})
            return
        await self._queue.remove(opponent.username)
        session = self._sessions.get_or_create(uuid.uuid4().hex[:8])
        await seat_and_notify(session, opponent.connection)
        await seat_and_notify(session, connection)
        self._event_bus.publish(events.MATCH_FOUND, {
            "room_id": session.session_id,
            "white": opponent.username,
            "black": connection.username,
        })

    async def forget(self, username: str) -> None:
        await self._queue.remove(username)

    async def sweep_expired(self) -> None:
        for entry in await self._queue.expired():
            await self._queue.remove(entry.username)
            await entry.connection.send_json({"type": "no_match_found", "message": "No opponent found within 1 minute."})
