"""Unit tests for network.home_flow.run_home_flow -- the UI-agnostic flow,
driven here by a scripted fake frontend and a scripted fake gate."""

from network.home_flow import run_home_flow


class FakeGate:
    """Returns the queued replies in order; asserts each is one the flow asked
    for so a wrong ordering fails loudly instead of silently."""

    def __init__(self, replies):
        self.sent = []
        self._replies = list(replies)

    def send(self, message):
        self.sent.append(message)

    def wait_for(self, *types):
        reply = self._replies.pop(0)
        assert reply["type"] in types, (reply, types)
        return reply


class FakeFrontend:
    def __init__(self, credentials, actions, room_action=None):
        self._credentials = list(credentials)
        self._actions = list(actions)
        self._room_action = room_action
        self.errors = []
        self.logged_in = None
        self.room_created = None
        self.searched = False
        self.shown_history = None

    def get_credentials(self):
        return self._credentials.pop(0)

    def on_logged_in(self, username, rating):
        self.logged_in = (username, rating)

    def choose_action(self):
        return self._actions.pop(0)

    def on_searching(self):
        self.searched = True

    def get_room_action(self):
        return self._room_action

    def on_room_created(self, room_id):
        self.room_created = room_id

    def show_history(self, games):
        self.shown_history = games

    def show_error(self, message):
        self.errors.append(message)


def test_login_then_play_match_found_returns_true():
    gate = FakeGate([
        {"type": "login_ok", "rating": 1200},
        {"type": "searching_match"},
        {"type": "role_assigned", "role": "white", "room_id": "r1"},
        {"type": "state", "snapshot": {}},
    ])
    frontend = FakeFrontend(credentials=[("alice", "pw")], actions=["play"])

    assert run_home_flow(gate, frontend) is True
    assert frontend.logged_in == ("alice", 1200)
    assert frontend.searched
    assert {"type": "login", "username": "alice", "password": "pw"} in gate.sent
    assert {"type": "find_match"} in gate.sent


def test_login_retries_after_wrong_password():
    gate = FakeGate([
        {"type": "login_failed", "message": "Wrong password."},
        {"type": "login_ok", "rating": 1300},
        {"type": "role_assigned", "role": "white", "room_id": "r1"},
        {"type": "state", "snapshot": {}},
    ])
    frontend = FakeFrontend(
        credentials=[("alice", "bad"), ("alice", "good")],
        actions=["room"],
        room_action=("create", ""),
    )

    assert run_home_flow(gate, frontend) is True
    assert frontend.errors == ["Wrong password."]
    assert frontend.logged_in == ("alice", 1300)


def test_cancelling_credentials_aborts_the_flow():
    gate = FakeGate([])
    frontend = FakeFrontend(credentials=[None], actions=[])

    assert run_home_flow(gate, frontend) is False
    assert gate.sent == []


def test_play_no_match_shows_error_then_quit_returns_false():
    gate = FakeGate([
        {"type": "login_ok", "rating": 1200},
        {"type": "searching_match"},
        {"type": "no_match_found", "message": "timed out"},
    ])
    frontend = FakeFrontend(credentials=[("alice", "pw")], actions=["play", "quit"])

    assert run_home_flow(gate, frontend) is False
    assert any("opponent" in e.lower() for e in frontend.errors)


def test_room_create_reports_room_id():
    gate = FakeGate([
        {"type": "login_ok", "rating": 1200},
        {"type": "role_assigned", "role": "white", "room_id": "abc123"},
        {"type": "state", "snapshot": {}},
    ])
    frontend = FakeFrontend(
        credentials=[("alice", "pw")], actions=["room"], room_action=("create", ""),
    )

    assert run_home_flow(gate, frontend) is True
    assert frontend.room_created == "abc123"


def test_room_join_unknown_id_shows_error_then_quit():
    gate = FakeGate([
        {"type": "login_ok", "rating": 1200},
        {"type": "room_not_found", "message": "No room 'nope'."},
    ])
    frontend = FakeFrontend(
        credentials=[("alice", "pw")], actions=["room", "quit"], room_action=("join", "nope"),
    )

    assert run_home_flow(gate, frontend) is False
    assert any("room" in e.lower() for e in frontend.errors)


def test_history_action_fetches_games_then_stays_on_home():
    gate = FakeGate([
        {"type": "login_ok", "rating": 1200},
        {"type": "history", "games": [{"id": 1, "room_id": "r1"}]},
        {"type": "role_assigned", "role": "white", "room_id": "r2"},
        {"type": "state", "snapshot": {}},
    ])
    frontend = FakeFrontend(
        credentials=[("alice", "pw")], actions=["history", "room"], room_action=("create", ""),
    )

    assert run_home_flow(gate, frontend) is True
    assert frontend.shown_history == [{"id": 1, "room_id": "r1"}]
    assert {"type": "get_history"} in gate.sent


def test_room_join_success_returns_true():
    gate = FakeGate([
        {"type": "login_ok", "rating": 1200},
        {"type": "role_assigned", "role": "black", "room_id": "abc123"},
        {"type": "state", "snapshot": {}},
    ])
    frontend = FakeFrontend(
        credentials=[("bob", "pw")], actions=["room"], room_action=("join", "abc123"),
    )

    assert run_home_flow(gate, frontend) is True
    assert {"type": "join_room", "room_id": "abc123"} in gate.sent
