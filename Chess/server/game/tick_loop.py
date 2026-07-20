"""Async tick loop: advances the game clock and broadcasts state every TICK_MS."""

from __future__ import annotations

import asyncio
import logging

from netcommon.messages import snapshot_to_wire
from server.bus import events
from server.bus.event_bus import EventBus
from server.game.snapshot_events import count_pieces, has_promotion, winner_color
from server.server_config import TICK_MS

logger = logging.getLogger("server.session")


class TickLoop:
    """Owns the background task that drives the game clock and pushes state."""

    def __init__(self, session_id: str, controller, connections: dict, event_bus: EventBus) -> None:
        self._session_id = session_id
        self._controller = controller
        self._connections = connections
        self._event_bus = event_bus
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(TICK_MS / 1000)
            snapshot_before = self._controller.get_snapshot()
            self._controller.update(TICK_MS)
            snapshot_after = self._controller.get_snapshot()
            self._publish_tick_events(snapshot_before, snapshot_after)
            await self._broadcast()
            if snapshot_after.game_over:
                break

    def _publish_tick_events(self, before, after) -> None:
        if count_pieces(after) < count_pieces(before):
            self._event_bus.publish(events.PIECE_CAPTURED, {"room_id": self._session_id})
        if has_promotion(before, after):
            self._event_bus.publish(events.PIECE_PROMOTED, {"room_id": self._session_id})
        if not before.game_over and after.game_over:
            self._event_bus.publish(events.GAME_ENDED, {
                "room_id": self._session_id,
                "winner": winner_color(after),
                "reason": "king_captured",
            })

    async def _broadcast(self) -> None:
        for color, connection in list(self._connections.items()):
            snapshot = self._controller.get_snapshot(viewer_color=color)
            try:
                await connection.send_json({"type": "state", "snapshot": snapshot_to_wire(snapshot)})
            except Exception:
                logger.exception("Failed to broadcast state to %s", color)
