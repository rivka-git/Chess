"""Integration tests - teacher-provided test cases."""

import io
import sys
import pytest
import app

CASES = [
    ("parse_empty_board_3x3", "Board:\n. . .\n. . .\n. . .\nCommands:\nprint board", ". . .\n. . .\n. . ."),
    ("parse_rectangular_board_3x4", "Board:\nwK . . bK\n. . . .\nwR . . bR\nCommands:\nprint board", "wK . . bK\n. . . .\nwR . . bR"),
    ("parse_piece_tokens_and_colors", "Board:\nwK . bQ\n. wN .\nbP . wR\nCommands:\nprint board", "wK . bQ\n. wN .\nbP . wR"),
    ("reject_unknown_token", "Board:\nwK xZ\n. .\nCommands:", "ERROR UNKNOWN_TOKEN"),
    ("reject_row_width_mismatch", "Board:\nwK . .\n. bK\nCommands:", "ERROR ROW_WIDTH_MISMATCH"),
    ("select_piece_by_center_click", "Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 150 150\nwait 1000\nprint board", ". . .\n. wK .\n. . ."),
    ("click_empty_cell_does_not_select", "Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 150 150\nclick 250 250\nwait 1000\nprint board", "wK . .\n. . .\n. . ."),
    ("click_outside_board_is_ignored", "Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 350 50\nclick -10 50\nprint board", "wK . .\n. . .\n. . ."),
    ("clicking_another_piece_replaces_selection", "Board:\nwR . wK\n. . .\nCommands:\nclick 50 50\nclick 250 50\nclick 250 150\nwait 1000\nprint board", "wR . .\n. . wK"),
    ("king_one_step_valid", "Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 150 150\nwait 1000\nprint board", ". . .\n. wK .\n. . ."),
    ("king_two_steps_invalid", "Board:\nwK . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 250 250\nwait 1000\nprint board", "wK . .\n. . .\n. . ."),
    ("rook_straight_valid", "Board:\nwR . .\nCommands:\nclick 50 50\nclick 250 50\nwait 2000\nprint board", ". . wR"),
    ("rook_diagonal_invalid", "Board:\nwR . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 150 150\nwait 1000\nprint board", "wR . .\n. . .\n. . ."),
    ("bishop_diagonal_valid", "Board:\nwB . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 250 250\nwait 2000\nprint board", ". . .\n. . .\n. . wB"),
    ("knight_L_valid", "Board:\nwN . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 150 250\nwait 3000\nprint board", ". . .\n. . .\n. wN ."),
    ("queen_diagonal_valid", "Board:\nwQ . .\n. . .\n. . .\nCommands:\nclick 50 50\nclick 250 250\nwait 2000\nprint board", ". . .\n. . .\n. . wQ"),
    ("rook_blocked_by_own_piece", "Board:\nwR wP .\nCommands:\nclick 50 50\nclick 250 50\nwait 2000\nprint board", "wR wP ."),
    ("bishop_blocked_by_own_piece", "Board:\nwB . .\n. wP .\n. . .\nCommands:\nclick 50 50\nclick 250 250\nwait 2000\nprint board", "wB . .\n. wP .\n. . ."),
    ("knight_jumps_over_blockers", "Board:\nwN wP .\nwP . .\n. . .\nCommands:\nclick 50 50\nclick 150 250\nwait 3000\nprint board", ". wP .\nwP . .\n. wN ."),
    ("cannot_capture_own_piece", "Board:\nwR . wP\nCommands:\nclick 50 50\nclick 250 50\nwait 2000\nprint board", "wR . wP"),
    ("rook_captures_enemy_at_destination", "Board:\nwR . bR\nCommands:\nclick 50 50\nclick 250 50\nwait 2000\nprint board", ". . wR"),
    ("pawn_cannot_capture_forward", "Board:\n. bR .\n. wP .\n. . .\nCommands:\nclick 150 150\nclick 150 50\nwait 1000\nprint board", ". bR .\n. wP .\n. . ."),
    ("one_cell_move_before_arrival_board_unchanged", "Board:\nwR . .\nCommands:\nclick 50 50\nclick 150 50\nwait 500\nprint board", "wR . ."),
    ("two_cell_move_before_and_after_arrival", "Board:\nwR . .\nCommands:\nclick 50 50\nclick 250 50\nwait 1000\nprint board\nwait 1000\nprint board", "wR . .\n. . wR"),
    ("moving_piece_ignores_redirect", "Board:\nwR . .\nCommands:\nclick 50 50\nclick 250 50\nwait 1000\nclick 50 50\nclick 150 50\nwait 1000\nprint board", ". . wR"),
    ("opposite_colors_do_not_move_concurrently_in_common_route", "Board:\nwR . .\n. . .\nbR . .\nCommands:\nclick 50 50\nclick 250 50\nclick 50 250\nclick 250 250\nwait 2000\nprint board", ". . wR\n. . .\n. . bR"),
    ("no_cooldown_state_in_common_route", "Board:\nwR . .\nCommands:\nclick 50 50\nclick 150 50\nwait 1000\nprint board", ". wR ."),
    ("can_move_again_after_arrival_without_cooldown", "Board:\nwR . .\nCommands:\nclick 50 50\nclick 150 50\nwait 1000\nclick 150 50\nclick 250 50\nwait 1000\nprint board", ". . wR"),
    ("piece_is_ready_after_arrival_without_cooldown", "Board:\nwR . .\nCommands:\nclick 50 50\nclick 150 50\nwait 1000\nclick 150 50\nclick 250 50\nwait 1000\nprint board", ". . wR"),
    ("enemy_collision_white_started_first", "Board:\nwR . . bR\nCommands:\nclick 50 50\nclick 350 50\nclick 350 50\nclick 50 50\nwait 3000\nprint board", ". . . wR"),
    ("enemy_collision_black_started_first", "Board:\nwR . . bR\nCommands:\nclick 350 50\nclick 50 50\nclick 50 50\nclick 350 50\nwait 3000\nprint board", "bR . . ."),
    ("cannot_start_move_through_friendly_piece", "Board:\n. . .\nwR wP .\n. . .\nCommands:\nclick 50 150\nclick 250 150\nwait 2000\nprint board", ". . .\nwR wP .\n. . ."),
    ("dynamic_block_tactic_not_in_common_route", "Board:\n. . . .\nwQ . . bK\n. . bP .\n. . . .\nCommands:\nclick 50 150\nclick 350 150\nwait 200\nclick 250 250\nclick 250 150\nwait 3000\nprint board", ". . . .\n. . . wQ\n. . bP .\n. . . ."),
    ("knight_cannot_land_on_friendly_piece", "Board:\n. wP .\n. . .\nwN . .\nCommands:\nclick 50 250\nclick 150 50\nwait 1000\nprint board", ". wP .\n. . .\nwN . ."),
    ("premove_does_not_execute_in_common_route", "Board:\nwR . .\nCommands:\nclick 50 50\nclick 150 50\nclick 50 50\nclick 250 50\nwait 2000\nprint board", ". wR ."),
    ("king_capture_ends_game", "Board:\nwR . bK\nCommands:\nclick 50 50\nclick 250 50\nwait 2000\nprint board", ". . wR"),
    ("no_moves_after_game_over", "Board:\nwR . bK\nbR . .\nCommands:\nclick 50 50\nclick 250 50\nwait 2000\nclick 50 150\nclick 150 150\nwait 1000\nprint board", ". . wR\nbR . ."),
    ("white_pawn_double_from_start_valid", "Board:\n. . .\n. . .\n. . .\n. wP .\nCommands:\nclick 150 350\nclick 150 150\nwait 2000\nprint board", ". . .\n. wP .\n. . .\n. . ."),
    ("black_pawn_double_from_start_valid", "Board:\n. bP .\n. . .\n. . .\n. . .\nCommands:\nclick 150 50\nclick 150 250\nwait 2000\nprint board", ". . .\n. . .\n. bP .\n. . ."),
    ("white_pawn_double_blocked_invalid", "Board:\n. . .\n. . .\n. bR .\n. wP .\nCommands:\nclick 150 350\nclick 150 150\nwait 2000\nprint board", ". . .\n. . .\n. bR .\n. wP ."),
    ("white_pawn_double_from_non_start_invalid", "Board:\n. . .\n. . .\n. wP .\n. . .\nCommands:\nclick 150 250\nclick 150 50\nwait 2000\nprint board", ". . .\n. . .\n. wP .\n. . ."),
    ("white_pawn_promotes_to_queen", "Board:\n. . .\n. wP .\nCommands:\nclick 150 150\nclick 150 50\nwait 1000\nprint board", ". wQ .\n. . ."),
    ("black_pawn_promotes_to_queen", "Board:\n. bP .\n. . .\nCommands:\nclick 150 50\nclick 150 150\nwait 1000\nprint board", ". . .\n. bQ ."),
    ("promoted_queen_moves_diagonal", "Board:\n. . .\n. wP .\n. . .\nCommands:\nclick 150 150\nclick 150 50\nwait 1000\nclick 150 50\nclick 250 150\nwait 1000\nprint board", ". . .\n. . wQ\n. . ."),
    ("jump_lands_same_square", "Board:\n. . .\n. wK .\n. . .\nCommands:\njump 150 150\nwait 1000\nprint board", ". . .\n. wK .\n. . ."),
    ("airborne_piece_captures_arriving_enemy", "Board:\n. . .\nwK bR .\n. . .\nCommands:\njump 50 150\nclick 150 150\nclick 50 150\nwait 1000\nprint board", ". . .\nwK . .\n. . ."),
    ("jump_too_late_does_not_save_piece", "Board:\n. . .\nwK bR .\n. . .\nCommands:\nclick 150 150\nclick 50 150\nwait 1000\njump 50 150\nprint board", ". . .\nbR . .\n. . ."),
    ("enemy_arrives_after_landing_captures_normally", "Board:\n. . . .\nwK . . bR\n. . . .\nCommands:\njump 50 150\nwait 1000\nclick 350 150\nclick 50 150\nwait 3000\nprint board", ". . . .\nbR . . .\n. . . ."),
    ("cannot_jump_while_moving", "Board:\nwR . .\nCommands:\nclick 50 50\nclick 250 50\nwait 500\njump 50 50\nwait 1500\nprint board", ". . wR"),
    ("airborne_capture_only_enemy", "Board:\n. . .\nwK wR .\n. . .\nCommands:\njump 50 150\nclick 150 150\nclick 50 150\nwait 1000\nprint board", ". . .\nwK wR .\n. . ."),
]


@pytest.mark.parametrize("name,board_input,expected", CASES, ids=[c[0] for c in CASES])
def test_teacher_case(name, board_input, expected, monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(board_input))
    app.main()
    assert capsys.readouterr().out.strip() == expected
