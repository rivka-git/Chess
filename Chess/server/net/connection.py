"""Wraps a single WebSocket connection with application-level identity."""

# 🇮🇱 הסבר: קובץ זה מגדיר את המחלקה ClientConnection.
# כל שחקן שמתחבר לשרת מקבל אובייקט ClientConnection משלו.
# האובייקט הזה עוטף את חיבור ה-WebSocket הגולמי ומוסיף לו "זהות" —
# מי הוא השחקן הזה? איזה צבע הוא משחק? באיזה חדר הוא נמצא?

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from server.persistence.player_repository import Player


class ClientConnection:
    """One connected client: its socket plus whatever the app layer knows
    about who they are and what they're doing (color/room/auth)."""

    def __init__(self, websocket) -> None:
        self.websocket = websocket          # חיבור ה-WebSocket הגולמי עצמו
        self.player: "Player | None" = None  # השחקן המחובר, נקבע לאחר login מוצלח
        self.color: str | None = None       # "w" = לבן, "b" = שחור, None = לא שובץ עדיין
        self.room_id: str | None = None     # מזהה החדר/המשחק שהשחקן נמצא בו
        self.is_spectator: bool = False     # האם הוא צופה בלבד (לא מותר לו לזוז)

    @property
    def username(self) -> str | None:
        return None if self.player is None else self.player.username

    @property
    def is_authenticated(self) -> bool:
        return self.player is not None

    async def send_json(self, message: dict[str, Any]) -> None:
        # 🇮🇱 שולח הודעת JSON ללקוח — ממיר מילון פייתון למחרוזת JSON ושולח דרך ה-WebSocket
        await self.websocket.send(json.dumps(message))
