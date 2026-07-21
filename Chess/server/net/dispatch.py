"""Routes incoming client messages to the right handler.

Every connection must log in before doing anything else. Once authenticated
but not yet seated in a room, it may either queue for automatic matchmaking
(find_match) or create/join an explicit room by id (create_room/join_room).
Once seated, move_click/jump_click are routed to that room's session.
"""

from __future__ import annotations

import logging

from server.auth.auth_service import AuthService
from server.auth.exceptions import InvalidCredentialsError
from server.bus import events
from server.bus.event_bus import EventBus
from server.game.seating import seat_and_notify
from server.game.session_manager import SessionManager
from server.matchmaking.matchmaker_service import MatchmakerService
from server.net.connection import ClientConnection
from server.rooms.exceptions import RoomNotFoundError
from server.rooms.room_service import RoomService

logger = logging.getLogger("server.dispatch")


class Dispatcher:
    def __init__(
        self,
        session_manager: SessionManager,
        auth_service: AuthService,
        matchmaker: MatchmakerService,
        room_service: RoomService,
        event_bus: EventBus,
    ) -> None:
        self._sessions = session_manager
        self._auth = auth_service
        self._matchmaker = matchmaker
        self._rooms = room_service
        self._event_bus = event_bus

    async def on_connect(self, connection: ClientConnection) -> None:
        # Nothing to do yet -- the connection must send a login message
        # before it is authenticated, matched, or seated into any room.
        pass

    async def on_message(self, connection: ClientConnection, message: dict) -> None:
        if not connection.is_authenticated:
            await self._handle_login(connection, message)
            return

        if connection.room_id is None:
            await self._handle_pre_room(connection, message)
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

    async def on_disconnect(self, connection: ClientConnection) -> None:
        if connection.username is not None:
            self._matchmaker.forget(connection.username)
        if connection.room_id is None:
            return
        session = self._sessions.get(connection.room_id)
        if session is None:
            return
        if connection.is_spectator:
            session.remove_connection(connection)
        else:
            session.on_player_disconnected(connection)

    # --- login ---

    async def _handle_login(self, connection: ClientConnection, message: dict) -> None:
        if message.get("type") != "login":
            await connection.send_json({
                "type": "error", "code": "not_authenticated", "message": "Log in first.",
            })
            return
        username, password = message.get("username"), message.get("password")
        if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
            await connection.send_json({
                "type": "error", "code": "bad_request", "message": "login requires non-empty username/password.",
            })
            return

        try:
            player = self._auth.login_or_register(username, password)
        except InvalidCredentialsError:
            await connection.send_json({
                "type": "login_failed", "code": "invalid_credentials", "message": "Wrong password.",
            })
            return

        connection.player = player
        self._event_bus.publish(events.LOGIN_SUCCEEDED, {
            "username": player.username, "rating": player.rating,
        })
        await connection.send_json({
            "type": "login_ok", "username": player.username, "rating": player.rating,
        })

    # --- matchmaking / rooms (pre-seating) ---

    async def _handle_pre_room(self, connection: ClientConnection, message: dict) -> None:
        msg_type = message.get("type")
        if msg_type == "find_match":
            await self._matchmaker.handle_find_match(connection)
        elif msg_type == "create_room":
            await self._handle_create_room(connection)
        elif msg_type == "join_room":
            await self._handle_join_room(connection, message)
        else:
            await connection.send_json({
                "type": "error", "code": "unknown_type", "message": f"Unknown message type: {msg_type!r}",
            })

    async def _handle_create_room(self, connection: ClientConnection) -> None:
        room_id = self._rooms.create_room()
        session = self._sessions.get(room_id)
        await seat_and_notify(session, connection)
        self._event_bus.publish(events.ROOM_CREATED, {
            "room_id": room_id, "username": connection.username,
        })

    async def _handle_join_room(self, connection: ClientConnection, message: dict) -> None:
        room_id = message.get("room_id")
        if not isinstance(room_id, str) or not room_id:
            await connection.send_json({
                "type": "error", "code": "bad_request", "message": "join_room requires a room_id.",
            })
            return
        try:
            session = self._rooms.get_room(room_id)
        except RoomNotFoundError:
            await connection.send_json({
                "type": "error", "code": "room_not_found", "message": f"No room {room_id!r}.",
            })
            return

        role = await seat_and_notify(session, connection)
        if role is None:
            await self._seat_as_spectator(session, connection)
        self._event_bus.publish(events.ROOM_JOINED, {
            "room_id": room_id, "username": connection.username,
            "role": role if role is not None else "spectator",
        })

    async def _seat_as_spectator(self, session, connection: ClientConnection) -> None:
        connection.is_spectator = True
        connection.room_id = session.session_id
        await connection.send_json({"type": "spectating", "room_id": session.session_id})
        from netcommon.messages import snapshot_to_wire
        await connection.send_json({
            "type": "state",
            "snapshot": snapshot_to_wire(session.get_viewer_snapshot(None)),
        })

    # --- in-game ---

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
