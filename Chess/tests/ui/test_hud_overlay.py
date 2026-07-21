"""Unit tests for render.hud_overlay."""

from render.hud_overlay import HudOverlay, overlay_from_controller


class FakeController:
    def __init__(self, room_id=None, opponent_left_seconds=None):
        self.room_id = room_id
        self.opponent_left_seconds = opponent_left_seconds


def test_overlay_from_none_controller_is_empty():
    overlay = overlay_from_controller(None)
    assert overlay == HudOverlay(room_id=None, countdown_seconds=None)


def test_overlay_reads_room_id_and_countdown():
    overlay = overlay_from_controller(FakeController(room_id="abc123", opponent_left_seconds=12))
    assert overlay.room_id == "abc123"
    assert overlay.countdown_seconds == 12


def test_overlay_tolerates_controller_without_the_attributes():
    overlay = overlay_from_controller(object())
    assert overlay == HudOverlay(room_id=None, countdown_seconds=None)
