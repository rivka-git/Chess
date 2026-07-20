"""asyncio websockets server: accepts connections and drives each one
through the Dispatcher until it closes."""

# 🇮🇱 הסבר: זהו קובץ השרת הראשי ברמת הרשת.
# התפקיד שלו:
#   1. לחכות לחיבורים נכנסים מלקוחות (שחקנים)
#   2. לקבל כל הודעת JSON מלקוח ולהעביר אותה ל-Dispatcher לטיפול
#   3. לטפל בניתוקים בצורה נקייה

from __future__ import annotations

import asyncio
import json
import logging

import websockets
from websockets.exceptions import ConnectionClosed

from server.bus.event_bus import EventBus
from server.bus.subscribers import MoveLogSubscriber
from server.game.session_manager import SessionManager
from server.net.connection import ClientConnection
from server.net.dispatch import Dispatcher
from server.server_config import HOST, PORT

logger = logging.getLogger("server.ws")


async def handle_connection(websocket, dispatcher: Dispatcher) -> None:
    # 🇮🇱 פונקציה זו מטפלת בחיבור של לקוח אחד מתחילתו ועד סופו
    connection = ClientConnection(websocket)  # עוטף את ה-websocket באובייקט עם זהות (צבע, חדר)
    await dispatcher.on_connect(connection)   # מודיע ל-Dispatcher שחיבור חדש נכנס
    try:
        async for raw_message in websocket:   # לולאה: ממתין לכל הודעה מהלקוח
            try:
                message = json.loads(raw_message)  # ממיר JSON גולמי למילון פייתון
            except json.JSONDecodeError:
                # אם הלקוח שלח JSON שבור — מחזיר שגיאה ללקוח ממשיך לחכות להודעה הבאה
                await connection.send_json({
                    "type": "error", "code": "bad_json", "message": "Malformed JSON.",
                })
                continue
            try:
                await dispatcher.on_message(connection, message)  # מעביר את ההודעה לטיפול
            except Exception:
                logger.exception("Error handling message %r", message)
                await connection.send_json({
                    "type": "error", "code": "server_error", "message": "Internal error.",
                })
    except ConnectionClosed:
        # 🇮🇱 הלקוח סגר את החיבור — זה תקין, פשוט יוצאים מהלולאה
        pass
    finally:
        # 🇮🇱 תמיד מנקים — מודיעים ל-Dispatcher שהלקוח התנתק (כדי לפנות את מושבו)
        await dispatcher.on_disconnect(connection)


def build_dispatcher() -> Dispatcher:
    # 🇮🇱 בונה את כל המערכת: EventBus → SessionManager → Dispatcher
    # EventBus = מערכת הודעות פנימית בין חלקי השרת
    # SessionManager = מנהל את כל המשחקים הפעילים
    # Dispatcher = "שוטר תנועה" שמנתב הודעות לסשן הנכון
    event_bus = EventBus()
    MoveLogSubscriber(event_bus)  # רושם subscriber שמדפיס לוג לכל אירוע
    session_manager = SessionManager(event_bus)
    return Dispatcher(session_manager)


async def run_server(host: str = HOST, port: int = PORT) -> None:
    # 🇮🇱 הפונקציה הראשית של השרת — מאזינה לחיבורים ורצה לנצח (עד שמכבים אותה)
    dispatcher = build_dispatcher()

    async def handler(websocket):
        await handle_connection(websocket, dispatcher)

    async with websockets.serve(handler, host, port):
        logger.info("Server listening on %s:%s", host, port)
        await asyncio.Future()  # run forever — ממתין לנצח (עד Ctrl+C)
