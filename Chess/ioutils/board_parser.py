"""Parser utilities for simple board fixtures."""

from __future__ import annotations

import sys

from model.board import Board
from rules.rule_engine import PieceRegistry, MovementRules


def _extract_board_lines(board_string: str) -> list[str]:
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
    tokens = []
    for part in line.split():
        if part != "." and (len(part) != 2 or part[0] not in {"w", "b"} or part[1] not in registry.rules):
            raise ValueError("UNKNOWN_TOKEN")
        tokens.append(part)
    return tokens


def parse_board(board_string: str, registry: PieceRegistry | None = None) -> Board:
    if not board_string or not board_string.strip():
        raise ValueError("Board input cannot be empty.")

    board_lines = _extract_board_lines(board_string)

    if not board_lines:
        raise ValueError("Board input cannot be empty.")

    reg = registry or MovementRules()._build_default_registry()
    board_rows = [_parse_row(line, reg) for line in board_lines if line.split()]

    return Board(board_rows)


def read_input() -> str:
    return sys.stdin.read()


def parse_command(command: str) -> tuple[str, list[int]] | None:
    parts = command.split()
    if not parts:
        return None
    if parts[0] in {"click", "jump"} and len(parts) == 3:
        return parts[0], [int(parts[1]), int(parts[2])]
    if parts[0] == "wait" and len(parts) == 2:
        return parts[0], [int(parts[1])]
    if parts[0] == "print" and len(parts) == 2 and parts[1] == "board":
        return parts[0], []
    return None


def parse_commands(board_string: str) -> list[str]:
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
