"""Tests for the board module."""

from board import Board


def test_board_can_be_instantiated() -> None:
    """A trivial test that confirms a board can be created from rows."""
    board = Board(["rnb", "p.p"])
    assert isinstance(board, Board)
