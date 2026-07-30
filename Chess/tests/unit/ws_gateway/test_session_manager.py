from ws_gateway.bus import events
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.game.session_manager import SessionManager


def make_manager():
    return SessionManager(EventBus())


def test_get_returns_none_for_unknown_id():
    assert make_manager().get("no-such-room") is None


def test_get_or_create_creates_new_session():
    manager = make_manager()
    session = manager.get_or_create("room1")
    assert session is not None
    assert session.session_id == "room1"


def test_get_or_create_returns_same_session_if_not_over():
    manager = make_manager()
    s1 = manager.get_or_create("room1")
    s2 = manager.get_or_create("room1")
    assert s1 is s2


def test_get_or_create_replaces_session_after_game_over():
    manager = make_manager()
    s1 = manager.get_or_create("room1")
    s1.resign("w")
    s2 = manager.get_or_create("room1")
    assert s1 is not s2


def test_remove_deletes_session():
    manager = make_manager()
    manager.get_or_create("room1")
    manager.remove("room1")
    assert manager.get("room1") is None


def test_remove_unknown_id_does_not_raise():
    make_manager().remove("ghost")


def test_game_ended_event_removes_session_from_memory():
    bus = EventBus()
    manager = SessionManager(bus)
    manager.get_or_create("room1")
    assert manager.get("room1") is not None

    bus.publish(events.GAME_ENDED, {"room_id": "room1"})

    assert manager.get("room1") is None


def test_game_ended_for_unknown_room_does_not_raise():
    bus = EventBus()
    manager = SessionManager(bus)
    bus.publish(events.GAME_ENDED, {"room_id": "no-such-room"})
