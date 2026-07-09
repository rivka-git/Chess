"""Tests for the board parser."""

import pytest

from model.board import Board
from ioutils.board_parser import parse_board


def test_parse_board_with_piece_tokens() -> None:
    board = parse_board("Board:\nwK . . bK\n. . . .\nCommands:\nprint board")

    assert isinstance(board, Board)
    assert board.height == 2
    assert board.width == 4
    assert board.to_canonical_string() == "wK . . bK\n. . . ."


def test_parse_board_rejects_unknown_token() -> None:
    with pytest.raises(ValueError, match="UNKNOWN_TOKEN"):
        parse_board("Board:\nwK xZ\n. .\nCommands:")


def test_parse_board_rejects_row_width_mismatch() -> None:
    with pytest.raises(ValueError, match="ROW_WIDTH_MISMATCH"):
        parse_board("Board:\nwK . .\n. bK\nCommands:")


def test_parse_board_no_board_section():
    import pytest
    with pytest.raises(ValueError):
        parse_board("Commands:\nprint board")


def test_parse_board_empty_string():
    with pytest.raises(ValueError):
        parse_board("")


def test_parse_commands_empty_string():
    from ioutils.board_parser import parse_commands
    assert parse_commands("") == []


def test_parse_commands_no_commands_section():
    from ioutils.board_parser import parse_commands
    assert parse_commands("Board:\nwK .\n") == []


def test_parse_board_skips_empty_lines_in_board_section():
    board = parse_board("Board:\n\nwK .\nCommands:")
    assert board.rows == [["wK", "."]]
