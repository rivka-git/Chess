"""Routes incoming client messages to the right handler.

M2 scope: a single fixed two-player game, no login/matchmaking/rooms yet
(those arrive in later milestones and replace DEFAULT_ROOM_ID's degenerate
single-session behavior with real room/matchmaking-created sessions).
"""

from __future__ import annotations

import logging

from server.game.session_manager import SessionManager
from server.net.connection import ClientConnection

logger = logging.getLogger("server.dispatch")

DEFAULT_ROOM_ID = "default"

_ROLE_NAMES = {"w": "white", "b": "black"}


class Dispatcher:
    def __init__(self, session_manager: SessionManager) -> None:
        self._sessions = session_manager

    async def on_connect(self, connection: ClientConnection) -> None:
        session = self._sessions.get_or_create(DEFAULT_ROOM_ID)
        role = session.seat_next(connection)
        if role is None:
            await connection.send_json({
                "type": "error", "code": "server_full",
                "message": "This game already has two players.",
            })
            await connection.websocket.close()
            return

        connection.color = role
        connection.room_id = DEFAULT_ROOM_ID
        await connection.send_json({
            "type": "role_assigned", "role": _ROLE_NAMES[role], "room_id": DEFAULT_ROOM_ID,
        })
        if session.is_full() and not session.started:
            session.start()

    async def on_message(self, connection: ClientConnection, message: dict) -> None:
        if connection.room_id is None:
            await connection.send_json({
                "type": "error", "code": "no_session", "message": "Not in a game.",
            })
            return
        session = self._sessions.get(connection.room_id)
        if session is None:
            await connection.send_json({
                "type": "error", "code": "no_session", "message": "Not in a game.",
            })
            return

        msg_type = message.get("type")
        if msg_type in ("move_click", "jump_click"):
            await self._handle_click(session, connection, message, is_jump=msg_type == "jump_click")
        else:
            await connection.send_json({
                "type": "error", "code": "unknown_type", "message": f"Unknown message type: {msg_type!r}",
            })

    async def _handle_click(self, session, connection: ClientConnection, message: dict, is_jump: bool) -> None:
        if connection.is_spectator or connection.color is None:
            await connection.send_json({
                "type": "error", "code": "read_only", "message": "Spectators cannot move pieces.",
            })
            return
        row, col = message.get("row"), message.get("col")
        if not isinstance(row, int) or not isinstance(col, int):
            await connection.send_json({
                "type": "error", "code": "bad_request", "message": "move_click/jump_click require integer row/col.",
            })
            return
        if is_jump:
            session.handle_jump_click(connection.color, row, col)
        else:
            session.handle_move_click(connection.color, row, col)

    async def on_disconnect(self, connection: ClientConnection) -> None:
        if connection.room_id is None:
            return
        session = self._sessions.get(connection.room_id)
        if session is not None:
            session.remove_connection(connection)
