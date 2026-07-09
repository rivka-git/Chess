"""Registry mapping piece types to their movement rule functions."""

from __future__ import annotations


class PieceRegistry:
    """Hold the mapping of piece types to their movement rule functions."""

    def __init__(self) -> None:
        self.rules: dict = {}

    def register(self, piece_type: str, checker: object) -> None:
        """Register a custom movement rule for a piece type."""
        self.rules[piece_type] = checker
