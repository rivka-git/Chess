"""Sends the current per-viewer game state to every connection in a room."""

from __future__ import annotations

import logging

from netcommon.messages import snapshot_to_wire

logger = logging.getLogger("ws_gateway.broadcast")


async def broadcast_state(connections: dict, snapshot_for, spectators: list | None = None) -> None:
    for color, connection in list(connections.items()):
        snapshot = snapshot_for(color)
        try:
            await connection.send_json({"type": "state", "snapshot": snapshot_to_wire(snapshot)})
        except Exception:
            logger.exception("Failed to broadcast state to %s", color)
    for connection in list(spectators or []):
        try:
            await connection.send_json({"type": "state", "snapshot": snapshot_to_wire(snapshot_for(None))})
        except Exception:
            logger.exception("Failed to broadcast state to spectator")
