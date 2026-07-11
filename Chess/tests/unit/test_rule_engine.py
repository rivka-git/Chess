"""Unit tests for rules.rule_engine."""

from model.board import Board
from rules.rule_engine import MovementRules, MoveExecutor, PawnPromoter


def make_board(rows):
    return Board(rows)


# --- MovementRules ---

def test_is_legal_move_same_start_end():
    rules = MovementRules()
    board = make_board([["wK", "."]])
    assert not rules.is_legal_move(board, (0, 0), (0, 0))


def test_is_legal_move_same_color_blocked():
    rules = MovementRules()
    board = make_board([["wK", "wR"]])
    assert not rules.is_legal_move(board, (0, 0), (0, 1))


def test_is_legal_move_unknown_piece():
    rules = MovementRules()
    board = make_board([[".", "."]])
    board.rows[0][0] = "wX"
    assert not rules.is_legal_move(board, (0, 0), (0, 1))


def test_is_same_color_true():
    assert MovementRules().is_same_color("wK", "wR")


def test_is_same_color_false():
    assert not MovementRules().is_same_color("wK", "bR")


def test_is_same_color_with_empty():
    assert not MovementRules().is_same_color("wK", ".")


# --- MoveExecutor ---

def test_apply_move_moves_piece():
    board = make_board([["wK", "."]])
    MoveExecutor().apply_move(board, (0, 0), (0, 1))
    assert board.rows[0][0] == "."
    assert board.rows[0][1] == "wK"


def test_apply_move_captures_enemy():
    board = make_board([["wR", "bK"]])
    MoveExecutor().apply_move(board, (0, 0), (0, 1))
    assert board.rows[0][1] == "wR"


# --- PawnPromoter ---

def test_white_pawn_promotes():
    board = make_board([["wP", "."], [".", "."]])
    PawnPromoter().promote_pawns(board, (1, 0), (0, 0))
    assert board.rows[0][0] == "wQ"


def test_black_pawn_promotes():
    board = make_board([[".", "."], ["bP", "."]])
    PawnPromoter().promote_pawns(board, (0, 0), (1, 0))
    assert board.rows[1][0] == "bQ"


def test_no_promotion_mid_board():
    board = make_board([[".", "."], ["wP", "."], [".", "."]])
    PawnPromoter().promote_pawns(board, (2, 0), (1, 0))
    assert board.rows[1][0] == "wP"


def test_game_end_detector_no_king_captured():
    from engine.game_engine import GameEndDetector
    board = make_board([["wK", "bK"]])
    assert not GameEndDetector().is_game_over(board)


def test_game_end_detector_king_captured():
    from engine.game_engine import GameEndDetector
    board = make_board([["wK", "."]])
    assert GameEndDetector().is_game_over(board)


