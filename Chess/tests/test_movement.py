"""Tests for basic piece movement rules."""

from controller import Controller


def test_king_can_move_one_step() -> None:
    controller = Controller([["wK", "."], [".", "."]])

    controller.click(50, 50)
    controller.click(150, 50)

    assert controller.board.rows[0][1] == "wK"


def test_king_cannot_move_two_steps() -> None:
    controller = Controller([["wK", ".", "."], [".", ".", "."]])

    controller.click(50, 50)
    controller.click(250, 50)

    assert controller.board.rows[0][0] == "wK"
    assert controller.board.rows[0][2] == "."


def test_rook_cannot_move_diagonally() -> None:
    controller = Controller([["wR", ".", "."], [".", ".", "."]])

    controller.click(50, 50)
    controller.click(150, 150)

    assert controller.board.rows[0][0] == "wR"
    assert controller.board.rows[1][1] == "."


def test_knight_can_move_in_l_shape() -> None:
    controller = Controller([["wN", ".", "."], [".", ".", "."], [".", ".", "."]])

    controller.click(50, 50)
    controller.click(250, 150)

    assert controller.board.rows[1][2] == "wN"


def test_rook_cannot_move_through_blocker() -> None:
    controller = Controller([["wR", "bB", "."]])

    controller.click(50, 50)
    controller.click(250, 50)

    assert controller.board.rows[0][0] == "wR"
    assert controller.board.rows[0][1] == "bB"
    assert controller.board.rows[0][2] == "."


def test_rook_can_capture_enemy_piece_on_destination() -> None:
    controller = Controller([["wR", ".", "bB"]])

    controller.click(50, 50)
    controller.click(250, 50)

    assert controller.board.rows[0][0] == "."
    assert controller.board.rows[0][2] == "wR"
