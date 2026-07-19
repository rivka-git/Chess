"""Unit tests for adapter.controller.Controller's color/viewer_color support
(added so two independent network players can share one board without
seeing or clobbering each other's selection)."""

from adapter.controller import Controller
from engine.game_engine import GameEngine
from ioutils.board_parser import TextBoardParser

SMALL_BOARD = """Board:
wK .
. bK
"""


def make_controller(board_text=SMALL_BOARD):
    board = TextBoardParser().parse(board_text)
    return Controller(GameEngine.from_board(board))


def test_get_snapshot_without_viewer_color_uses_shared_selection():
    controller = make_controller()
    controller.move(50, 50)  # select wK at (0,0), legacy no-color path
    snapshot = controller.get_snapshot()
    assert snapshot.selected_position == (0, 0)


def test_get_snapshot_per_viewer_color_diverges():
    controller = make_controller()
    controller.move(50, 50, color="w")    # select wK
    controller.move(150, 150, color="b")  # select bK

    white_view = controller.get_snapshot(viewer_color="w")
    black_view = controller.get_snapshot(viewer_color="b")

    assert white_view.selected_position == (0, 0)
    assert black_view.selected_position == (1, 1)


def test_opponent_piece_cannot_be_selected_via_controller():
    controller = make_controller()
    controller.move(150, 150, color="w")  # attempt to select black's king
    snapshot = controller.get_snapshot(viewer_color="w")
    assert snapshot.selected_position is None
