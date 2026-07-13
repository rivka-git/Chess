"""Chess piece classes and movement geometry."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Piece(ABC):
    """Abstract base class for all chess pieces."""

    def __init__(self, color: str) -> None:
        self.color = color

    @property
    @abstractmethod
    def piece_type(self) -> str:
        """Return the single-character piece type, e.g. 'K', 'P'."""

    @abstractmethod
    def is_legal_move(self, board: object, start: tuple[int, int], end: tuple[int, int]) -> bool:
        """Return whether moving from start to end is legal for this piece."""

    def on_reach_end(self, board: object, position: tuple[int, int]) -> None:
        """Called when a piece reaches the end of the board. Override to define promotion or other behavior."""

    def __str__(self) -> str:
        return self.color + self.piece_type


class King(Piece):
    piece_type = "K"

    def is_legal_move(self, board, start, end) -> bool:
        abs_row = abs(end[0] - start[0])
        abs_col = abs(end[1] - start[1])
        return (abs_row, abs_col) in {(0, 1), (1, 0), (1, 1)}


class Queen(Piece):
    piece_type = "Q"

    def is_legal_move(self, board, start, end) -> bool:
        row_delta = end[0] - start[0]
        col_delta = end[1] - start[1]
        abs_row, abs_col = abs(row_delta), abs(col_delta)
        return (row_delta == 0 or col_delta == 0 or abs_row == abs_col) and _is_path_clear(board, start, end)


class Rook(Piece):
    piece_type = "R"

    def is_legal_move(self, board, start, end) -> bool:
        row_delta = end[0] - start[0]
        col_delta = end[1] - start[1]
        return (row_delta == 0 or col_delta == 0) and _is_path_clear(board, start, end)


class Bishop(Piece):
    piece_type = "B"

    def is_legal_move(self, board, start, end) -> bool:
        abs_row = abs(end[0] - start[0])
        abs_col = abs(end[1] - start[1])
        return abs_row == abs_col and _is_path_clear(board, start, end)


class Knight(Piece):
    piece_type = "N"

    def is_legal_move(self, board, start, end) -> bool:
        abs_row = abs(end[0] - start[0])
        abs_col = abs(end[1] - start[1])
        return {abs_row, abs_col} == {1, 2}


class Pawn(Piece):
    piece_type = "P"

    def is_legal_move(self, board, start, end) -> bool:
        start_row, start_col = start
        end_row, end_col = end
        row_delta = end_row - start_row
        col_delta = end_col - start_col
        abs_col = abs(col_delta)
        direction = -1 if self.color == "w" else 1
        start_rank = board.height - 1 if self.color == "w" else 0
        target = board.rows[end_row][end_col]

        if col_delta == 0 and row_delta == direction:
            return target == "."
        if col_delta == 0 and row_delta == 2 * direction and start_row == start_rank:
            mid = board.rows[start_row + direction][start_col]
            return target == "." and mid == "."
        if abs_col == 1 and row_delta == direction:
            return target != "." and target[0] != self.color
        return False

    def on_reach_end(self, board: object, position: tuple[int, int]) -> None:
        row, col = position
        # Promote to queen upon reaching the opposite end of the board
        if self.color == "w" and row == 0:
            board.rows[row][col] = "wQ"
        elif self.color == "b" and row == board.height - 1:
            board.rows[row][col] = "bQ"


def _sign(n: int) -> int:
    return (n > 0) - (n < 0)


def _is_path_clear(board: object, start: tuple[int, int], end: tuple[int, int]) -> bool:
    """Return whether every intermediate square between start and end is empty."""
    row_step = _sign(end[0] - start[0])
    col_step = _sign(end[1] - start[1])
    row, col = start[0] + row_step, start[1] + col_step
    while (row, col) != (end[0], end[1]):
        if board.rows[row][col] != ".":
            return False
        row += row_step
        col += col_step
    return True
