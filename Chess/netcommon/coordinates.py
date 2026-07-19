"""Coordinate conversions shared by the server and networked clients:
pixel space (what a mouse click reports) <-> board (row, col) space (what
the wire protocol carries) <-> algebraic square notation."""

from __future__ import annotations


def pixel_to_rowcol(x: int, y: int, cell_size: int) -> tuple[int, int]:
    return y // cell_size, x // cell_size


def rowcol_to_pixel_center(row: int, col: int, cell_size: int) -> tuple[int, int]:
    return col * cell_size + cell_size // 2, row * cell_size + cell_size // 2


def square_to_rowcol(square: str, board_height: int = 8) -> tuple[int, int]:
    """Convert an algebraic square like "e2" to (row, col); rank 8 = row 0."""
    file_char = square[0].lower()
    rank = int(square[1:])
    col = ord(file_char) - ord("a")
    row = board_height - rank
    return row, col


def rowcol_to_square(row: int, col: int, board_height: int = 8) -> str:
    file_char = chr(ord("a") + col)
    rank = board_height - row
    return f"{file_char}{rank}"
