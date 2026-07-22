"""Tests for basic piece movement rules."""

from core.engine.game_engine import GameEngine


def test_king_can_move_one_step() -> None:
    engine = GameEngine([["wK", "."], [".", "."]])
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(1000)
    assert engine.board.rows[0][1] == "wK"


def test_king_cannot_move_two_steps() -> None:
    engine = GameEngine([["wK", ".", "."], [".", ".", "."]])
    engine.click(0, 0)
    engine.click(0, 2)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wK"
    assert engine.board.rows[0][2] == "."


def test_rook_cannot_move_diagonally() -> None:
    engine = GameEngine([["wR", ".", "."], [".", ".", "."]])
    engine.click(0, 0)
    engine.click(1, 1)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wR"
    assert engine.board.rows[1][1] == "."


def test_knight_can_move_in_l_shape() -> None:
    engine = GameEngine([["wN", ".", "."], [".", ".", "."], [".", ".", "."]])
    engine.click(0, 0)
    engine.click(1, 2)
    engine.wait(2000)
    assert engine.board.rows[1][2] == "wN"


def test_rook_cannot_move_through_blocker() -> None:
    engine = GameEngine([["wR", "bB", "."]])
    engine.click(0, 0)
    engine.click(0, 2)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wR"
    assert engine.board.rows[0][1] == "bB"
    assert engine.board.rows[0][2] == "."


def test_rook_can_capture_enemy_piece_on_destination() -> None:
    engine = GameEngine([["wR", ".", "bB"]])
    engine.click(0, 0)
    engine.click(0, 2)
    engine.wait(2000)
    assert engine.board.rows[0][0] == "."
    assert engine.board.rows[0][2] == "wR"


def test_white_pawn_moves_forward() -> None:
    engine = GameEngine([[".", "."], [".", "."], ["wP", "."]])
    engine.click(2, 0)
    engine.click(1, 0)
    engine.wait(1000)
    assert engine.board.rows[1][0] == "wP"


def test_black_pawn_moves_forward() -> None:
    engine = GameEngine([["bP", "."], [".", "."], [".", "."]])
    engine.click(0, 0)
    engine.click(1, 0)
    engine.wait(1000)
    assert engine.board.rows[1][0] == "bP"


def test_pawn_captures_diagonally() -> None:
    engine = GameEngine([[".", "."], [".", "bP"], ["wP", "."]])
    engine.click(2, 0)
    engine.click(1, 1)
    engine.wait(1000)
    assert engine.board.rows[1][1] == "wP"


def test_pawn_cannot_move_two_steps() -> None:
    engine = GameEngine([[".", "."], [".", "."], [".", "."], ["wP", "."], [".", "."]])
    engine.click(3, 0)
    engine.click(1, 0)
    engine.wait(1000)
    assert engine.board.rows[3][0] == "wP"
    assert engine.board.rows[1][0] == "."


def test_pawn_cannot_capture_forward() -> None:
    engine = GameEngine([["bP", "."], ["wP", "."]])
    engine.click(1, 0)
    engine.click(0, 0)
    engine.wait(1000)
    assert engine.board.rows[1][0] == "wP"
    assert engine.board.rows[0][0] == "bP"


def test_pawn_double_step_from_start() -> None:
    engine = GameEngine([[".", "."], [".", "."], [".", "."], ["wP", "."]])
    engine.click(3, 0)
    engine.click(1, 0)
    engine.wait(2000)
    assert engine.board.rows[1][0] == "wP"


def test_pawn_double_step_blocked() -> None:
    engine = GameEngine([[".", "."], [".", "."], [".", "."], [".", "."], [".", "."], ["bB", "."], ["wP", "."], [".", "."]])
    engine.click(6, 0)
    engine.click(4, 0)
    engine.wait(1000)
    assert engine.board.rows[6][0] == "wP"


def test_white_pawn_promotes_to_queen() -> None:
    engine = GameEngine([[".", "."], ["wP", "."]])
    engine.click(1, 0)
    engine.click(0, 0)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wQ"


def test_black_pawn_promotes_to_queen() -> None:
    engine = GameEngine([["bP", "."], [".", "."]])
    engine.click(0, 0)
    engine.click(1, 0)
    engine.wait(1000)
    assert engine.board.rows[1][0] == "bQ"


def test_piece_not_moved_before_arrival() -> None:
    engine = GameEngine([["wK", "."], [".", "."]])
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(500)
    assert engine.board.rows[0][0] == "wK"
    assert engine.board.rows[0][1] == "."


def test_piece_moved_after_arrival() -> None:
    engine = GameEngine([["wK", "."], [".", "."]])
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "."
    assert engine.board.rows[0][1] == "wK"


def test_capturing_enemy_king_ends_game() -> None:
    engine = GameEngine([["wR", "bK"]])
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(1000)
    assert engine.game_over is True


