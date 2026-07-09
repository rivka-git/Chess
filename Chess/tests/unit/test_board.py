"""Unit tests for model.Board."""

import pytest
from model.board import Board


def test_board_stores_rows():
    board = Board([["wK", "."], [".", "bK"]])
    assert board.rows == [["wK", "."], [".", "bK"]]


def test_board_dimensions():
    board = Board([["wK", ".", "."], [".", ".", "."]])
    assert board.height == 2
    assert board.width == 3


def test_board_to_canonical_string():
    board = Board([["wK", "."], [".", "bK"]])
    assert board.to_canonical_string() == "wK .\n. bK"


def test_board_rejects_empty():
    with pytest.raises(ValueError):
        Board([])


def test_board_rejects_empty_rows():
    with pytest.raises(ValueError):
        Board([[]])


def test_board_rejects_row_width_mismatch():
    with pytest.raises(ValueError, match="ROW_WIDTH_MISMATCH"):
        Board([["wK", "."], ["."]])


def test_board_rejects_zero_width_row():
    with pytest.raises(ValueError):
        Board([[], []])


def test_board_filters_empty_rows():
    board = Board([["wK", "."], [".", "bK"]])
    assert board.height == 2
