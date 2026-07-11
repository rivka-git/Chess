"""Tests for basic piece movement rules."""

from engine.game_engine import GameEngine


def test_king_can_move_one_step() -> None:
    engine = GameEngine([["wK", "."], [".", "."]])
    engine.click(50, 50)
    engine.click(150, 50)
    engine.wait(1000)
    assert engine.board.rows[0][1] == "wK"


def test_king_cannot_move_two_steps() -> None:
    engine = GameEngine([["wK", ".", "."], [".", ".", "."]])
    engine.click(50, 50)
    engine.click(250, 50)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wK"
    assert engine.board.rows[0][2] == "."


def test_rook_cannot_move_diagonally() -> None:
    engine = GameEngine([["wR", ".", "."], [".", ".", "."]])
    engine.click(50, 50)
    engine.click(150, 150)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wR"
    assert engine.board.rows[1][1] == "."


def test_knight_can_move_in_l_shape() -> None:
    engine = GameEngine([["wN", ".", "."], [".", ".", "."], [".", ".", "."]])
    engine.click(50, 50)
    engine.click(250, 150)
    engine.wait(2000)
    assert engine.board.rows[1][2] == "wN"


def test_rook_cannot_move_through_blocker() -> None:
    engine = GameEngine([["wR", "bB", "."]])
    engine.click(50, 50)
    engine.click(250, 50)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wR"
    assert engine.board.rows[0][1] == "bB"
    assert engine.board.rows[0][2] == "."


def test_rook_can_capture_enemy_piece_on_destination() -> None:
    engine = GameEngine([["wR", ".", "bB"]])
    engine.click(50, 50)
    engine.click(250, 50)
    engine.wait(2000)
    assert engine.board.rows[0][0] == "."
    assert engine.board.rows[0][2] == "wR"


def test_white_pawn_moves_forward() -> None:
    engine = GameEngine([[".", "."], [".", "."], ["wP", "."]])
    engine.click(50, 250)
    engine.click(50, 150)
    engine.wait(1000)
    assert engine.board.rows[1][0] == "wP"


def test_black_pawn_moves_forward() -> None:
    engine = GameEngine([["bP", "."], [".", "."], [".", "."]])
    engine.click(50, 50)
    engine.click(50, 150)
    engine.wait(1000)
    assert engine.board.rows[1][0] == "bP"


def test_pawn_captures_diagonally() -> None:
    engine = GameEngine([[".", "."], [".", "bP"], ["wP", "."]])
    engine.click(50, 250)
    engine.click(150, 150)
    engine.wait(1000)
    assert engine.board.rows[1][1] == "wP"


def test_pawn_cannot_move_two_steps() -> None:
    engine = GameEngine([[".", "."], [".", "."], [".", "."], ["wP", "."], [".", "."]])
    engine.click(50, 350)
    engine.click(50, 150)
    engine.wait(1000)
    assert engine.board.rows[3][0] == "wP"
    assert engine.board.rows[1][0] == "."


def test_pawn_cannot_capture_forward() -> None:
    engine = GameEngine([["bP", "."], ["wP", "."]])
    engine.click(50, 150)
    engine.click(50, 50)
    engine.wait(1000)
    assert engine.board.rows[1][0] == "wP"
    assert engine.board.rows[0][0] == "bP"


def test_pawn_double_step_from_start() -> None:
    engine = GameEngine([[".", "."], [".", "."], [".", "."], ["wP", "."]])
    engine.click(50, 350)
    engine.click(50, 150)
    engine.wait(2000)
    assert engine.board.rows[1][0] == "wP"


def test_pawn_double_step_blocked() -> None:
    engine = GameEngine([[".", "."], [".", "."], [".", "."], [".", "."], [".", "."], ["bB", "."], ["wP", "."], [".", "."]])
    engine.click(50, 650)
    engine.click(50, 450)
    engine.wait(1000)
    assert engine.board.rows[6][0] == "wP"


def test_white_pawn_promotes_to_queen() -> None:
    engine = GameEngine([[".", "."], ["wP", "."]])
    engine.click(50, 150)
    engine.click(50, 50)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wQ"


def test_black_pawn_promotes_to_queen() -> None:
    engine = GameEngine([["bP", "."], [".", "."]])
    engine.click(50, 50)
    engine.click(50, 150)
    engine.wait(1000)
    assert engine.board.rows[1][0] == "bQ"


def test_piece_not_moved_before_arrival() -> None:
    engine = GameEngine([["wK", "."], [".", "."]])
    engine.click(50, 50)
    engine.click(150, 50)
    engine.wait(500)
    assert engine.board.rows[0][0] == "wK"
    assert engine.board.rows[0][1] == "."


def test_piece_moved_after_arrival() -> None:
    engine = GameEngine([["wK", "."], [".", "."]])
    engine.click(50, 50)
    engine.click(150, 50)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "."
    assert engine.board.rows[0][1] == "wK"


def test_capturing_enemy_king_ends_game() -> None:
    engine = GameEngine([["wR", "bK"]])
    engine.click(50, 50)
    engine.click(150, 50)
    engine.wait(1000)
    assert engine.game_over is True


def test_moves_ignored_after_game_over() -> None:
    engine = GameEngine([["wR", "bK", "."]])
    engine.click(50, 50)
    engine.click(150, 50)
    engine.wait(1000)
    engine.click(150, 50)
    engine.click(250, 50)
    engine.wait(1000)
    assert engine.board.rows[0][1] == "wR"
    assert engine.board.rows[0][2] == "."


def test_second_piece_blocked_while_first_in_transit() -> None:
    engine = GameEngine([["wR", ".", "."], [".", ".", "."], ["bR", ".", "."]])
    engine.click(50, 50)
    engine.click(250, 50)
    engine.click(50, 250)
    engine.click(250, 250)
    engine.wait(2000)
    assert engine.board.rows[0][2] == "wR"
    assert engine.board.rows[2][0] == "bR"


def test_piece_can_move_again_immediately_after_arrival() -> None:
    engine = GameEngine([["wR", ".", "."], ["wK", ".", "bK"]])
    engine.click(50, 50)
    engine.click(150, 50)
    engine.wait(1000)
    engine.click(150, 50)
    engine.click(250, 50)
    engine.wait(1000)
    assert engine.board.rows[0][2] == "wR"


def test_jump_captures_arriving_enemy() -> None:
    engine = GameEngine([["wR", ".", "bR"]])
    engine.click(250, 50)
    engine.click(50, 50)
    engine.wait(1000)
    engine.jump(50, 50)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wR"
    assert engine.board.rows[0][2] == "."


def test_jump_no_enemy_piece_lands_normally() -> None:
    engine = GameEngine([["wR", ".", "."]])
    engine.jump(50, 50)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wR"


def test_moving_piece_cannot_jump() -> None:
    engine = GameEngine([["wR", ".", "."]])
    engine.click(50, 50)
    engine.click(150, 50)
    engine.jump(50, 50)
    engine.wait(1000)
    assert engine.board.rows[0][1] == "wR"  # זז ליעד, לא קפץ
