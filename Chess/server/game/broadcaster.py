"""Sends the current per-viewer game state to every connection in a room.
Shared by the tick loop (every tick) and the disconnect flow (one final
push once a resignation is decided)."""

from __future__ import annotations

import logging

from netcommon.messages import snapshot_to_wire

logger = logging.getLogger("server.broadcast")


async def broadcast_state(connections: dict, snapshot_for) -> None:
    for color, connection in list(connections.items()):
        snapshot = snapshot_for(color)
        try:
            await connection.send_json({"type": "state", "snapshot": snapshot_to_wire(snapshot)})
        except Exception:
            logger.exception("Failed to broadcast state to %s", color)