def test_airborne_king_intercepts_moving_enemy_triggers_game_over() -> None:
    """bK jumps (airborne at its own square) and intercepts wK arriving there — wK is captured, game over."""
    engine = GameEngine([["wK", "bK"]])
    # wK at (0,0) moves to (0,1) — straight into bK
    engine.click(0, 0)
    engine.click(0, 1)
    # bK at (0,1) jumps — becomes airborne at (0,1)
    engine.jump(0, 1)
    # wK arrives at (0,1) but bK is airborne there → wK (the mover) is captured
    engine.wait(1000)
    assert engine.game_over is True
    assert engine.board.rows[0][0] == "."   # wK removed from start
    assert engine.board.rows[0][1] == "bK"  # bK still alive at Y


def test_moves_ignored_after_game_over() -> None:
    engine = GameEngine([["wR", "bK", "."]])
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(1000)
    engine.click(0, 1)
    engine.click(0, 2)
    engine.wait(1000)
    assert engine.board.rows[0][1] == "wR"
    assert engine.board.rows[0][2] == "."


def test_second_piece_blocked_while_first_in_transit() -> None:
    engine = GameEngine([["wR", ".", "."], [".", ".", "."], ["bR", ".", "."]])
    engine.click(0, 0)
    engine.click(0, 2)
    engine.click(2, 0)
    engine.click(2, 2)
    engine.wait(2000)
    assert engine.board.rows[0][2] == "wR"
    assert engine.board.rows[2][2] == "bR"


def test_piece_can_move_again_immediately_after_arrival() -> None:
    engine = GameEngine([["wR", ".", "."], ["wK", ".", "bK"]])
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(1000)
    engine.click(0, 1)
    engine.click(0, 2)
    engine.wait(1000)
    assert engine.board.rows[0][2] == "wR"


def test_jump_captures_arriving_enemy() -> None:
    engine = GameEngine([["wR", ".", "bR"]])
    engine.click(0, 2)
    engine.click(0, 0)
    engine.wait(1000)
    engine.jump(0, 0)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wR"
    assert engine.board.rows[0][2] == "."


def test_jump_no_enemy_piece_lands_normally() -> None:
    engine = GameEngine([["wR", ".", "."]])
    engine.jump(0, 0)
    engine.wait(1000)
    assert engine.board.rows[0][0] == "wR"


def test_moving_piece_cannot_jump() -> None:
    engine = GameEngine([["wR", ".", "."]])
    engine.click(0, 0)
    engine.click(0, 1)
    engine.jump(0, 0)
    engine.wait(1000)
    assert engine.board.rows[0][1] == "wR"  # זז ליעד, לא קפץ


def test_same_destination_collision_stops_both_at_last_legal_square() -> None:
    engine = GameEngine([["wR", ".", "bR"]])
    engine.click(0, 0)
    engine.click(0, 1)
    engine.click(0, 2)
    engine.click(0, 1)
    engine.wait(1000)
    assert engine.board.rows[0] == ["wR", ".", "bR"]


def test_same_color_same_destination_collision_also_stops_both() -> None:
    engine = GameEngine([["wR", ".", "wQ"]])
    engine.click(0, 0)
    engine.click(0, 1)
    engine.click(0, 2)
    engine.click(0, 1)
    engine.wait(1000)
    assert engine.board.rows[0] == ["wR", ".", "wQ"]


def test_mid_path_collision_stops_both_before_meeting_point() -> None:
    engine = GameEngine([["wR", ".", ".", ".", "bR"]])
    engine.click(0, 0)
    engine.click(0, 4)
    engine.click(0, 4)
    engine.click(0, 0)
    engine.wait(4000)
    assert engine.board.rows[0] == [".", "wR", ".", "bR", "."]


def test_same_destination_collision_ui_timing() -> None:
    """Moves registered 16 ms apart (one UI frame) must still collide."""
    engine = GameEngine([["wR", ".", "bR"]])
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(16)          # simulate one UI frame between the two clicks
    engine.click(0, 2)
    engine.click(0, 1)
    engine.wait(1000)
    assert engine.board.rows[0] == ["wR", ".", "bR"]


def test_same_destination_collision_ui_timing_32ms() -> None:
    """Moves registered 32 ms apart must still collide."""
    engine = GameEngine([["wR", ".", "bR"]])
    engine.click(0, 0)
    engine.click(0, 1)
    engine.wait(32)
    engine.click(0, 2)
    engine.click(0, 1)
    engine.wait(1000)
    assert engine.board.rows[0] == ["wR", ".", "bR"]


def test_no_false_collision_when_piece_already_at_rest() -> None:
    """bR captures wR normally when wR already arrived (not in transit) — no false collision."""
    engine = GameEngine([["wR", ".", "bR"]])
    engine.click(0, 0)
    engine.click(0, 1)   # wR → (0,1), arrives at T=1000
    engine.wait(2000)       # T=2000 — wR long at rest, bR now starts moving
    engine.click(0, 2)
    engine.click(0, 1)   # bR captures wR (valid independent capture, no collision)
    engine.wait(1001)
    assert engine.board.rows[0][1] == "bR"
