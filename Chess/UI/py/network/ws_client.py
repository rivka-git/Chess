"""Background-thread asyncio WebSocket client.

`UIRunner`'s loop is a synchronous ~60fps OpenCV loop, so this bridges it to
an async `websockets` connection by running the connection on its own
thread with its own event loop, and handing incoming messages back via a
plain callback (invoked from that background thread -- callers that touch
shared state from it must take their own lock, see RemoteController).
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Callable

import websockets

logger = logging.getLogger("client.ws")


class WsClient:
    def __init__(self, uri: str) -> None:
        self._uri = uri
        self._on_message: Callable[[dict], None] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._websocket = None
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self, on_message: Callable[[dict], None]) -> None:
        self._on_message = on_message
        self._thread.start()
        self._ready.wait(timeout=10)

    def set_message_handler(self, on_message: Callable[[dict], None]) -> None:
        """Swaps the callback for an already-started connection (e.g. handing
        off from the login handshake to the in-game controller)."""
        self._on_message = on_message

    def send(self, message: dict) -> None:
        if self._loop is None or self._websocket is None:
            logger.warning("send() called before connection is ready: %r", message)
            return
        asyncio.run_coroutine_threadsafe(self._websocket.send(json.dumps(message)), self._loop)

    def close(self) -> None:
        if self._loop is not None and self._websocket is not None:
            asyncio.run_coroutine_threadsafe(self._websocket.close(), self._loop)

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_and_listen())

    async def _connect_and_listen(self) -> None:
        async with websockets.connect(self._uri) as websocket:
            self._websocket = websocket
            self._ready.set()
            try:
                async for raw_message in websocket:
                    try:
                        message = json.loads(raw_message)
                    except json.JSONDecodeError:
                        logger.warning("Received malformed JSON from server")
                        continue
                    if self._on_message is not None:
                        self._on_message(message)
            except websockets.exceptions.ConnectionClosed:
                logger.info("Connection to server closed")
