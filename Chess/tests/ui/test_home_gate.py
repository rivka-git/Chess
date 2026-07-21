"""Unit tests for network.home_gate.HomeGate."""

from network.home_gate import HomeGate


class FakeWsClient:
    """Stand-in for WsClient: send() synchronously delivers whatever replies
    the test queued up, so wait_for()'s blocking wait resolves without a
    real thread."""

    def __init__(self):
        self.sent = []
        self._on_message = None
        self._next_replies = []

    def start(self, on_message):
        self._on_message = on_message

    def set_message_handler(self, on_message):
        self._on_message = on_message

    def send(self, message):
        self.sent.append(message)
        for reply in self._next_replies:
            self._on_message(reply)
        self._next_replies = []

    def queue_replies(self, *replies):
        self._next_replies = list(replies)

    def push(self, message):
        self._on_message(message)


def test_wait_for_returns_the_matching_reply():
    ws = FakeWsClient()
    gate = HomeGate(ws)
    ws.queue_replies({"type": "login_ok", "username": "alice", "rating": 1200})

    gate.send({"type": "login", "username": "alice", "password": "pw"})
    result = gate.wait_for("login_ok", "login_failed")

    assert result == {"type": "login_ok", "username": "alice", "rating": 1200}
    assert ws.sent == [{"type": "login", "username": "alice", "password": "pw"}]


def test_wait_for_ignores_non_matching_types_until_the_right_one_arrives():
    ws = FakeWsClient()
    gate = HomeGate(ws)
    ws.queue_replies(
        {"type": "searching_match"},
        {"type": "no_match_found", "message": "timed out"},
    )

    gate.send({"type": "find_match"})
    first = gate.wait_for("searching_match", "role_assigned")
    second = gate.wait_for("role_assigned", "no_match_found")

    assert first["type"] == "searching_match"
    assert second["type"] == "no_match_found"


def test_messages_that_do_not_match_are_buffered_until_handoff():
    ws = FakeWsClient()
    gate = HomeGate(ws)
    ws.queue_replies({"type": "login_ok", "username": "alice", "rating": 1200})
    gate.send({"type": "login", "username": "alice", "password": "pw"})
    gate.wait_for("login_ok", "login_failed")

    ws.push({"type": "role_assigned", "role": "white", "room_id": "abc123"})
    ws.push({"type": "state", "snapshot": "x"})

    received = []
    gate.handoff(received.append)

    assert received == [
        {"type": "role_assigned", "role": "white", "room_id": "abc123"},
        {"type": "state", "snapshot": "x"},
    ]


def test_handoff_with_nothing_buffered_calls_nothing():
    ws = FakeWsClient()
    gate = HomeGate(ws)

    received = []
    gate.handoff(received.append)

    assert received == []


def test_second_wait_for_after_first_completes_still_works():
    ws = FakeWsClient()
    gate = HomeGate(ws)
    ws.queue_replies({"type": "role_assigned", "role": "white", "room_id": "abc"})
    gate.send({"type": "create_room"})
    role_assigned = gate.wait_for("role_assigned")

    ws.queue_replies({"type": "state", "snapshot": "x"})
    gate.send({"type": "noop"})
    state = gate.wait_for("state")

    assert role_assigned["room_id"] == "abc"
    assert state["snapshot"] == "x"
