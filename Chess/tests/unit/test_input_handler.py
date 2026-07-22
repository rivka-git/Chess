"""Unit tests for input.input_handler."""

from core.model.board import Board
from core.realtime.motion import GameTimer
from core.rules.rule_engine import MovementRules
from input.input_handler import InputHandler


def make_handler():
    return InputHandler(GameTimer(), MovementRules())


def test_click_selects_piece():
    handler = make_handler()
    board = Board([["wK", "."]])
    handler.handle_click(board, 0, 0, lambda s, e: None)
    assert handler.selected_position == (0, 0)


def test_click_outside_board_clears_selection():
    handler = make_handler()
    board = Board([["wK", "."]])
    handler.selected_position = (0, 0)
    handler.handle_click(board, 99, 99, lambda s, e: None)
    assert handler.selected_position is None


def test_click_empty_cell_does_not_select():
    handler = make_handler()
    board = Board([[".", "wK"]])
    handler.handle_click(board, 0, 0, lambda s, e: None)
    assert handler.selected_position is None


def test_second_click_on_own_piece_switches_selection():
    handler = make_handler()
    board = Board([["wK", "wR"]])
    handler.handle_click(board, 0, 0, lambda s, e: None)
    handler.handle_click(board, 0, 1, lambda s, e: None)
    assert handler.selected_position == (0, 1)


def test_second_click_requests_move():
    handler = make_handler()
    board = Board([["wK", "."]])
    moves = []
    handler.handle_click(board, 0, 0, lambda s, e: None)
    handler.handle_click(board, 0, 1, lambda s, e: moves.append((s, e)))
    assert len(moves) == 1


def test_jump_on_empty_cell_ignored():
    handler = make_handler()
    board = Board([[".", "wR"]])
    jumps = []
    handler.handle_jump(board, 0, 0, lambda p: jumps.append(p))
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
    handler.handle_jump(board, 0, 0, lambda p: jumps.append(p))
    assert jumps == []


def test_second_click_illegal_move_clears_selection():
    handler = make_handler()
    board = Board([["wR", "."], [".", "."]])
    handler.handle_click(board, 0, 0, lambda s, e: None)
    handler.handle_click(board, 1, 1, lambda s, e: None)
    assert handler.selected_position is None


def test_legal_move_blocked_while_pending():
    timer = GameTimer()
    handler = InputHandler(timer, MovementRules())
    board = Board([["wK", ".", "."]])
    timer.add_move((0, 0), (0, 2), "wK")
    moves = []
    handler.selected_position = (0, 0)
    handler.handle_click(board, 0, 1, lambda s, e: moves.append((s, e)))
    assert moves == []


# --- Color-scoped selection (networked multiplayer: two independent players,
# each restricted to their own pieces, sharing one InputHandler) ---

def test_color_none_still_uses_shared_selected_position():
    handler = make_handler()
    board = Board([["wK", "."]])
    handler.handle_click(board, 0, 0, lambda s, e: None)
    assert handler.selected_position == (0, 0)
    assert handler.selection_for(None) == (0, 0)


def test_click_selects_own_piece_when_color_given():
    handler = make_handler()
    board = Board([["wK", "bK"]])
    handler.handle_click(board, 0, 0, lambda s, e: None, color="w")
    assert handler.selection_for("w") == (0, 0)


def test_click_rejects_opponent_piece_when_color_given():
    handler = make_handler()
    board = Board([["wK", "bK"]])
    handler.handle_click(board, 0, 0, lambda s, e: None, color="b")
    assert handler.selection_for("b") is None


def test_color_scoped_selection_independent_per_color():
    handler = make_handler()
    board = Board([["wK", "bK"]])
    handler.handle_click(board, 0, 0, lambda s, e: None, color="w")
    handler.handle_click(board, 0, 1, lambda s, e: None, color="b")
    assert handler.selection_for("w") == (0, 0)
    assert handler.selection_for("b") == (0, 1)


def test_second_click_own_color_still_requests_move():
    handler = make_handler()
    board = Board([["wK", "."]])
    moves = []
    handler.handle_click(board, 0, 0, lambda s, e: None, color="w")
    handler.handle_click(board, 0, 1, lambda s, e: moves.append((s, e)), color="w")
    assert moves == [((0, 0), (0, 1))]
    assert handler.selection_for("w") is None


def test_jump_allows_own_piece_when_color_given():
    handler = make_handler()
    board = Board([["wR", "bR"]])
    jumps = []
    handler.handle_jump(board, 0, 0, lambda p: jumps.append(p), color="w")
    assert jumps == [(0, 0)]


def test_jump_rejects_opponent_piece_when_color_given():
    handler = make_handler()
    board = Board([["wR", "bR"]])
    jumps = []
    handler.handle_jump(board, 0, 1, lambda p: jumps.append(p), color="w")
    assert jumps == []
