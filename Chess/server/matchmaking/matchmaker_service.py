"""Matches waiting players by rating range; a background sweep times out
anyone who waited too long without an opponent."""

from __future__ import annotations

import uuid

from server.bus import events
from server.bus.event_bus import EventBus
from server.game.seating import seat_and_notify
from server.game.session_manager import SessionManager
from server.matchmaking.matchmaking_queue import MatchmakingQueue


class MatchmakerService:
    def __init__(self, queue: MatchmakingQueue, session_manager: SessionManager, event_bus: EventBus) -> None:
        self._queue = queue
        self._sessions = session_manager
        self._event_bus = event_bus

    async def handle_find_match(self, connection):
        """Returns the new session when a match is made, or None if the player
        was placed in the queue to wait."""
        rating = connection.player.rating
        opponent = self._queue.find_match(rating)
        if opponent is None:
            self._queue.add(connection.username, rating, connection)
            await connection.send_json({"type": "searching_match"})
            return None
        self._queue.remove(opponent.username)
        session = self._sessions.get_or_create(uuid.uuid4().hex[:8])
        # seat_and_notify assigns white to the first seated (the waiting
        # opponent) and black to the second (the player who just searched).
        await seat_and_notify(session, opponent.connection)
        await seat_and_notify(session, connection)
        self._event_bus.publish(events.MATCH_FOUND, {
            "room_id": session.session_id,
            "white": opponent.username,
            "black": connection.username,
        })
        return session

    def forget(self, username: str) -> None:
        """Removes a queued player, e.g. on disconnect while still waiting."""
        self._queue.remove(username)

    async def sweep_expired(self) -> None:
        for entry in self._queue.expired():
            self._queue.remove(entry.username)
            await entry.connection.send_json({
                "type": "no_match_found", "message": "No opponent found within 1 minute.",
            })
