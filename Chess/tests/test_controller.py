"""Tests for the controller behavior in iteration 2."""

from controller import Controller
from movement import MovementRules


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
