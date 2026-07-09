"""Collision detection and resolution for chess moves and jumps."""

from __future__ import annotations

from model.board import Board


class CollisionResolver:
    """Handle collisions between arriving pieces and airborne jumpers."""

    def resolve_collisions(
        self,
        board: Board,
        arrived_moves: list[tuple[tuple[int, int], tuple[int, int], int]],
        airborne_positions: list[tuple[int, int]],
    ) -> tuple[list[tuple[tuple[int, int], tuple[int, int]]], list[tuple[int, int]]]:
        moves_to_execute = []
        pieces_destroyed = []

        for start, end, arrival_time in arrived_moves:
            if end in airborne_positions:
                pieces_destroyed.append(start)
            else:
                moves_to_execute.append((start, end))

        return moves_to_execute, pieces_destroyed

    def destroy_pieces(self, board: Board, positions: list[tuple[int, int]]) -> None:
        for row, col in positions:
            board.rows[row][col] = "."
