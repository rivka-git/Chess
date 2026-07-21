"""Room creation/joining by explicit id -- the alternative to matchmaking's
automatic pairing."""

from __future__ import annotations

import uuid

from server.game.session_manager import SessionManager
from server.rooms.exceptions import RoomNotFoundError


class RoomService:
    def __init__(self, session_manager: SessionManager) -> None:
        self._sessions = session_manager

    def create_room(self) -> str:
        room_id = uuid.uuid4().hex[:8]
        self._sessions.get_or_create(room_id)
        return room_id

    def get_room(self, room_id: str):
        session = self._sessions.get(room_id)
        if session is None:
            raise RoomNotFoundError(f"No room with id {room_id!r}")
        return session
