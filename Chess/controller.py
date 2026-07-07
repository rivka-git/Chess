"""Controller logic for click, wait, and board printing commands."""

from __future__ import annotations

from board import Board


class Controller:
    """Manage simple board interaction for iteration 2."""

    def __init__(self, rows: list[list[str]] | None = None) -> None:
        """Create a controller around a board representation."""
        self.board = Board(rows or [["."]])
        self.selected_position: tuple[int, int] | None = None
        self.pending_moves: list[tuple[tuple[int, int], tuple[int, int]]] = []
        self.time_ms = 0

    def click(self, x: int, y: int) -> None:
        """Handle a click at pixel coordinates, converting to a board cell."""
        row = y // 100
        col = x // 100

        if not self._is_inside_board(row, col):
            return

        cell = self.board.rows[row][col]
        if cell == ".":
            if self.selected_position is not None:
                self.pending_moves.append((self.selected_position, (row, col)))
                if self._is_legal_move(self.selected_position, (row, col)):
                    self._apply_move(self.selected_position, (row, col))
                self.selected_position = None
            return

        self.selected_position = (row, col)

    def wait(self, milliseconds: int) -> None:
        """Advance the game clock by the provided number of milliseconds."""
        self.time_ms += milliseconds

    def print_board(self) -> str:
        """Return the current settled board state after completed moves."""
        return self.board.to_canonical_string()

    def _apply_move(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        """Move a piece from one cell to another without applying chess rules."""
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board.rows[start_row][start_col]
        self.board.rows[start_row][start_col] = "."
        self.board.rows[end_row][end_col] = piece

    def _is_legal_move(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        """Return whether the move follows a basic movement pattern."""
        start_row, start_col = start
        end_row, end_col = end

        if start == end:
            return False

        piece = self.board.rows[start_row][start_col]
        piece_type = piece[1] if len(piece) > 1 else piece

        row_delta = end_row - start_row
        col_delta = end_col - start_col
        abs_row = abs(row_delta)
        abs_col = abs(col_delta)

        if piece_type == "K":
            return (abs_row, abs_col) in {(0, 1), (1, 0), (1, 1)}
        if piece_type == "R":
            return (row_delta == 0) or (col_delta == 0)
        if piece_type == "B":
            return abs_row == abs_col
        if piece_type == "Q":
            return (row_delta == 0) or (col_delta == 0) or (abs_row == abs_col)
        if piece_type == "N":
            return {abs_row, abs_col} == {1, 2}

        return False

    def _is_inside_board(self, row: int, col: int) -> bool:
        """Return whether the coordinates fall within the board bounds."""
        return 0 <= row < self.board.height and 0 <= col < self.board.width
