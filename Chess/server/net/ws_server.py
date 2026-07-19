"""asyncio websockets server: accepts connections and drives each one
through the Dispatcher until it closes."""

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


def build_dispatcher() -> Dispatcher:
    event_bus = EventBus()
    MoveLogSubscriber(event_bus)
    session_manager = SessionManager(event_bus)
    return Dispatcher(session_manager)


async def run_server(host: str = HOST, port: int = PORT) -> None:
    dispatcher = build_dispatcher()

    async def handler(websocket):
        await handle_connection(websocket, dispatcher)

    async with websockets.serve(handler, host, port):
        logger.info("Server listening on %s:%s", host, port)
        await asyncio.Future()  # run forever
