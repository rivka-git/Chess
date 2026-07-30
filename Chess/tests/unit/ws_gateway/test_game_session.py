import asyncio

import pytest
import pytest_asyncio

from ws_gateway.bus import events
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.game.game_session import GameSession

SMALL_BOARD = """Board:
wK .
. bK
"""


class FakeConnection:
    def __init__(self, username="player"):
        self.username = username

    async def send_json(self, message):
        pass


def make_session(board_text=SMALL_BOARD):
    return GameSession("test-room", EventBus(), board_text=board_text)


@pytest_asyncio.fixture
async def cancel_tasks():
    yield
    current = asyncio.current_task()
    pending = [task for task in asyncio.all_tasks() if task is not current]
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


def test_seat_next_assigns_white_then_black_then_full():
    session = make_session()
    assert session.seat_next(FakeConnection("alice")) == "w"
    assert session.seat_next(FakeConnection("bob")) == "b"
    assert session.seat_next(FakeConnection("carol")) is None


def test_is_full_only_after_two_seated():
    session = make_session()
    assert not session.is_full()
    session.seat_next(FakeConnection("alice"))
    assert not session.is_full()
    session.seat_next(FakeConnection("bob"))
    assert session.is_full()


def test_remove_connection_frees_seat():
    session = make_session()
    conn = FakeConnection("alice")
    session.seat_next(conn)
    session.remove_connection(conn)
    assert session.seat_next(FakeConnection("bob")) == "w"


def test_white_cannot_select_black_piece():
    session = make_session()
    session.handle_move_click("w", 1, 1)
    assert session.get_viewer_snapshot("w").selected_position is None


def test_move_click_selects_own_piece():
    session = make_session()
    session.handle_move_click("w", 0, 0)
    assert session.get_viewer_snapshot("w").selected_position == (0, 0)


def test_selection_is_independent_per_viewer():
    session = make_session()
    session.handle_move_click("w", 0, 0)
    session.handle_move_click("b", 1, 1)
    assert session.get_viewer_snapshot("w").selected_position == (0, 0)
    assert session.get_viewer_snapshot("b").selected_position == (1, 1)


def test_move_click_publishes_move_made_event():
    bus = EventBus()
    published = []
    bus.subscribe(events.MOVE_MADE, lambda payload: published.append(payload))
    session = GameSession("test-room", bus, board_text="Board:\nwK .\n")

    session.handle_move_click("w", 0, 0)
    session.handle_move_click("w", 0, 1)

    assert len(published) == 1
    assert published[0]["start"] == (0, 0)
    assert published[0]["end"] == (0, 1)
    assert published[0]["color"] == "w"


def test_selecting_own_piece_does_not_publish_move_made():
    bus = EventBus()
    published = []
    bus.subscribe(events.MOVE_MADE, lambda payload: published.append(payload))
    session = GameSession("test-room", bus, board_text="Board:\nwK .\n")

    session.handle_move_click("w", 0, 0)

    assert published == []


def test_is_over_is_false_for_a_fresh_session():
    assert not make_session().is_over()


def test_resign_declares_the_opponent_the_winner_and_ends_the_game():
    session = make_session()
    session.seat_next(FakeConnection("alice"))
    session.seat_next(FakeConnection("bob"))

    session.resign("w")

    assert session.is_over()
    assert session.get_viewer_snapshot("b").game_over


def test_resign_publishes_game_ended_with_disconnect_reason_and_usernames():
    bus = EventBus()
    ended = []
    bus.subscribe(events.GAME_ENDED, lambda payload: ended.append(payload))
    session = GameSession("test-room", bus, board_text=SMALL_BOARD)
    session.seat_next(FakeConnection("alice"))
    session.seat_next(FakeConnection("bob"))

    session.resign("b")

    assert len(ended) == 1
    assert ended[0]["winner"] == "white"
    assert ended[0]["reason"] == "disconnect_timeout"
    assert ended[0]["white"] == "alice"
    assert ended[0]["black"] == "bob"


