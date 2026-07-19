"""Unit tests for server.game.game_session.GameSession.

Only the synchronous parts are covered here (seating, per-color click
routing/ownership, per-viewer snapshots, bus events on move) -- the tick
loop and broadcast are async and are covered by manual smoke testing, per
the project's "pure core + thin async shell" approach.
"""

from server.bus import events
from server.bus.event_bus import EventBus
from server.game.game_session import GameSession

SMALL_BOARD = """Board:
wK .
. bK
"""


class FakeConnection:
    def __init__(self, username="player"):
        self.username = username


def make_session(board_text=SMALL_BOARD):
    return GameSession("test-room", EventBus(), board_text=board_text)


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

    session.handle_move_click("w", 0, 0)  # select
    session.handle_move_click("w", 0, 1)  # move -> should publish

    assert len(published) == 1
    assert published[0]["start"] == (0, 0)
    assert published[0]["end"] == (0, 1)
    assert published[0]["color"] == "w"


def test_selecting_own_piece_does_not_publish_move_made():
    bus = EventBus()
    published = []
    bus.subscribe(events.MOVE_MADE, lambda payload: published.append(payload))
    session = GameSession("test-room", bus, board_text="Board:\nwK .\n")

    session.handle_move_click("w", 0, 0)  # selection only, no move queued

    assert published == []
