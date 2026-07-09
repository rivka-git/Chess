"""Parser utilities for simple board fixtures."""

from __future__ import annotations

from board import Board
from movement import PieceRegistry, MovementRules


def _extract_board_lines(board_string: str) -> list[str]:
    """Extract the raw text lines that belong to the Board section."""
    board_lines: list[str] = []
    in_board = False

    for raw_line in board_string.splitlines():
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

    return board_lines


def _parse_row(line: str, registry: PieceRegistry) -> list[str]:
    """Parse and validate a single board row, returning a list of tokens."""
    tokens = []
    for part in line.split():
        if part != "." and (len(part) != 2 or part[0] not in {"w", "b"} or part[1] not in registry.rules):
            raise ValueError("UNKNOWN_TOKEN")
        tokens.append(part)
    return tokens


def parse_board(board_string: str, registry: PieceRegistry | None = None) -> Board:
    """Parse a text board fixture into a Board instance."""
    if not board_string or not board_string.strip():
        raise ValueError("Board input cannot be empty.")

    board_lines = _extract_board_lines(board_string)

    if not board_lines:
        raise ValueError("Board input cannot be empty.")

    reg = registry or MovementRules()._build_default_registry()
    board_rows = [_parse_row(line, reg) for line in board_lines if line.split()]

    return Board(board_rows)


def parse_commands(board_string: str) -> list[str]:
    """Extract the command lines that follow the Commands section."""
    if not board_string or not board_string.strip():
        return []

    commands: list[str] = []
    in_commands = False

    for raw_line in board_string.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line == "Commands:":
            in_commands = True
            continue

        if in_commands:
            commands.append(line)

    return commands
