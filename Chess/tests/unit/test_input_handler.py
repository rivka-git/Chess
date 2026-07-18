"""Unit tests for input.input_handler."""

from model.board import Board
from realtime.motion import GameTimer
from rules.rule_engine import MovementRules
from input.input_handler import InputHandler


def make_handler():
    return InputHandler(GameTimer(), MovementRules())


def test_click_selects_piece():
    handler = make_handler()
    board = Board([["wK", "."]])
    handler.handle_click(board, 50, 50, lambda s, e: None)
    assert handler.selected_position == (0, 0)


def test_click_outside_board_clears_selection():
    handler = make_handler()
    board = Board([["wK", "."]])
    handler.selected_position = (0, 0)
    handler.handle_click(board, 9999, 9999, lambda s, e: None)
    assert handler.selected_position is None


def test_click_empty_cell_does_not_select():
    handler = make_handler()
    board = Board([[".", "wK"]])
    handler.handle_click(board, 50, 50, lambda s, e: None)
    assert handler.selected_position is None


def test_second_click_on_own_piece_switches_selection():
    handler = make_handler()
    board = Board([["wK", "wR"]])
    handler.handle_click(board, 50, 50, lambda s, e: None)
    handler.handle_click(board, 150, 50, lambda s, e: None)
    assert handler.selected_position == (0, 1)


def test_second_click_requests_move():
    handler = make_handler()
    board = Board([["wK", "."]])
    moves = []
    handler.handle_click(board, 50, 50, lambda s, e: None)
    handler.handle_click(board, 150, 50, lambda s, e: moves.append((s, e)))
    assert len(moves) == 1


def test_jump_on_empty_cell_ignored():
    handler = make_handler()
    board = Board([[".", "wR"]])
    jumps = []
    handler.handle_jump(board, 50, 50, lambda p: jumps.append(p))
    assert jumps == []


def test_jump_on_piece_in_transit_ignored():
    timer = GameTimer()
    handler = InputHandler(timer, MovementRules())
    board = Board([["wR", "."]])
    timer.add_move((0, 0), (0, 1), "wR")
    timer = GameTimer()
    handler = InputHandler(timer, MovementRules())
    board = Board([["wR", "."]])
    timer.add_airborne((0, 0))
    jumps = []
    handler.handle_jump(board, 50, 50, lambda p: jumps.append(p))
    assert jumps == []


def test_second_click_illegal_move_clears_selection():
    handler = make_handler()
    board = Board([["wR", "."], [".", "."]])
    handler.handle_click(board, 50, 50, lambda s, e: None)
    handler.handle_click(board, 150, 150, lambda s, e: None)
    assert handler.selected_position is None


def test_legal_move_blocked_while_pending():
    timer = GameTimer()
    handler = InputHandler(timer, MovementRules())
    board = Board([["wK", ".", "."]])
    timer.add_move((0, 0), (0, 2), "wK")
    moves = []
    handler.selected_position = (0, 0)
    handler.handle_click(board, 150, 50, lambda s, e: moves.append((s, e)))
    assert moves == []
