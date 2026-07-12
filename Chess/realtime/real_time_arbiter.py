"""Collision detection and resolution for chess moves and jumps."""

from __future__ import annotations

from model.board import Board
from rules.rule_engine import MoveExecutor


class CollisionResolver:
    """Handle collisions between arriving pieces and airborne jumpers."""

    def resolve_collisions(
        self,
        board: Board,
        arrived_moves: list[tuple[tuple[int, int], tuple[int, int], int]],
        airborne_positions: list[tuple[int, int]],
        move_executor: MoveExecutor,
    ) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        moves_executed = []

        for start, end, arrival_time in arrived_moves:
            if end not in airborne_positions:
                self._capture_piece(board, end)
                move_executor.apply_move(board, start, end)
                moves_executed.append((start, end))
            else:
                self._capture_piece(board, start)

        return moves_executed

    def _capture_piece(self, board: Board, position: tuple[int, int]) -> None:
        row, col = position
        board.rows[row][col] = "."
