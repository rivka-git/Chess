"""Post-move side-effects applied after a piece reaches its destination."""

from __future__ import annotations

from core.model.board import Board


class PostMoveEffects:
    """Apply side-effects after a piece arrives at its destination (e.g. pawn promotion)."""

    def __init__(self, registry=None) -> None:
        if registry is None:
            from core.rules.rule_engine import MovementRules
            registry = MovementRules()._build_default_registry()
        self._registry = registry

    def apply(self, board: Board, end: tuple[int, int]) -> None:
        end_row, end_col = end
        token = board.get_piece(end_row, end_col)
        if token == ".":
            return
        piece_class = self._registry.rules.get(token[1])
        if piece_class is not None:
            piece_class(token[0]).on_reach_end(board, end)
