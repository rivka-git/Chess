"""Handle game end condition detection."""

from __future__ import annotations

from board import Board


class GameEndDetector:
    """Detect when the game has ended."""

    def check_king_captured(self, board: Board, kings_before: set[str]) -> bool:
        """
        Return whether a king that was present before a move is now gone.
        
        Args:
            board: The game board
            kings_before: Set of king tokens before the move
            
        Returns:
            True if a king was captured, False otherwise
        """
        kings_now = self._get_kings_on_board(board)
        return bool(kings_before - kings_now)

    def _get_kings_on_board(self, board: Board) -> set[str]:
        """Return the set of king tokens currently present on the board."""
        pieces = {cell for row in board.rows for cell in row}
        return pieces & {"wK", "bK"}
