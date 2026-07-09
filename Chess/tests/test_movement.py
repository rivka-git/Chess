"""Tests for basic piece movement rules."""

from controller import Controller


def test_king_can_move_one_step() -> None:
    controller = Controller([["wK", "."], [".", "."]])

    controller.click(50, 50)
    controller.click(150, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][1] == "wK"


def test_king_cannot_move_two_steps() -> None:
    controller = Controller([["wK", ".", "."], [".", ".", "."]])

    controller.click(50, 50)
    controller.click(250, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][0] == "wK"
    assert controller.board.rows[0][2] == "."


def test_rook_cannot_move_diagonally() -> None:
    controller = Controller([["wR", ".", "."], [".", ".", "."]])

    controller.click(50, 50)
    controller.click(150, 150)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][0] == "wR"
    assert controller.board.rows[1][1] == "."


def test_knight_can_move_in_l_shape() -> None:
    controller = Controller([["wN", ".", "."], [".", ".", "."], [".", ".", "."]])

    controller.click(50, 50)
    controller.click(250, 150)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[1][2] == "wN"


def test_rook_cannot_move_through_blocker() -> None:
    controller = Controller([["wR", "bB", "."]])

    controller.click(50, 50)
    controller.click(250, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][0] == "wR"
    assert controller.board.rows[0][1] == "bB"
    assert controller.board.rows[0][2] == "."


def test_rook_can_capture_enemy_piece_on_destination() -> None:
    controller = Controller([["wR", ".", "bB"]])

    controller.click(50, 50)
    controller.click(250, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][0] == "."
    assert controller.board.rows[0][2] == "wR"


def test_white_pawn_moves_forward() -> None:
    controller = Controller([[".", "."], [".", "."], ["wP", "."]])

    controller.click(50, 250)
    controller.click(50, 150)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[1][0] == "wP"


def test_black_pawn_moves_forward() -> None:
    controller = Controller([["bP", "."], [".", "."], [".", "."]])

    controller.click(50, 50)
    controller.click(50, 150)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[1][0] == "bP"


def test_pawn_captures_diagonally() -> None:
    controller = Controller([[".", "."], [".", "bP"], ["wP", "."]])

    controller.click(50, 250)
    controller.click(150, 150)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[1][1] == "wP"


def test_pawn_cannot_move_two_steps() -> None:
    # wP not on start rank (height-1=3), double step is illegal
    controller = Controller([[".", "."], [".", "."], [".", "."], ["wP", "."], [".", "."]])

    controller.click(50, 350)
    controller.click(50, 150)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[3][0] == "wP"
    assert controller.board.rows[1][0] == "."


def test_pawn_cannot_capture_forward() -> None:
    controller = Controller([["bP", "."], ["wP", "."]])

    controller.click(50, 150)
    controller.click(50, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[1][0] == "wP"
    assert controller.board.rows[0][0] == "bP"


def test_pawn_double_step_from_start() -> None:
    # wP on start rank (height-1=3), double step is legal
    controller = Controller([[".", "."], [".", "."], [".", "."], ["wP", "."]])

    controller.click(50, 350)
    controller.click(50, 150)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[1][0] == "wP"


def test_pawn_double_step_blocked() -> None:
    controller = Controller([[".", "."], [".", "."], [".", "."], [".", "."], [".", "."], ["bB", "."], ["wP", "."], [".", "."]])

    controller.click(50, 650)
    controller.click(50, 450)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[6][0] == "wP"


def test_white_pawn_promotes_to_queen() -> None:
    # wP on last row (height-1=1), single step to row 0 -> promotes
    controller = Controller([[".", "."], ["wP", "."]])

    controller.click(50, 150)
    controller.click(50, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][0] == "wQ"


def test_black_pawn_promotes_to_queen() -> None:
    # bP on row 0 (last row for black = 0), single step to last row -> promotes
    controller = Controller([["bP", "."], [".", "."]])

    controller.click(50, 50)
    controller.click(50, 150)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[1][0] == "bQ"


def test_piece_not_moved_before_arrival() -> None:
    controller = Controller([["wK", "."], [".", "."]])

    controller.click(50, 50)
    controller.click(150, 50)
    controller.wait(500)
    controller.print_board()

    assert controller.board.rows[0][0] == "wK"
    assert controller.board.rows[0][1] == "."


def test_piece_moved_after_arrival() -> None:
    controller = Controller([["wK", "."], [".", "."]])

    controller.click(50, 50)
    controller.click(150, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][0] == "."
    assert controller.board.rows[0][1] == "wK"


def test_capturing_enemy_king_ends_game() -> None:
    controller = Controller([["wR", "bK"]])

    controller.click(50, 50)
    controller.click(150, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.game_over is True


def test_moves_ignored_after_game_over() -> None:
    controller = Controller([["wR", "bK", "."]])

    controller.click(50, 50)
    controller.click(150, 50)
    controller.wait(1000)
    controller.print_board()
    controller.click(150, 50)
    controller.click(250, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][1] == "wR"
    assert controller.board.rows[0][2] == "."


def test_second_piece_blocked_while_first_in_transit() -> None:
    controller = Controller([["wR", ".", "."], [".", ".", "."], ["bR", ".", "."]])

    controller.click(50, 50)
    controller.click(250, 50)
    controller.click(50, 250)
    controller.click(250, 250)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][2] == "wR"
    assert controller.board.rows[2][0] == "bR"


def test_piece_can_move_again_immediately_after_arrival() -> None:
    controller = Controller([["wR", ".", "."], ["wK", ".", "bK"]])

    controller.click(50, 50)
    controller.click(150, 50)
    controller.wait(1000)
    controller.print_board()
    controller.click(150, 50)
    controller.click(250, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][2] == "wR"


def test_jump_captures_arriving_enemy() -> None:
    controller = Controller([["wR", ".", "bR"]])

    controller.jump(50, 50)
    controller.click(250, 50)
    controller.click(50, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][0] == "wR"
    assert controller.board.rows[0][2] == "."


def test_jump_no_enemy_piece_lands_normally() -> None:
    controller = Controller([["wR", ".", "."]])

    controller.jump(50, 50)
    controller.wait(1000)
    controller.print_board()

    assert controller.board.rows[0][0] == "wR"


def test_moving_piece_cannot_jump() -> None:
    controller = Controller([["wR", ".", "."]])

    controller.click(50, 50)
    controller.click(150, 50)
    controller.jump(50, 50)

    assert controller.airborne == []
