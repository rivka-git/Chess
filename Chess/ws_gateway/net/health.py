"""Minimal HTTP health-check server that runs alongside the WebSocket server.

Exposes GET /health on HEALTH_PORT (default 8766).
Returns 200 {"status": "ok"} when the process is alive.
Used by Docker's healthcheck directive.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

HEALTH_PORT = int(os.environ.get("HEALTH_PORT", 8766))

logger = logging.getLogger("ws_gateway.health")


async def _handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        await reader.read(1024)  # consume the request
        body = json.dumps({"status": "ok"}).encode()
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            b"Connection: close\r\n"
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"\r\n"
            + body
        )
        writer.write(response)
        await writer.drain()
    finally:
        writer.close()


async def start_health_server() -> None:
    server = await asyncio.start_server(_handle, "0.0.0.0", HEALTH_PORT)
    logger.info("Health check listening on port %s", HEALTH_PORT)
    async with server:
        await server.serve_forever()
