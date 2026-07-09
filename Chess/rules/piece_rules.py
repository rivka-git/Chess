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

    def __str__(self) -> str:
        return self.color + self.piece_type

    @staticmethod
    def from_token(token: str) -> Piece:
        color = token[0]
        piece_type = token[1]
        registry = {"K": King, "Q": Queen, "R": Rook, "B": Bishop, "N": Knight, "P": Pawn}
        return registry[piece_type](color)


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


def _is_path_clear(board: object, start: tuple[int, int], end: tuple[int, int]) -> bool:
    """Return whether every intermediate square between start and end is empty."""
    start_row, start_col = start
    end_row, end_col = end

    if start_row == end_row:
        step = 1 if end_col > start_col else -1
        for col in range(start_col + step, end_col, step):
            if board.rows[start_row][col] != ".":
                return False
        return True

    if start_col == end_col:
        step = 1 if end_row > start_row else -1
        for row in range(start_row + step, end_row, step):
            if board.rows[row][start_col] != ".":
                return False
        return True

    if abs(end_row - start_row) == abs(end_col - start_col):
        row_step = 1 if end_row > start_row else -1
        col_step = 1 if end_col > start_col else -1
        row, col = start_row + row_step, start_col + col_step
        while (row, col) != (end_row, end_col):
            if board.rows[row][col] != ".":
                return False
            row += row_step
            col += col_step
        return True

    return False
