"""Entry point for the board parsing program."""

from __future__ import annotations

from engine.game_engine import GameEngine, GameEndDetector
from ioutils.board_parser import read_input, parse_board, parse_commands, parse_command
from rules.rule_engine import MovementRules, MoveExecutor
from realtime.motion import GameTimer
from realtime.real_time_arbiter import CollisionResolver


def _build_engine(board_input: str) -> GameEngine:
    board = parse_board(board_input)
    return GameEngine(
        rows=[list(row) for row in board.rows],
        movement_rules=MovementRules(),
        move_executor=MoveExecutor(),
        game_timer=GameTimer(),
        collision_resolver=CollisionResolver(),
        game_end_detector=GameEndDetector(),
    )


def _run_commands(engine: GameEngine, commands: list[str]) -> None:
    for command in commands:
        parsed = parse_command(command)
        if parsed is None:
            continue
        name, args = parsed
        if name == "click":
            engine.click(*args)
        elif name == "jump":
            engine.jump(*args)
        elif name == "wait":
            engine.wait(*args)
        elif name == "print":
            print(engine.print_board())


def main() -> None:
    """Run the board interaction program from standard input."""
    board_input = read_input()
    try:
        _run_commands(_build_engine(board_input), parse_commands(board_input))
    except ValueError as error:
        print(f"ERROR {error}")


if __name__ == "__main__":
    main()
