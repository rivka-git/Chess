"""Entry point for the board parsing program."""

from __future__ import annotations

import sys

from parser import parse_board


if __name__ == "__main__":
    board_input = sys.stdin.read()
    try:
        board = parse_board(board_input)
        print(board.to_canonical_string())
    except ValueError as error:
        print(f"ERROR {error}")
