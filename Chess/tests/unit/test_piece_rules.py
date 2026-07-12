"""Unit tests for rules.piece_rules - each piece in isolation."""

import pytest
from model.board import Board
from model.piece import King, Queen, Rook, Bishop, Knight, Pawn, Piece


def make_board(rows):
    return Board(rows)


# --- King ---

def test_king_moves_one_step_horizontal():
    assert King("w").is_legal_move(make_board([["wK", "."]]), (0, 0), (0, 1))


def test_king_moves_one_step_vertical():
    assert King("w").is_legal_move(make_board([["wK"], ["."]]), (0, 0), (1, 0))


def test_king_moves_one_step_diagonal():
    assert King("w").is_legal_move(make_board([["wK", "."], [".", "."]]), (0, 0), (1, 1))


def test_king_cannot_move_two_steps():
    assert not King("w").is_legal_move(make_board([["wK", ".", "."]]), (0, 0), (0, 2))


# --- Rook ---

def test_rook_moves_horizontally():
    assert Rook("w").is_legal_move(make_board([["wR", ".", "."]]), (0, 0), (0, 2))


def test_rook_moves_vertically():
    assert Rook("w").is_legal_move(make_board([["wR"], ["."], ["."]]), (0, 0), (2, 0))


def test_rook_cannot_move_diagonally():
    assert not Rook("w").is_legal_move(make_board([["wR", "."], [".", "."]]), (0, 0), (1, 1))


def test_rook_blocked_by_piece():
    assert not Rook("w").is_legal_move(make_board([["wR", "bP", "."]]), (0, 0), (0, 2))


# --- Bishop ---

def test_bishop_moves_diagonally():
    assert Bishop("w").is_legal_move(make_board([["wB", "."], [".", "."]]), (0, 0), (1, 1))


def test_bishop_cannot_move_straight():
    assert not Bishop("w").is_legal_move(make_board([["wB", "."]]), (0, 0), (0, 1))


def test_bishop_blocked_by_piece():
    assert not Bishop("w").is_legal_move(
        make_board([["wB", ".", "."], [".", "bP", "."], [".", ".", "."]]),
        (0, 0), (2, 2)
    )


# --- Knight ---

def test_knight_moves_in_l_shape():
    assert Knight("w").is_legal_move(
        make_board([["wN", ".", "."], [".", ".", "."], [".", ".", "."]]),
        (0, 0), (1, 2)
    )


def test_knight_cannot_move_straight():
    assert not Knight("w").is_legal_move(
        make_board([["wN", "."]]), (0, 0), (0, 1)
    )


# --- Queen ---

def test_queen_moves_straight():
    assert Queen("w").is_legal_move(make_board([["wQ", ".", "."]]), (0, 0), (0, 2))


def test_queen_moves_diagonally():
    assert Queen("w").is_legal_move(make_board([["wQ", "."], [".", "."]]), (0, 0), (1, 1))


def test_queen_blocked_by_piece():
    assert not Queen("w").is_legal_move(make_board([["wQ", "bP", "."]]), (0, 0), (0, 2))


# --- Pawn ---

def test_pawn_moves_forward_white():
    assert Pawn("w").is_legal_move(make_board([[".", "."], ["wP", "."]]), (1, 0), (0, 0))


def test_pawn_moves_forward_black():
    assert Pawn("b").is_legal_move(make_board([["bP", "."], [".", "."]]), (0, 0), (1, 0))


def test_pawn_cannot_move_backward():
    assert not Pawn("w").is_legal_move(make_board([[".", "."], ["wP", "."]]), (0, 0), (1, 0))


def test_pawn_captures_diagonally():
    assert Pawn("w").is_legal_move(make_board([[".", "bP"], ["wP", "."]]), (1, 0), (0, 1))


def test_pawn_cannot_capture_forward():
    assert not Pawn("w").is_legal_move(make_board([["bP"], ["wP"]]), (1, 0), (0, 0))


def test_pawn_double_step_from_start():
    board = make_board([[".", "."], [".", "."], [".", "."], ["wP", "."]])
    assert Pawn("w").is_legal_move(board, (3, 0), (1, 0))


def test_pawn_double_step_blocked():
    board = make_board([[".", "."], [".", "."], ["bB", "."], ["wP", "."]])
    assert not Pawn("w").is_legal_move(board, (3, 0), (1, 0))


# --- Piece.from_token ---

def test_from_token_king():
    piece = Piece.from_token("wK")
    assert isinstance(piece, King)
    assert piece.color == "w"


def test_from_token_pawn():
    piece = Piece.from_token("bP")
    assert isinstance(piece, Pawn)
    assert piece.color == "b"


def test_piece_str():
    assert str(King("w")) == "wK"
    assert str(Pawn("b")) == "bP"


def test_rook_blocked_going_left():
    board = make_board([[".", "bP", "wR"]])
    assert not Rook("w").is_legal_move(board, (0, 2), (0, 0))


def test_bishop_blocked_going_up_left():
    board = make_board([[".", ".", "."], [".", "bP", "."], [".", ".", "wB"]])
    assert not Bishop("w").is_legal_move(board, (2, 2), (0, 0))


def test_bishop_blocked_going_down_right():
    board = make_board([["wB", ".", "."], [".", "bP", "."], [".", ".", "."]])
    assert not Bishop("w").is_legal_move(board, (0, 0), (2, 2))


def test_queen_blocked_going_up():
    board = make_board([["."], ["bP"], ["wQ"]])
    assert not Queen("w").is_legal_move(board, (2, 0), (0, 0))


