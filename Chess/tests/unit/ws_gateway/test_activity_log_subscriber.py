from ws_gateway.bus import events
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.observability.subscribers import ActivityLogSubscriber


def test_logs_login(caplog):
    bus = EventBus()
    ActivityLogSubscriber(bus)
    with caplog.at_level("INFO", logger="ws_gateway.activity"):
        bus.publish(events.LOGIN_SUCCEEDED, {"username": "alice", "rating": 1200})
    assert "alice" in caplog.text
    assert "1200" in caplog.text


def test_logs_match_found(caplog):
    bus = EventBus()
    ActivityLogSubscriber(bus)
    with caplog.at_level("INFO", logger="ws_gateway.activity"):
        bus.publish(events.MATCH_FOUND, {"room_id": "r1", "white": "alice", "black": "bob"})
    assert "r1" in caplog.text
    assert "alice" in caplog.text
    assert "bob" in caplog.text


def test_logs_room_created_and_joined(caplog):
    bus = EventBus()
    ActivityLogSubscriber(bus)
    with caplog.at_level("INFO", logger="ws_gateway.activity"):
        bus.publish(events.ROOM_CREATED, {"room_id": "abc123", "username": "alice"})
        bus.publish(events.ROOM_JOINED, {"room_id": "abc123", "username": "bob", "role": "b"})
    assert "abc123" in caplog.text
    assert "bob" in caplog.text


def test_logs_player_disconnected(caplog):
    bus = EventBus()
    ActivityLogSubscriber(bus)
    with caplog.at_level("INFO", logger="ws_gateway.activity"):
        bus.publish(events.PLAYER_DISCONNECTED, {"room_id": "r1", "username": "alice", "color": "w"})
    assert "alice" in caplog.text
