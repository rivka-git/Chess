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
                move_executor.apply_move(board, start, end)
                moves_executed.append((start, end))
            else:
                start_row, start_col = start
                board.rows[start_row][start_col] = "."

        return moves_executed
