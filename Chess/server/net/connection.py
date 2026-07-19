"""Wraps a single WebSocket connection with application-level identity."""

from __future__ import annotations

import json
from typing import Any


class ClientConnection:
    """One connected client: its socket plus whatever the app layer knows
    about who they are and what they're doing (color/role/room)."""

    def __init__(self, websocket) -> None:
        self.websocket = websocket
        self.username: str | None = None
        self.color: str | None = None  # "w" | "b" | None (unassigned/spectator)
        self.room_id: str | None = None
        self.is_spectator: bool = False

    async def send_json(self, message: dict[str, Any]) -> None:
        await self.websocket.send(json.dumps(message))
