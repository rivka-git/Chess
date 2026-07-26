"""Routes incoming client messages to the right handler.

Every connection must log in before doing anything else. Once authenticated
but not yet seated in a room, it may either queue for automatic matchmaking
(find_match) or create/join an explicit room by id (create_room/join_room).
Once seated, move_click/jump_click are routed to that room's session.
"""

from __future__ import annotations

import logging

from pydantic import ValidationError

from netcommon.messages import (
    parse_client_message,
    LoginMsg, FindMatchMsg, CreateRoomMsg, JoinRoomMsg, GetHistoryMsg,
    MoveClickMsg, JumpClickMsg,
)
from server.auth.auth_service import AuthService
from server.auth.exceptions import InvalidCredentialsError
from server.bus import events
from server.bus.event_bus import EventBus
from server.game.seating import seat_and_notify
from server.game.session_manager import SessionManager
from server.matchmaking.matchmaker_service import MatchmakerService
from server.net.connection import ClientConnection
from server.persistence.game_repository import GameRepository
from server.rooms.exceptions import RoomNotFoundError
from server.rooms.room_service import RoomService

logger = logging.getLogger("server.dispatch")


def _game_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "room_id": row["room_id"],
        "white": row["white_username"],
        "black": row["black_username"],
        "winner": row["winner"],
        "reason": row["reason"],
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
    }


class Dispatcher:
    def __init__(
        self,
        session_manager: SessionManager,
        auth_service: AuthService,
        matchmaker: MatchmakerService,
        room_service: RoomService,
        event_bus: EventBus,
        game_repository: GameRepository,
    ) -> None:
        self._sessions = session_manager
        self._auth = auth_service
        self._matchmaker = matchmaker
        self._rooms = room_service
        self._event_bus = event_bus
        self._games = game_repository

    async def on_connect(self, connection: ClientConnection) -> None:
        # Nothing to do yet -- the connection must send a login message
        # before it is authenticated, matched, or seated into any room.
        pass

    async def on_message(self, connection: ClientConnection, raw: dict) -> None:
        try:
            message = parse_client_message(raw)
        except ValidationError as exc:
            await connection.send_json({
                "type": "error", "code": "bad_request", "message": exc.errors()[0]["msg"],
            })
            return

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

        if isinstance(message, (MoveClickMsg, JumpClickMsg)):
            await self._handle_click(session, connection, message)
        else:
            await connection.send_json({
                "type": "error", "code": "unknown_type", "message": f"Unexpected message type in-game: {message.type!r}",
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
            session.remove_spectator(connection)
        else:
            session.on_player_disconnected(connection)

    # --- reconnect ---

    async def _try_reconnect(self, connection: ClientConnection) -> None:
        """After login, check if this player has an active disconnect timer
        in any session. If so, cancel it and restore their seat."""
        from netcommon.messages import snapshot_to_wire
        for session in self._sessions._sessions.values():
            color = session.on_player_reconnected(connection.username, connection)
            if color is not None:
                connection.color = color
                connection.room_id = session.session_id
                await connection.send_json({"type": "reconnected", "room_id": session.session_id})
                await connection.send_json({
                    "type": "state",
                    "snapshot": snapshot_to_wire(session.get_viewer_snapshot(color)),
                })
                return

    # --- login ---

    async def _handle_login(self, connection: ClientConnection, message) -> None:
        if not isinstance(message, LoginMsg):
            await connection.send_json({
                "type": "error", "code": "not_authenticated", "message": "Log in first.",
            })
            return

        try:
            player = self._auth.login_or_register(message.username, message.password)
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
        await self._try_reconnect(connection)

    # --- matchmaking / rooms (pre-seating) ---

    async def _handle_pre_room(self, connection: ClientConnection, message) -> None:
        if isinstance(message, FindMatchMsg):
            await self._matchmaker.handle_find_match(connection)
        elif isinstance(message, CreateRoomMsg):
            await self._handle_create_room(connection)
        elif isinstance(message, JoinRoomMsg):
            await self._handle_join_room(connection, message)
        elif isinstance(message, GetHistoryMsg):
            await self._handle_get_history(connection)
        else:
            await connection.send_json({
                "type": "error", "code": "unknown_type", "message": f"Unknown message type: {message.type!r}",
            })

    async def _handle_get_history(self, connection: ClientConnection) -> None:
        rows = self._games.get_games_for_player(connection.username)
        await connection.send_json({
            "type": "history", "games": [_game_to_dict(row) for row in rows],
        })

    async def _handle_create_room(self, connection: ClientConnection) -> None:
        room_id = self._rooms.create_room()
        session = self._sessions.get(room_id)
        await seat_and_notify(session, connection)
        self._event_bus.publish(events.ROOM_CREATED, {
            "room_id": room_id, "username": connection.username,
        })

    async def _handle_join_room(self, connection: ClientConnection, message: JoinRoomMsg) -> None:
        try:
            session = self._rooms.get_room(message.room_id)
        except RoomNotFoundError:
            await connection.send_json({
                "type": "error", "code": "room_not_found", "message": f"No room {message.room_id!r}.",
            })
            return

        role = await seat_and_notify(session, connection)
        if role is None:
            await self._seat_as_spectator(session, connection)
        self._event_bus.publish(events.ROOM_JOINED, {
            "room_id": message.room_id, "username": connection.username,
            "role": role if role is not None else "spectator",
        })

    async def _seat_as_spectator(self, session, connection: ClientConnection) -> None:
        connection.is_spectator = True
        connection.room_id = session.session_id
        session.add_spectator(connection)
        await connection.send_json({"type": "spectating", "room_id": session.session_id})
        from netcommon.messages import snapshot_to_wire
        await connection.send_json({
            "type": "state",
            "snapshot": snapshot_to_wire(session.get_viewer_snapshot(None)),
        })

    # --- in-game ---

    async def _handle_click(self, session, connection: ClientConnection, message: MoveClickMsg | JumpClickMsg) -> None:
        if connection.is_spectator or connection.color is None:
            await connection.send_json({
                "type": "error", "code": "read_only", "message": "Spectators cannot move pieces.",
            })
            return
        if isinstance(message, JumpClickMsg):
            session.handle_jump_click(connection.color, message.row, message.col)
        else:
            session.handle_move_click(connection.color, message.row, message.col)
