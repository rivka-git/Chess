"""Entry point for the board parsing program."""

from __future__ import annotations

import sys

from engine.game_engine import GameEngine, GameEndDetector
from ioutils.board_parser import parse_board, parse_commands
from rules.rule_engine import MovementRules, MoveExecutor
from realtime.motion import GameTimer
from realtime.real_time_arbiter import CollisionResolver


def main() -> None:
    """Run the board interaction program from standard input."""
    board_input = sys.stdin.read()
    try:
        board = parse_board(board_input)
        game_timer = GameTimer()
        engine = GameEngine(
            rows=[list(row) for row in board.rows],
            movement_rules=MovementRules(),
            move_executor=MoveExecutor(),
            game_timer=game_timer,
            collision_resolver=CollisionResolver(),
            game_end_detector=GameEndDetector(),
        )
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
