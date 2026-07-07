"""Tests for the parser module."""

import pytest

from board import Board
from parser import parse_board


def test_parse_board_with_piece_tokens() -> None:
    """Piece tokens such as wK and bQ should be preserved as single cells."""
    board = parse_board("Board:\nwK . . bK\n. . . .\nCommands:\nprint board")

    assert isinstance(board, Board)
    assert board.height == 2
    assert board.width == 4
    assert board.to_canonical_string() == "wK . . bK\n. . . ."


def test_parse_board_rejects_unknown_token() -> None:
    """Unknown piece tokens should be rejected."""
    with pytest.raises(ValueError, match="UNKNOWN_TOKEN"):
        parse_board("Board:\nwK xZ\n. .\nCommands:")


def test_parse_board_rejects_row_width_mismatch() -> None:
    """Rows with different numbers of cells should be rejected."""
    with pytest.raises(ValueError, match="ROW_WIDTH_MISMATCH"):
        parse_board("Board:\nwK . .\n. bK\nCommands:")
