"""Handle user input for clicks and jumps."""

from __future__ import annotations

from board import Board
from movement import MovementRules
from game_timer import GameTimer


class InputHandler:
    """Handle user input: clicks and jumps."""

    def __init__(self, game_timer: GameTimer, movement_rules: MovementRules) -> None:
        """Initialize the input handler."""
        self.game_timer = game_timer
        self.movement_rules = movement_rules
        self.selected_position: tuple[int, int] | None = None

    def handle_click(
        self, board: Board, x: int, y: int, on_move_requested: callable
    ) -> None:
        """
        Handle a click at pixel coordinates.
        
        Args:
            board: The game board
            x, y: Pixel coordinates
            on_move_requested: Callback when a move should be queued
        """
        row = y // 100
        col = x // 100

        if not self._is_inside_board(board, row, col):
            self.selected_position = None
            return

        if self.selected_position is None:
            # First click: select a piece
            if board.rows[row][col] != ".":
                self.selected_position = (row, col)
            return

        target_position = (row, col)
        target_piece = board.rows[row][col]

        # Second click: either select different piece or request move
        if target_piece != "." and self._is_own_piece(
            board, self.selected_position, target_position
        ):
            self.selected_position = target_position
            return

        if self.movement_rules.is_legal_move(board, self.selected_position, target_position):
            # Board is locked while any piece is in transit
            if not self.game_timer.has_pending_moves():
                on_move_requested(self.selected_position, target_position)

        self.selected_position = None

    def handle_jump(
        self, board: Board, x: int, y: int, on_jump_requested: callable
    ) -> None:
        """
        Handle a jump action.
        
        Args:
            board: The game board
            x, y: Pixel coordinates
            on_jump_requested: Callback when a jump should be queued
        """
        row = y // 100
        col = x // 100

        if not self._is_inside_board(board, row, col):
            return

        position = (row, col)

        if board.rows[row][col] == ".":
            return

        if self.game_timer.is_piece_in_transit(position):
            return

        if any(pos == position for pos, land_time in self.game_timer.airborne):
            return

        on_jump_requested(position)

    def _is_own_piece(
        self, board: Board, start: tuple[int, int], end: tuple[int, int]
    ) -> bool:
        """Return whether the destination contains a piece of the same color."""
        start_piece = board.rows[start[0]][start[1]]
        end_piece = board.rows[end[0]][end[1]]
        return end_piece != "." and self.movement_rules.is_same_color(
            start_piece, end_piece
        )

    def _is_inside_board(self, board: Board, row: int, col: int) -> bool:
        """Return whether the coordinates fall within the board bounds."""
        return 0 <= row < board.height and 0 <= col < board.width
