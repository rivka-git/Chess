"""Handle pawn promotion logic."""

from __future__ import annotations

from board import Board


class PawnPromoter:
    """Promote pawns that reach the opponent's back row."""

    def promote_pawns(self, board: Board) -> None:
        """Promote any pawn that has reached the last row to a queen."""
        for col in range(board.width):
            # White pawns promote on row 0
            if board.rows[0][col] == "wP":
                board.rows[0][col] = "wQ"
            # Black pawns promote on the last row
            if board.rows[board.height - 1][col] == "bP":
                board.rows[board.height - 1][col] = "bQ"
