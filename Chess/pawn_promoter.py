"""Handle pawn promotion logic."""

from __future__ import annotations

from board import Board


class PawnPromoter:
    """Promote pawns that reach the opponent's back row."""

    def promote_pawns(self, board: Board, start: tuple[int, int], end: tuple[int, int]) -> None:
        """Promote a pawn that reached the back rank."""
        end_row, end_col = end
        piece = board.rows[end_row][end_col]
        if piece == "wP" and end_row == 0:
            board.rows[end_row][end_col] = "wQ"
        elif piece == "bP" and end_row == board.height - 1:
            board.rows[end_row][end_col] = "bQ"
