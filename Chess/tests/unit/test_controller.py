"""Tests for the controller behavior."""

import io
import sys

from engine.game_engine import GameEngine
from rules.rule_engine import MovementRules
import app


def test_click_selects_friendly_piece() -> None:
    engine = GameEngine([["wK", "."], [".", "bR"]])
    engine.click(50, 50)
    assert engine.selected_position == (0, 0)


def test_click_on_empty_cell_requests_move() -> None:
    engine = GameEngine([["wK", "."], [".", "bR"]])
    engine.click(50, 50)
    engine.click(150, 50)
    assert engine.selected_position is None
    assert len(engine.pending_moves) == 1


def test_click_outside_board_is_ignored() -> None:
    engine = GameEngine([["wK", "."], [".", "bR"]])
    engine.click(1000, 1000)
    assert engine.selected_position is None
    assert engine.pending_moves == []


def test_jump_ignored_after_game_over():
    engine = GameEngine([["wR", "bK", "."]])
    engine.click(50, 50)
    engine.click(150, 50)
    engine.wait(1000)
    engine.jump(250, 50)
    assert engine.airborne == []


def test_controller_accepts_injected_movement_rules() -> None:
    movement_rules = MovementRules()
    engine = GameEngine([["wK", "."], [".", "bR"]], movement_rules=movement_rules)
    assert engine.movement_rules is movement_rules


def test_main_function_processes_board_input(monkeypatch: object, capsys: object) -> None:
    board_input = """Board:
wR wP .
Commands:
click 50 50
click 250 50
wait 1000
print board
"""
    monkeypatch.setattr(sys, "stdin", io.StringIO(board_input))
    app.main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "wR wP ."


def test_main_jump_command(monkeypatch, capsys):
    board_input = """Board:
wR . .
Commands:
jump 50 50
wait 1000
print board
"""
    monkeypatch.setattr(sys, "stdin", io.StringIO(board_input))
    app.main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "wR . ."


def test_main_invalid_board_prints_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    app.main()
    captured = capsys.readouterr()
    assert captured.out.startswith("ERROR")


def test_main_empty_command_ignored(monkeypatch, capsys):
    board_input = "Board:\nwK .\nCommands:\n\nprint board\n"
    monkeypatch.setattr(sys, "stdin", io.StringIO(board_input))
    app.main()
    captured = capsys.readouterr()
    assert "wK" in captured.out
