import asyncio
import json

import pytest
import pytest_asyncio

from ws_gateway.auth.password_hasher import PasswordHasher
from ws_gateway.auth.auth_service import AuthService
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.game.session_manager import SessionManager
from ws_gateway.matchmaking.matchmaker_service import MatchmakerService
from ws_gateway.matchmaking.matchmaking_queue import MatchmakingQueue
from ws_gateway.net.connection import ClientConnection
from ws_gateway.net.dispatch import Dispatcher
from ws_gateway.rooms.room_service import RoomService
from ws_gateway.persistence.player_repository import Player


class FakeWebSocket:
    def __init__(self):
        self.sent = []
        self.closed = False

    async def send(self, raw):
        self.sent.append(json.loads(raw))

    async def close(self):
        self.closed = True


class FakePlayerRepository:
    def __init__(self):
        self._store: dict = {}
        self._next_id = 1

    async def get_by_username(self, username):
        return self._store.get(username)

    async def create(self, username, password_hash, password_salt, rating=1200):
        player = Player(id=self._next_id, username=username, password_hash=password_hash,
                        password_salt=password_salt, rating=rating, created_at="")
        self._next_id += 1
        self._store[username] = player
        return player

    async def update_rating(self, username, new_rating):
        p = self._store[username]
        self._store[username] = Player(p.id, p.username, p.password_hash, p.password_salt, new_rating, p.created_at)


@pytest_asyncio.fixture(autouse=True)
async def _cancel_background_tasks():
    yield
    current = asyncio.current_task()
    pending = [task for task in asyncio.all_tasks() if task is not current]
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


def make_dispatcher():
    bus = EventBus()
    player_repo = FakePlayerRepository()
    auth = AuthService(player_repo, PasswordHasher(iterations=1_000))
    session_manager = SessionManager(bus)
    queue = MatchmakingQueue()
    matchmaker = MatchmakerService(queue, session_manager, bus)
    room_service = RoomService(session_manager)
    return Dispatcher(session_manager, auth, matchmaker, room_service, bus)


def make_connection():
    return ClientConnection(FakeWebSocket())


async def login(dispatcher, connection, username, password="pw"):
    await dispatcher.on_message(connection, {"type": "login", "username": username, "password": password})


# --- login gating ---

@pytest.mark.asyncio
async def test_move_click_before_login_is_rejected():
    dispatcher = make_dispatcher()
    connection = make_connection()

    await dispatcher.on_message(connection, {"type": "move_click", "row": 0, "col": 0})

    assert connection.websocket.sent[-1]["code"] == "not_authenticated"
    assert not connection.is_authenticated


@pytest.mark.asyncio
async def test_login_with_missing_password_is_bad_request():
    dispatcher = make_dispatcher()
    connection = make_connection()

    await dispatcher.on_message(connection, {"type": "login", "username": "alice"})

    assert connection.websocket.sent[-1]["code"] == "bad_request"
    assert not connection.is_authenticated


@pytest.mark.asyncio
async def test_login_with_new_username_auto_registers_but_does_not_seat():
    dispatcher = make_dispatcher()
    connection = make_connection()

    await login(dispatcher, connection, "alice")

    assert connection.websocket.sent == [{"type": "login_ok", "username": "alice", "rating": 1200}]
    assert connection.username == "alice"
    assert connection.room_id is None
    assert connection.color is None


@pytest.mark.asyncio
async def test_login_with_wrong_password_is_rejected_and_connection_stays_open():
    dispatcher = make_dispatcher()
    first = make_connection()
    await login(dispatcher, first, "alice", "correct")

    second = make_connection()
    await login(dispatcher, second, "alice", "wrong")

    assert second.websocket.sent[-1] == {
        "type": "login_failed", "code": "invalid_credentials", "message": "Wrong password.",
    }
    assert not second.is_authenticated
    assert not second.websocket.closed


# --- matchmaking ---

@pytest.mark.asyncio
async def test_find_match_with_nobody_waiting_sends_searching_match():
    dispatcher = make_dispatcher()
    connection = make_connection()
    await login(dispatcher, connection, "alice")

    await dispatcher.on_message(connection, {"type": "find_match"})

    assert connection.websocket.sent[-1] == {"type": "searching_match"}
    assert connection.room_id is None


