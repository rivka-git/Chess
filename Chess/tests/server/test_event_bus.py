"""Unit tests for server.bus.event_bus and server.bus.subscribers."""

from server.bus import events
from server.bus.event_bus import EventBus
from server.bus.subscribers import MoveLogSubscriber


def test_publish_calls_subscribed_handler():
    bus = EventBus()
    received = []
    bus.subscribe("something", lambda payload: received.append(payload))
    bus.publish("something", {"x": 1})
    assert received == [{"x": 1}]


def test_publish_with_no_subscribers_is_noop():
    bus = EventBus()
    bus.publish("nothing", {"x": 1})  # must not raise


def test_publish_defaults_to_empty_payload():
    bus = EventBus()
    received = []
    bus.subscribe("evt", lambda payload: received.append(payload))
    bus.publish("evt")
    assert received == [{}]


def test_multiple_subscribers_all_called_in_order():
    bus = EventBus()
    calls = []
    bus.subscribe("evt", lambda payload: calls.append("a"))
    bus.subscribe("evt", lambda payload: calls.append("b"))
    bus.publish("evt", {})
    assert calls == ["a", "b"]


def test_handler_exception_does_not_break_other_subscribers():
    bus = EventBus()
    calls = []

    def failing(payload):
        raise ValueError("boom")

    bus.subscribe("evt", failing)
    bus.subscribe("evt", lambda payload: calls.append("ok"))
    bus.publish("evt", {})
    assert calls == ["ok"]


def test_subscribers_are_isolated_per_event_type():
    bus = EventBus()
    calls = []
    bus.subscribe("evt_a", lambda payload: calls.append("a"))
    bus.publish("evt_b", {})
    assert calls == []


def test_move_log_subscriber_logs_game_started(caplog):
    bus = EventBus()
    MoveLogSubscriber(bus)
    with caplog.at_level("INFO", logger="server.movelog"):
        bus.publish(events.GAME_STARTED, {"room_id": "r1", "white": "alice", "black": "bob"})
    assert "r1" in caplog.text
    assert "alice" in caplog.text
    assert "bob" in caplog.text


def test_move_log_subscriber_logs_move_made(caplog):
    bus = EventBus()
    MoveLogSubscriber(bus)
    with caplog.at_level("INFO", logger="server.movelog"):
        bus.publish(events.MOVE_MADE, {"room_id": "r1", "start": (0, 0), "end": (0, 1)})
    assert "r1" in caplog.text
    assert "(0, 0)" in caplog.text
    assert "(0, 1)" in caplog.text


def test_move_log_subscriber_logs_piece_captured(caplog):
    bus = EventBus()
    MoveLogSubscriber(bus)
    with caplog.at_level("INFO", logger="server.movelog"):
        bus.publish(events.PIECE_CAPTURED, {"room_id": "r1", "position": (0, 1), "captured_token": "bR"})
    assert "bR" in caplog.text


def test_move_log_subscriber_logs_game_ended(caplog):
    bus = EventBus()
    MoveLogSubscriber(bus)
    with caplog.at_level("INFO", logger="server.movelog"):
        bus.publish(events.GAME_ENDED, {"room_id": "r1", "winner": "white", "reason": "king_captured"})
    assert "white" in caplog.text
    assert "king_captured" in caplog.text
