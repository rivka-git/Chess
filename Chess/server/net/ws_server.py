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

from server.auth.auth_service import AuthService
from server.auth.password_hasher import PasswordHasher
from server.bus.event_bus import EventBus
from server.bus.subscribers import ActivityLogSubscriber, MoveLogSubscriber
from server.game.session_manager import SessionManager
from server.matchmaking.matchmaker_service import MatchmakerService
from server.matchmaking.matchmaking_queue import MatchmakingQueue
from server.net.connection import ClientConnection
from server.net.dispatch import Dispatcher
from server.persistence.db import connect
from server.persistence.game_history_recorder import GameHistoryRecorder
from server.persistence.game_repository import GameRepository
from server.persistence.move_repository import MoveRepository
from server.persistence.player_repository import PlayerRepository
from server.rating.rating_service import RatingService
from server.rooms.room_service import RoomService
from server.server_config import DB_PATH, HOST, PORT

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


def build_dispatcher(db_path: str = DB_PATH) -> tuple[Dispatcher, MatchmakerService]:
    # 🇮🇱 בונה את כל המערכת: EventBus → SessionManager, DB → AuthService/Rating/History → Dispatcher
    # EventBus = מערכת הודעות פנימית בין חלקי השרת
    # SessionManager = מנהל את כל המשחקים הפעילים
    # AuthService = login/הרשמה אוטומטית, מגובה ב-SQLite
    # MatchmakerService/RoomService = שיבוץ לחדר (Play אוטומטי / Room לפי מזהה)
    # Dispatcher = "שוטר תנועה" שמנתב הודעות לשירות/לסשן הנכון
    event_bus = EventBus()
    MoveLogSubscriber(event_bus)  # רושם subscriber שמדפיס לוג למהלכי המשחק
    ActivityLogSubscriber(event_bus)  # רושם subscriber שמתעד login/matchmaking/rooms/ניתוקים
    session_manager = SessionManager(event_bus)
    db_conn = connect(db_path)
    player_repository = PlayerRepository(db_conn)
    auth_service = AuthService(player_repository, PasswordHasher())
    RatingService(player_repository, event_bus)  # מעדכן ELO אוטומטית בסיום כל משחק
    GameHistoryRecorder(GameRepository(db_conn), MoveRepository(db_conn), event_bus)  # שומר היסטוריית משחקים/מהלכים
    matchmaker = MatchmakerService(MatchmakingQueue(), session_manager, event_bus)
    room_service = RoomService(session_manager)
    dispatcher = Dispatcher(session_manager, auth_service, matchmaker, room_service, event_bus)
    return dispatcher, matchmaker


async def _matchmaking_sweep_loop(matchmaker: MatchmakerService) -> None:
    # 🇮🇱 כל שנייה בודק אם מישהו חיכה יותר מדי זמן ל-Play ושולח לו no_match_found
    while True:
        await asyncio.sleep(1)
        await matchmaker.sweep_expired()


async def run_server(host: str = HOST, port: int = PORT) -> None:
    # 🇮🇱 הפונקציה הראשית של השרת — מאזינה לחיבורים ורצה לנצח (עד שמכבים אותה)
    dispatcher, matchmaker = build_dispatcher()
    asyncio.create_task(_matchmaking_sweep_loop(matchmaker))

    async def handler(websocket):
        await handle_connection(websocket, dispatcher)

    async with websockets.serve(handler, host, port):
        logger.info("Server listening on %s:%s", host, port)
        await asyncio.Future()  # run forever — ממתין לנצח (עד Ctrl+C)
