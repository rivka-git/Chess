"""Tests for the board module."""

from model.board import Board


def test_board_can_be_instantiated() -> None:
    board = Board([["r", "n", "b"], ["p", ".", "p"]])
    assert isinstance(board, Board)
