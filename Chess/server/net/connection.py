"""Wraps a single WebSocket connection with application-level identity."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from server.persistence.player_repository import Player


class ClientConnection:
    """One connected client: its socket plus whatever the app layer knows
    about who they are and what they're doing (color/room/auth)."""

    def __init__(self, websocket) -> None:
        self.websocket = websocket
        self.player: "Player | None" = None
        self.color: str | None = None
        self.room_id: str | None = None
        self.is_spectator: bool = False

    @property
    def username(self) -> str | None:
        return None if self.player is None else self.player.username

    @property
    def is_authenticated(self) -> bool:
        return self.player is not None

    async def send_json(self, message: dict[str, Any]) -> None:
        await self.websocket.send(json.dumps(message))
