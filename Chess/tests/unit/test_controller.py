"""Tests for the controller behavior."""

import io
import sys
from unittest.mock import MagicMock

from core.engine.game_engine import GameEngine, GameEndDetector
from core.rules.rule_engine import MovementRules, MoveExecutor
from core.realtime.motion import GameTimer
from core.realtime.real_time_arbiter import CollisionResolver
import app


def make_engine(rows, **kwargs):
    defaults = dict(
        movement_rules=MovementRules(),
        move_executor=MoveExecutor(),
        game_timer=GameTimer(),
        collision_resolver=CollisionResolver(),
        game_end_detector=GameEndDetector(),
    )
    defaults.update(kwargs)
    return GameEngine(rows, **defaults)


def test_click_selects_friendly_piece() -> None:
    mock_rules = MagicMock(spec=MovementRules)
    engine = make_engine([["wK", "."], [".", "bR"]], movement_rules=mock_rules)
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(1000)
    assert engine.print_board() == ". wK\n. bR"


def test_click_on_empty_cell_requests_move() -> None:
    mock_rules = MagicMock(spec=MovementRules)
    mock_rules.is_legal_move.return_value = True
    mock_rules.is_same_color.return_value = False
    engine = make_engine([["wK", "."], [".", "bR"]], movement_rules=mock_rules)
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(1000)
    assert engine.print_board() == ". wK\n. bR"


def test_click_outside_board_is_ignored() -> None:
    mock_rules = MagicMock(spec=MovementRules)
    engine = make_engine([["wK", "."], [".", "bR"]], movement_rules=mock_rules)
    engine.click(10, 10)
    assert engine.print_board() == "wK .\n. bR"


def test_jump_ignored_after_game_over():
    mock_detector = MagicMock(spec=GameEndDetector)
    mock_detector.is_game_over.return_value = True
    engine = make_engine([["wR", "bK", "."]], game_end_detector=mock_detector)
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(1000)
    board_before = engine.print_board()
    engine.jump(0, 2)
    assert engine.print_board() == board_before


def test_controller_accepts_injected_movement_rules() -> None:
    movement_rules = MovementRules()
    engine = make_engine([["wK", "."], [".", "bR"]], movement_rules=movement_rules)
    assert engine.movement_rules is movement_rules


def test_game_over_detected_via_mock_end_detector() -> None:
    mock_detector = MagicMock(spec=GameEndDetector)
    mock_detector.is_game_over.return_value = True
    engine = make_engine([["wR", "bK"]], game_end_detector=mock_detector)
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(1000)
    assert engine.game_over


def test_collision_resolver_called_via_mock() -> None:
    mock_resolver = MagicMock(spec=CollisionResolver)
    mock_resolver.resolve_collisions.return_value = []
    engine = make_engine([["wR", "."]], collision_resolver=mock_resolver)
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(1000)
    mock_resolver.resolve_collisions.assert_called_once()


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
