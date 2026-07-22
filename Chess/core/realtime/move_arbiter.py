"""Arbitration of which arrived moves are executed and which are cancelled."""

from __future__ import annotations


class MoveArbiter:
    """Decide which arrived moves proceed, based on destination priority and head-on conflicts."""

    def filter_arrived(self, arrived_moves: list) -> list:
        """Return only the earliest-arriving move per destination square."""
        seen_ends: set[tuple[int, int]] = set()
        filtered: list = []
        for move in sorted(arrived_moves, key=lambda m: (m[4], arrived_moves.index(m))):
            if move[1] not in seen_ends:
                seen_ends.add(move[1])
                filtered.append(move)
        return filtered

    def cancel_head_on(self, pending_moves: list, arrived_end: tuple[int, int]) -> list:
        """Cancel pending moves that conflict with a piece arriving at arrived_end.

        Removes moves whose destination equals arrived_end (two pieces targeting the same square)
        and moves whose origin equals arrived_end (piece was displaced before it could leave).
        """
        return [m for m in pending_moves if m[1] != arrived_end and m[0] != arrived_end]
