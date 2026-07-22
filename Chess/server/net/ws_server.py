"""asyncio websockets server: accepts connections and drives each one
through the Dispatcher until it closes."""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3

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
    connection = ClientConnection(websocket)
    await dispatcher.on_connect(connection)
    try:
        async for raw_message in websocket:
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await connection.send_json({
                    "type": "error", "code": "bad_json", "message": "Malformed JSON.",
                })
                continue
            try:
                await dispatcher.on_message(connection, message)
            except Exception:
                logger.exception("Error handling message %r", message)
                await connection.send_json({
                    "type": "error", "code": "server_error", "message": "Internal error.",
                })
    except ConnectionClosed:
        pass
    finally:
        await dispatcher.on_disconnect(connection)


def build_dispatcher(db_path: str = DB_PATH) -> tuple[Dispatcher, MatchmakerService, sqlite3.Connection]:
    event_bus = EventBus()
    MoveLogSubscriber(event_bus)
    ActivityLogSubscriber(event_bus)
    session_manager = SessionManager(event_bus)
    db_conn = connect(db_path)
    player_repository = PlayerRepository(db_conn)
    game_repository = GameRepository(db_conn)
    auth_service = AuthService(player_repository, PasswordHasher())
    RatingService(player_repository, event_bus)
    GameHistoryRecorder(game_repository, MoveRepository(db_conn), event_bus)
    matchmaker = MatchmakerService(MatchmakingQueue(), session_manager, event_bus)
    room_service = RoomService(session_manager)
    dispatcher = Dispatcher(session_manager, auth_service, matchmaker, room_service, event_bus, game_repository)
    return dispatcher, matchmaker, db_conn


async def _matchmaking_sweep_loop(matchmaker: MatchmakerService) -> None:
    while True:
        await asyncio.sleep(1)
        await matchmaker.sweep_expired()


async def run_server(host: str = HOST, port: int = PORT) -> None:
    dispatcher, matchmaker, db_conn = build_dispatcher()
    asyncio.create_task(_matchmaking_sweep_loop(matchmaker))

    async def handler(websocket):
        await handle_connection(websocket, dispatcher)

    try:
        async with websockets.serve(handler, host, port):
            logger.info("Server listening on %s:%s", host, port)
            await asyncio.Future()  # run forever
    finally:
        db_conn.close()
