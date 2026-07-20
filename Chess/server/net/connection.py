"""Wraps a single WebSocket connection with application-level identity."""

# 🇮🇱 הסבר: קובץ זה מגדיר את המחלקה ClientConnection.
# כל שחקן שמתחבר לשרת מקבל אובייקט ClientConnection משלו.
# האובייקט הזה עוטף את חיבור ה-WebSocket הגולמי ומוסיף לו "זהות" —
# מי הוא השחקן הזה? איזה צבע הוא משחק? באיזה חדר הוא נמצא?

from __future__ import annotations

import json
from typing import Any


class ClientConnection:
    """One connected client: its socket plus whatever the app layer knows
    about who they are and what they're doing (color/role/room)."""

    def __init__(self, websocket) -> None:
        self.websocket = websocket          # חיבור ה-WebSocket הגולמי עצמו
        self.username: str | None = None    # שם המשתמש (עדיין לא בשימוש — לעתיד)
        self.color: str | None = None       # "w" = לבן, "b" = שחור, None = לא שובץ עדיין
        self.room_id: str | None = None     # מזהה החדר/המשחק שהשחקן נמצא בו
        self.is_spectator: bool = False     # האם הוא צופה בלבד (לא מותר לו לזוז)

    async def send_json(self, message: dict[str, Any]) -> None:
        # 🇮🇱 שולח הודעת JSON ללקוח — ממיר מילון פייתון למחרוזת JSON ושולח דרך ה-WebSocket
        await self.websocket.send(json.dumps(message))
