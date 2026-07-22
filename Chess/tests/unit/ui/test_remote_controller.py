"""Unit tests for network.remote_controller.RemoteController."""

from network.remote_controller import RemoteController


class FakeWsClient:
    """Stand-in for WsClient: no thread, no real socket."""

    def __init__(self):
        self.sent = []
        self._on_message = None

    def start(self, on_message):
        self._on_message = on_message

    def set_message_handler(self, on_message):
        self._on_message = on_message

    def send(self, message):
        self.sent.append(message)

    def close(self):
        pass

    def push(self, message):
        """Test helper: simulate a message arriving from the server."""
        self._on_message(message)


def test_move_sends_row_col_click():
    ws = FakeWsClient()
    controller = RemoteController(ws)
    controller.move(2, 1)
    assert ws.sent == [{"type": "move_click", "row": 2, "col": 1}]


def test_jump_sends_row_col_jump():
    ws = FakeWsClient()
    controller = RemoteController(ws)
    controller.jump(0, 0)
    assert ws.sent == [{"type": "jump_click", "row": 0, "col": 0}]


def test_update_is_a_noop():
    ws = FakeWsClient()
    controller = RemoteController(ws)
    controller.update(16.0)
    assert ws.sent == []


def test_get_snapshot_before_any_state_message_is_empty():
    ws = FakeWsClient()
    controller = RemoteController(ws)
    snapshot = controller.get_snapshot()
    assert snapshot.board == []
    assert snapshot.game_over is False


def test_state_message_updates_cached_snapshot():
    ws = FakeWsClient()
    controller = RemoteController(ws)
    ws.push({
        "type": "state",
        "snapshot": {
            "clock": 1000.0,
            "board": [[{"token": "wK", "row": 0, "col": 0, "cooldown_until": 0.0}, None]],
            "pending_moves": [],
            "jumps": [],
            "selected_position": [0, 0],
            "legal_targets": [[0, 1]],
            "game_over": False,
        },
    })
    snapshot = controller.get_snapshot()
    assert snapshot.clock == 1000.0
    assert snapshot.board[0][0].token == "wK"
    assert snapshot.board[0][1] is None
    assert snapshot.selected_position == (0, 0)
    assert snapshot.legal_targets == [(0, 1)]


def test_role_assigned_message_sets_role_and_room():
    ws = FakeWsClient()
    controller = RemoteController(ws)
    ws.push({"type": "role_assigned", "role": "white", "room_id": "default"})
    assert controller.role == "white"
    assert controller.room_id == "default"
