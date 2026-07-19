"""Maps session/room ids to active GameSession instances."""

from __future__ import annotations

from server.bus.event_bus import EventBus
from server.game.game_session import GameSession


class SessionManager:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._sessions: dict[str, GameSession] = {}

    def get(self, session_id: str) -> GameSession | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str, board_text: str | None = None) -> GameSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = GameSession(session_id, self._event_bus, board_text=board_text)
        return self._sessions[session_id]

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
