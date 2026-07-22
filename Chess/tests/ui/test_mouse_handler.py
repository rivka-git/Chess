"""MouseHandler is the seam where screen pixels become board cells, so these
tests pin the conversion: everything downstream of it must receive (row, col)."""

import cv2
import pytest

from controls.mouse_handler import MouseHandler

CELL = 100


class FakeWindow:
    def __init__(self):
        self.callback = None

    def set_mouse_callback(self, callback):
        self.callback = callback


class FakeController:
    def __init__(self):
        self.moves = []
        self.jumps = []

    def move(self, row, col):
        self.moves.append((row, col))

    def jump(self, row, col):
        self.jumps.append((row, col))


@pytest.fixture
def wired():
    window, controller = FakeWindow(), FakeController()
    MouseHandler(window, controller, CELL)
    return window, controller


def test_left_click_converts_pixels_to_row_col(wired):
    window, controller = wired
    window.callback(cv2.EVENT_LBUTTONDOWN, 150, 250, 0, None)
    assert controller.moves == [(2, 1)]
    assert controller.jumps == []


def test_right_click_converts_pixels_to_row_col(wired):
    window, controller = wired
    window.callback(cv2.EVENT_RBUTTONDOWN, 150, 250, 0, None)
    assert controller.jumps == [(2, 1)]
    assert controller.moves == []


def test_click_at_cell_origin_and_cell_interior_map_to_same_cell(wired):
    window, controller = wired
    window.callback(cv2.EVENT_LBUTTONDOWN, 100, 100, 0, None)
    window.callback(cv2.EVENT_LBUTTONDOWN, 199, 199, 0, None)
    assert controller.moves == [(1, 1), (1, 1)]


def test_mouse_move_is_ignored(wired):
    window, controller = wired
    window.callback(cv2.EVENT_MOUSEMOVE, 150, 250, 0, None)
    assert controller.moves == []
    assert controller.jumps == []


def test_cell_size_is_honored():
    window, controller = FakeWindow(), FakeController()
    MouseHandler(window, controller, 50)
    window.callback(cv2.EVENT_LBUTTONDOWN, 150, 250, 0, None)
    assert controller.moves == [(5, 3)]
