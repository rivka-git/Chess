"""Parser utilities for simple board fixtures."""

from __future__ import annotations

from board import Board

VALID_TOKENS = {".", "wK", "bK", "wQ", "bQ", "wR", "bR", "wB", "bB", "wN", "bN", "wP", "bP"}


def parse_board(board_string: str) -> Board:
    """Parse a text board fixture into a Board instance.

    The platform provides input in the form:
    Board:
    <rows>
    Commands:
    <optional commands>

    This parser extracts the board section, validates its cells, and returns a
    board object ready to print back in its original row/column layout.
    """
    if not board_string or not board_string.strip():
        raise ValueError("Board input cannot be empty.")

    lines = [line.rstrip() for line in board_string.splitlines()]
    board_lines: list[str] = []
    in_board = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line == "Board:":
            in_board = True
            continue

        if line == "Commands:":
            break

        if in_board:
            board_lines.append(line)

    if not board_lines:
        raise ValueError("Board input cannot be empty.")

    board_rows: list[list[str]] = []
    for line in board_lines:
        parts = line.split()
        if not parts:
            continue

        normalized_parts: list[str] = []
        for part in parts:
            if part in VALID_TOKENS:
                normalized_parts.append(part)
            elif part == ".":
                normalized_parts.append(part)
            else:
                raise ValueError("UNKNOWN_TOKEN")

        board_rows.append(normalized_parts)

    return Board(board_rows)
