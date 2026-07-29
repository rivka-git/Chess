"""asyncio websockets server for the WebSocket Gateway."""

from __future__ import annotations

import asyncio
import json
import logging

import redis.asyncio as aioredis
import websockets
from websockets.exceptions import ConnectionClosed

from ws_gateway.auth.auth_service import AuthService
from ws_gateway.auth.password_hasher import PasswordHasher
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.config import DATABASE_URL, HOST, PORT, REDIS_URL
from ws_gateway.game.session_manager import SessionManager
from ws_gateway.matchmaking.matchmaker_service import MatchmakerService
from ws_gateway.matchmaking.redis_queue import RedisMatchmakingQueue
from ws_gateway.net.connection import ClientConnection
from ws_gateway.net.dispatch import Dispatcher
from ws_gateway.observability.subscribers import ActivityLogSubscriber, MoveLogSubscriber
from ws_gateway.persistence.db import create_pool
from ws_gateway.persistence.game_history_recorder import GameHistoryRecorder
from ws_gateway.persistence.game_repository import GameRepository
from ws_gateway.persistence.move_repository import MoveRepository
from ws_gateway.persistence.player_repository import PlayerRepository
from ws_gateway.rating.rating_service import RatingService
from ws_gateway.rooms.room_service import RoomService

from ws_gateway.net.health import start_health_server

logger = logging.getLogger("ws_gateway.ws")


async def handle_connection(websocket, dispatcher: Dispatcher) -> None:
    connection = ClientConnection(websocket)
    await dispatcher.on_connect(connection)
    try:
        async for raw_message in websocket:
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await connection.send_json({"type": "error", "code": "bad_json", "message": "Malformed JSON."})
                continue
            try:
                await dispatcher.on_message(connection, message)
            except Exception:
                logger.exception("Error handling message %r", message)
                await connection.send_json({"type": "error", "code": "server_error", "message": "Internal error."})
    except ConnectionClosed:
        pass
    finally:
        await dispatcher.on_disconnect(connection)


async def _matchmaking_sweep_loop(matchmaker: MatchmakerService) -> None:
    while True:
        await asyncio.sleep(1)
        await matchmaker.sweep_expired()


async def run_server(host: str = HOST, port: int = PORT) -> None:
    db_pool = await create_pool()
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)

    event_bus = EventBus()
    MoveLogSubscriber(event_bus)
    ActivityLogSubscriber(event_bus)

    player_repo = PlayerRepository(db_pool)
    game_repo = GameRepository(db_pool)
    move_repo = MoveRepository(db_pool)

    session_manager = SessionManager(event_bus)
    auth_service = AuthService(player_repo, PasswordHasher())
    RatingService(player_repo, event_bus)
    GameHistoryRecorder(game_repo, move_repo, event_bus)

    queue = RedisMatchmakingQueue(redis)
    matchmaker = MatchmakerService(queue, session_manager, event_bus)
    room_service = RoomService(session_manager)
    dispatcher = Dispatcher(session_manager, auth_service, matchmaker, room_service, event_bus)

    asyncio.create_task(_matchmaking_sweep_loop(matchmaker))

    async def handler(websocket):
        await handle_connection(websocket, dispatcher)

    try:
        async with websockets.serve(handler, host, port):
            logger.info("WS Gateway listening on %s:%s", host, port)
            await asyncio.gather(
                asyncio.Future(),       # WebSocket runs forever
                start_health_server(),  # HTTP health check runs alongside
            )
    finally:
        await db_pool.close()
        await redis.aclose()
