"""Entry point for the board parsing program."""

from __future__ import annotations

import sys

from engine.game_engine import GameEngine
from ioutils.board_parser import parse_board, parse_commands


def main() -> None:
    """Run the board interaction program from standard input."""
    board_input = sys.stdin.read()
    try:
        board = parse_board(board_input)
        engine = GameEngine([list(row) for row in board.rows])
        commands = parse_commands(board_input)

        for command in commands:
            parts = command.split()
            if not parts:
                continue

            if parts[0] == "click" and len(parts) == 3:
                engine.click(int(parts[1]), int(parts[2]))
            elif parts[0] == "jump" and len(parts) == 3:
                engine.jump(int(parts[1]), int(parts[2]))
            elif parts[0] == "wait" and len(parts) == 2:
                engine.wait(int(parts[1]))
            elif parts[0] == "print" and len(parts) == 2 and parts[1] == "board":
                print(engine.print_board())

    except ValueError as error:
        print(f"ERROR {error}")


if __name__ == "__main__":
    main()