@pytest.mark.asyncio
async def test_find_match_pairs_two_waiting_players():
    dispatcher = make_dispatcher()
    alice = make_connection()
    bob = make_connection()
    await login(dispatcher, alice, "alice")
    await login(dispatcher, bob, "bob")

    await dispatcher.on_message(alice, {"type": "find_match"})
    await dispatcher.on_message(bob, {"type": "find_match"})

    assert alice.color == "w"
    assert bob.color == "b"
    assert alice.room_id == bob.room_id
    assert [m["type"] for m in bob.websocket.sent[-2:]] == ["role_assigned", "state"]


@pytest.mark.asyncio
async def test_disconnect_while_queued_removes_from_matchmaking():
    dispatcher = make_dispatcher()
    alice = make_connection()
    bob = make_connection()
    await login(dispatcher, alice, "alice")
    await login(dispatcher, bob, "bob")

    await dispatcher.on_message(alice, {"type": "find_match"})
    await dispatcher.on_disconnect(alice)

    await dispatcher.on_message(bob, {"type": "find_match"})

    assert bob.websocket.sent[-1] == {"type": "searching_match"}
    assert bob.room_id is None


# --- rooms ---

@pytest.mark.asyncio
async def test_create_room_seats_creator_as_white():
    dispatcher = make_dispatcher()
    connection = make_connection()
    await login(dispatcher, connection, "alice")

    await dispatcher.on_message(connection, {"type": "create_room"})

    assert connection.color == "w"
    assert connection.room_id is not None
    assert not connection.is_spectator


@pytest.mark.asyncio
async def test_join_room_seats_second_player_as_black():
    dispatcher = make_dispatcher()
    creator = make_connection()
    joiner = make_connection()
    await login(dispatcher, creator, "alice")
    await login(dispatcher, joiner, "bob")
    await dispatcher.on_message(creator, {"type": "create_room"})
    room_id = creator.room_id

    await dispatcher.on_message(joiner, {"type": "join_room", "room_id": room_id})

    assert joiner.color == "b"
    assert joiner.room_id == room_id
    assert not joiner.is_spectator


@pytest.mark.asyncio
async def test_join_room_with_unknown_id_is_rejected():
    dispatcher = make_dispatcher()
    connection = make_connection()
    await login(dispatcher, connection, "alice")

    await dispatcher.on_message(connection, {"type": "join_room", "room_id": "does-not-exist"})

    assert connection.websocket.sent[-1]["code"] == "room_not_found"
    assert connection.room_id is None


@pytest.mark.asyncio
async def test_third_player_joining_a_full_room_becomes_spectator():
    dispatcher = make_dispatcher()
    creator = make_connection()
    joiner = make_connection()
    viewer = make_connection()
    await login(dispatcher, creator, "alice")
    await login(dispatcher, joiner, "bob")
    await login(dispatcher, viewer, "carol")
    await dispatcher.on_message(creator, {"type": "create_room"})
    room_id = creator.room_id
    await dispatcher.on_message(joiner, {"type": "join_room", "room_id": room_id})

    await dispatcher.on_message(viewer, {"type": "join_room", "room_id": room_id})

    assert viewer.is_spectator
    assert viewer.color is None
    assert viewer.room_id == room_id
    assert [m["type"] for m in viewer.websocket.sent[-2:]] == ["spectating", "state"]


# --- in-game routing ---

@pytest.mark.asyncio
async def test_move_click_after_being_seated_is_routed_to_session_not_rejected():
    dispatcher = make_dispatcher()
    alice = make_connection()
    bob = make_connection()
    await login(dispatcher, alice, "alice")
    await login(dispatcher, bob, "bob")
    await dispatcher.on_message(alice, {"type": "find_match"})
    await dispatcher.on_message(bob, {"type": "find_match"})

    sent_before = len(alice.websocket.sent)
    await dispatcher.on_message(alice, {"type": "move_click", "row": 0, "col": 0})

    assert len(alice.websocket.sent) == sent_before


@pytest.mark.asyncio
async def test_spectator_move_click_is_rejected():
    dispatcher = make_dispatcher()
    creator = make_connection()
    joiner = make_connection()
    viewer = make_connection()
    await login(dispatcher, creator, "alice")
    await login(dispatcher, joiner, "bob")
    await login(dispatcher, viewer, "carol")
    await dispatcher.on_message(creator, {"type": "create_room"})
    room_id = creator.room_id
    await dispatcher.on_message(joiner, {"type": "join_room", "room_id": room_id})
    await dispatcher.on_message(viewer, {"type": "join_room", "room_id": room_id})

    await dispatcher.on_message(viewer, {"type": "move_click", "row": 0, "col": 0})

    assert viewer.websocket.sent[-1]["code"] == "read_only"