def test_resign_is_idempotent():
    bus = EventBus()
    ended = []
    bus.subscribe(events.GAME_ENDED, lambda payload: ended.append(payload))
    session = GameSession("test-room", bus, board_text=SMALL_BOARD)
    session.seat_next(FakeConnection("alice"))
    session.seat_next(FakeConnection("bob"))

    session.resign("w")
    session.resign("w")
    session.resign("b")

    assert len(ended) == 1


def test_on_player_disconnected_before_start_frees_seat_without_ending_game():
    bus = EventBus()
    ended = []
    bus.subscribe(events.GAME_ENDED, lambda payload: ended.append(payload))
    session = GameSession("test-room", bus, board_text=SMALL_BOARD)
    alice = FakeConnection("alice")
    session.seat_next(alice)

    session.on_player_disconnected(alice)

    assert ended == []
    assert not session.is_over()
    assert session.seat_next(FakeConnection("bob")) == "w"


@pytest.mark.asyncio
async def test_on_player_disconnected_after_start_publishes_event_and_arms_timer(cancel_tasks):
    bus = EventBus()
    disconnects = []
    bus.subscribe(events.PLAYER_DISCONNECTED, lambda payload: disconnects.append(payload))
    session = GameSession("test-room", bus, board_text=SMALL_BOARD)
    alice = FakeConnection("alice")
    bob = FakeConnection("bob")
    session.seat_next(alice)
    session.seat_next(bob)
    session.start()

    session.on_player_disconnected(alice)

    assert len(disconnects) == 1
    assert disconnects[0]["color"] == "w"
    assert disconnects[0]["username"] == "alice"
    assert not session.is_over()


@pytest.mark.asyncio
async def test_reconnect_cancels_timer_and_restores_seat(cancel_tasks):
    session = GameSession("test-room", EventBus(), board_text=SMALL_BOARD)
    alice = FakeConnection("alice")
    bob = FakeConnection("bob")
    session.seat_next(alice)
    session.seat_next(bob)
    session.start()

    session.on_player_disconnected(alice)
    assert "w" in session._disconnect_timers

    new_alice = FakeConnection("alice")
    color = session.on_player_reconnected("alice", new_alice)

    assert color == "w"
    assert "w" not in session._disconnect_timers
    assert session._connections["w"] is new_alice
    assert not session.is_over()


@pytest.mark.asyncio
async def test_reconnect_unknown_username_returns_none(cancel_tasks):
    session = GameSession("test-room", EventBus(), board_text=SMALL_BOARD)
    alice = FakeConnection("alice")
    bob = FakeConnection("bob")
    session.seat_next(alice)
    session.seat_next(bob)
    session.start()

    result = session.on_player_reconnected("carol", FakeConnection("carol"))

    assert result is None


@pytest.mark.asyncio
async def test_reconnect_without_active_timer_returns_none(cancel_tasks):
    session = GameSession("test-room", EventBus(), board_text=SMALL_BOARD)
    alice = FakeConnection("alice")
    bob = FakeConnection("bob")
    session.seat_next(alice)
    session.seat_next(bob)
    session.start()

    result = session.on_player_reconnected("alice", FakeConnection("alice"))

    assert result is None


def test_add_spectator_and_remove_spectator():
    session = make_session()
    spectator = FakeConnection("spectator")
    session.add_spectator(spectator)
    assert spectator in session._spectators
    session.remove_spectator(spectator)
    assert spectator not in session._spectators


def test_spectator_gets_none_color_snapshot():
    session = make_session()
    spectator = FakeConnection("spectator")
    session.add_spectator(spectator)
    snapshot = session.get_viewer_snapshot(None)
    assert snapshot is not None
    assert snapshot.selected_position is None


def test_spectator_does_not_affect_is_full():
    session = make_session()
    session.add_spectator(FakeConnection("spectator"))
    assert not session.is_full()
    session.seat_next(FakeConnection("alice"))
    session.seat_next(FakeConnection("bob"))
    assert session.is_full()


def test_remove_nonexistent_spectator_is_safe():
    session = make_session()
    session.remove_spectator(FakeConnection("ghost"))
