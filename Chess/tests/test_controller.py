"""Tests for the controller behavior in iteration 2."""

import io
import sys

from controller import Controller
from movement import MovementRules
import main


def test_click_selects_friendly_piece() -> None:
    """A click on a piece should select it."""
    controller = Controller([["wK", "."], [".", "bR"]])

    controller.click(50, 50)

    assert controller.selected_position == (0, 0)


def test_click_on_empty_cell_requests_move() -> None:
    """A click on an empty cell after selecting a piece should queue a move request."""
    controller = Controller([["wK", "."], [".", "bR"]])

    controller.click(50, 50)
    controller.click(150, 50)

    assert controller.selected_position is None
    assert controller.pending_moves == [((0, 0), (0, 1))]


def test_click_outside_board_is_ignored() -> None:
    """Clicks outside the board should not change the controller state."""
    controller = Controller([["wK", "."], [".", "bR"]])

    controller.click(1000, 1000)

    assert controller.selected_position is None
    assert controller.pending_moves == []


def test_controller_accepts_injected_movement_rules() -> None:
    """The controller should be able to use movement rules provided by the caller."""
    movement_rules = MovementRules()
    controller = Controller([["wK", "."], [".", "bR"]], movement_rules=movement_rules)

    assert controller.movement_rules is movement_rules


def test_main_function_processes_board_input(monkeypatch: object, capsys: object) -> None:
    """The main entry point should process board input and print the board output."""
    board_input = """Board:
wR wP .
Commands:
click 50 50
click 250 50
wait 2000
print board
"""

    monkeypatch.setattr(sys, "stdin", io.StringIO(board_input))
    main.main()

    captured = capsys.readouterr()
    assert captured.out.strip() == "wR wP ."
