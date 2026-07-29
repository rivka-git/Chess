"""Routes incoming client messages to the right handler.

Login is handled here over WebSocket for backward compatibility with the
existing client. History queries are forwarded to the API Gateway.
"""

from __future__ import annotations

import logging

from pydantic import ValidationError

from netcommon.messages import (
    parse_client_message,
    LoginMsg, FindMatchMsg, CreateRoomMsg, JoinRoomMsg,
    MoveClickMsg, JumpClickMsg,
)
from ws_gateway.bus import events
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.game.seating import seat_and_notify
from ws_gateway.game.session_manager import SessionManager
from ws_gateway.matchmaking.matchmaker_service import MatchmakerService
from ws_gateway.net.connection import ClientConnection
from ws_gateway.rooms.exceptions import RoomNotFoundError
from ws_gateway.rooms.room_service import RoomService

logger = logging.getLogger("ws_gateway.dispatch")


class Dispatcher:
    def __init__(
        self,
        session_manager: SessionManager,
        auth_service,
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
        pass

    async def on_message(self, connection: ClientConnection, raw: dict) -> None:
        try:
            message = parse_client_message(raw)
        except ValidationError as exc:
            await connection.send_json({"type": "error", "code": "bad_request", "message": exc.errors()[0]["msg"]})
            return

        if not connection.is_authenticated:
            await self._handle_login(connection, message)
            return

        if connection.room_id is None:
            await self._handle_pre_room(connection, message)
            return

        session = self._sessions.get(connection.room_id)
        if session is None:
            await connection.send_json({"type": "error", "code": "no_session", "message": "Not in a game."})
            return

        if isinstance(message, (MoveClickMsg, JumpClickMsg)):
            await self._handle_click(session, connection, message)
        else:
            await connection.send_json({"type": "error", "code": "unknown_type", "message": f"Unexpected message type in-game: {message.type!r}"})

    async def on_disconnect(self, connection: ClientConnection) -> None:
        if connection.username is not None:
            await self._matchmaker.forget(connection.username)
        if connection.room_id is None:
            return
        session = self._sessions.get(connection.room_id)
        if session is None:
            return
        if connection.is_spectator:
            session.remove_spectator(connection)
        else:
            session.on_player_disconnected(connection)

    async def _try_reconnect(self, connection: ClientConnection) -> None:
        from netcommon.messages import snapshot_to_wire
        for session in self._sessions._sessions.values():
            color = session.on_player_reconnected(connection.username, connection)
            if color is not None:
                connection.color = color
                connection.room_id = session.session_id
                await connection.send_json({"type": "reconnected", "room_id": session.session_id})
                await connection.send_json({"type": "state", "snapshot": snapshot_to_wire(session.get_viewer_snapshot(color))})
                return

    async def _handle_login(self, connection: ClientConnection, message) -> None:
        if not isinstance(message, LoginMsg):
            await connection.send_json({"type": "error", "code": "not_authenticated", "message": "Log in first."})
            return
        try:
            player = await self._auth.login_or_register(message.username, message.password)
        except Exception:
            await connection.send_json({"type": "login_failed", "code": "invalid_credentials", "message": "Wrong password."})
            return
        connection.player = player
        self._event_bus.publish(events.LOGIN_SUCCEEDED, {"username": player.username, "rating": player.rating})
        await connection.send_json({"type": "login_ok", "username": player.username, "rating": player.rating})
        await self._try_reconnect(connection)

    async def _handle_pre_room(self, connection: ClientConnection, message) -> None:
        if isinstance(message, FindMatchMsg):
            await self._matchmaker.handle_find_match(connection)
        elif isinstance(message, CreateRoomMsg):
            await self._handle_create_room(connection)
        elif isinstance(message, JoinRoomMsg):
            await self._handle_join_room(connection, message)
        else:
            await connection.send_json({"type": "error", "code": "unknown_type", "message": f"Unknown message type: {message.type!r}"})

    async def _handle_create_room(self, connection: ClientConnection) -> None:
        room_id = self._rooms.create_room()
        session = self._sessions.get(room_id)
        await seat_and_notify(session, connection)
        self._event_bus.publish(events.ROOM_CREATED, {"room_id": room_id, "username": connection.username})

    async def _handle_join_room(self, connection: ClientConnection, message: JoinRoomMsg) -> None:
        try:
            session = self._rooms.get_room(message.room_id)
        except RoomNotFoundError:
            await connection.send_json({"type": "error", "code": "room_not_found", "message": f"No room {message.room_id!r}."})
            return
        role = await seat_and_notify(session, connection)
        if role is None:
            await self._seat_as_spectator(session, connection)
        self._event_bus.publish(events.ROOM_JOINED, {"room_id": message.room_id, "username": connection.username, "role": role if role is not None else "spectator"})

    async def _seat_as_spectator(self, session, connection: ClientConnection) -> None:
        from netcommon.messages import snapshot_to_wire
        connection.is_spectator = True
        connection.room_id = session.session_id
        session.add_spectator(connection)
        await connection.send_json({"type": "spectating", "room_id": session.session_id})
        await connection.send_json({"type": "state", "snapshot": snapshot_to_wire(session.get_viewer_snapshot(None))})

    async def _handle_click(self, session, connection: ClientConnection, message) -> None:
        if connection.is_spectator or connection.color is None:
            await connection.send_json({"type": "error", "code": "read_only", "message": "Spectators cannot move pieces."})
            return
        if isinstance(message, JumpClickMsg):
            session.handle_jump_click(connection.color, message.row, message.col)
        else:
            session.handle_move_click(connection.color, message.row, message.col)
