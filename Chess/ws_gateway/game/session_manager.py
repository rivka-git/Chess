"""Maps session/room ids to active GameSession instances."""

from __future__ import annotations

from ws_gateway.bus import events
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.game.game_session import GameSession


class SessionManager:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._sessions: dict[str, GameSession] = {}
        event_bus.subscribe(events.GAME_ENDED, self._on_game_ended)

    def _on_game_ended(self, payload: dict) -> None:
        self.remove(payload.get("room_id", ""))

    def get(self, session_id: str) -> GameSession | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str, board_text: str | None = None) -> GameSession:
        existing = self._sessions.get(session_id)
        if existing is None or existing.is_over():
            self._sessions[session_id] = GameSession(session_id, self._event_bus, board_text=board_text)
        return self._sessions[session_id]

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
