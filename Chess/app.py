"""Entry point for the board parsing program."""

from __future__ import annotations

from core.engine.game_engine import GameEngine
from core.ioutils.board_parser import read_input, parse_commands, parse_command, TextBoardParser
from config import BOARD_FORMAT


def _create_parser():
    # Controlled by BOARD_FORMAT in config.py to support future binary board format
    if BOARD_FORMAT == "text":
        return TextBoardParser()
    raise ValueError(f"Unsupported board format: {BOARD_FORMAT}")


def _run_commands(engine: GameEngine, commands: list[str]) -> None:
    for command in commands:
        parsed = parse_command(command)
        if parsed is not None:
            parsed.execute(engine)


def main() -> None:
    """Run the board interaction program from standard input."""
    board_input = read_input()
    try:
        parser = _create_parser()
        _run_commands(GameEngine.from_board(parser.parse(board_input)), parse_commands(board_input))
    except ValueError as error:
        print(f"ERROR {error}")


if __name__ == "__main__":
    main()
