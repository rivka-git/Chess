"""Collision detection and resolution for chess moves and jumps."""

from __future__ import annotations

from board import Board


class CollisionResolver:
    """Handle collisions between arriving pieces and airborne jumpers."""

    def resolve_collisions(
        self,
        board: Board,
        arrived_moves: list[tuple[tuple[int, int], tuple[int, int], int]],
        airborne_positions: list[tuple[int, int]],
    ) -> tuple[list[tuple[tuple[int, int], tuple[int, int]]], list[tuple[int, int]]]:
        """
        Resolve collisions between moving pieces and airborne pieces.
        
        Returns:
            Tuple of (moves_to_execute, pieces_destroyed)
            - moves_to_execute: moves that don't collide
            - pieces_destroyed: pieces that were destroyed in collisions
        """
        moves_to_execute = []
        pieces_destroyed = []

        for start, end, arrival_time in arrived_moves:
            if end in airborne_positions:
                # Collision! Moving piece is destroyed, jumper stays in place
                pieces_destroyed.append(start)
            else:
                # No collision, move can proceed
                moves_to_execute.append((start, end))

        return moves_to_execute, pieces_destroyed

    def destroy_pieces(self, board: Board, positions: list[tuple[int, int]]) -> None:
        """Remove pieces at the given positions."""
        for row, col in positions:
            board.rows[row][col] = "."
