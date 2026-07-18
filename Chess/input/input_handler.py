"""Handle user input for clicks and jumps."""

from __future__ import annotations

from config import CELL_SIZE_PX
from model.board import Board
from rules.rule_engine import MovementRules
from realtime.motion import GameTimer


class InputHandler:
    """Handle user input: clicks and jumps."""

    def __init__(self, game_timer: GameTimer, movement_rules: MovementRules) -> None:
        self.game_timer = game_timer
        self.movement_rules = movement_rules
        self.selected_position: tuple[int, int] | None = None
        self.cell_size: int = CELL_SIZE_PX

    def handle_click(self, board: Board, x: int, y: int, on_move_requested: callable) -> None:
        row = y // self.cell_size
        col = x // self.cell_size

        if not self._is_inside_board(board, row, col):
            self.selected_position = None
            return

        if self.selected_position is None:
            self._on_no_selection(board, row, col)
        else:
            self._on_piece_selected(board, row, col, on_move_requested)

    def _on_no_selection(self, board: Board, row: int, col: int) -> None:
        piece = board.rows[row][col]
        if piece != "." and not self.game_timer.is_piece_in_transit((row, col)):
            self.selected_position = (row, col)
            return
        for start, end, *_ in self.game_timer.pending_moves:
            if end == (row, col):
                self.selected_position = start
                return

    def _on_piece_selected(self, board: Board, row: int, col: int, on_move_requested: callable) -> None:
        target_position = (row, col)
        target_piece = board.rows[row][col]
        selected_piece = board.rows[self.selected_position[0]][self.selected_position[1]]

        if target_position == self.selected_position:
            self.selected_position = None
            return

        if target_piece != "." and self.movement_rules.is_same_color(selected_piece, target_piece):
            self.selected_position = target_position
            return

        if selected_piece == ".":
            self.selected_position = None
            return

        legal = self.movement_rules.is_legal_move(board, self.selected_position, target_position)
        in_transit = self.game_timer.is_piece_in_transit(self.selected_position)
        if legal and not in_transit:
            on_move_requested(self.selected_position, target_position)

        self.selected_position = None

    def handle_jump(self, board: Board, x: int, y: int, on_jump_requested: callable) -> None:
        row = y // self.cell_size
        col = x // self.cell_size

        if not self._is_inside_board(board, row, col):
            return

        position = (row, col)

        if board.rows[row][col] == ".":
            return

        if self.game_timer.is_piece_in_transit(position):
            return

        if self.game_timer.is_piece_airborne(position):
            return

        on_jump_requested(position)

    def _is_own_piece(self, board: Board, start: tuple[int, int], end: tuple[int, int]) -> bool:
        start_piece = board.get_piece(start[0], start[1])
        end_piece = board.get_piece(end[0], end[1])
        return end_piece != "." and self.movement_rules.is_same_color(start_piece, end_piece)

    def _is_inside_board(self, board: Board, row: int, col: int) -> bool:
        return 0 <= row < board.height and 0 <= col < board.width
