"""Movement validation, piece registry, move execution, and pawn promotion."""

from __future__ import annotations

from model.board import Board
from model.piece import Piece, King, Queen, Rook, Bishop, Knight, Pawn


class PieceRegistry:
    """Map piece type characters to Piece subclasses."""

    def __init__(self) -> None:
        self.rules: dict[str, type[Piece]] = {}

    def register(self, piece_type: str, piece_class: type[Piece]) -> None:
        self.rules[piece_type] = piece_class


class MoveExecutor:
    """Execute a validated move on the board."""

    def apply_move(self, board: Board, start: tuple[int, int], end: tuple[int, int]) -> None:
        start_row, start_col = start
        end_row, end_col = end
        board.rows[end_row][end_col] = board.rows[start_row][start_col]
        board.rows[start_row][start_col] = "."


class MovementRules:
    """Encapsulate movement validation for chess pieces."""

    def __init__(self, registry: PieceRegistry | None = None) -> None:
        self._registry = registry or self._build_default_registry()

    def _build_default_registry(self) -> PieceRegistry:
        registry = PieceRegistry()
        registry.register("K", King)
        registry.register("Q", Queen)
        registry.register("R", Rook)
        registry.register("B", Bishop)
        registry.register("N", Knight)
        registry.register("P", Pawn)
        return registry

    def is_legal_move(self, board: Board, start: tuple[int, int], end: tuple[int, int]) -> bool:
        if start == end:
            return False

        start_row, start_col = start
        end_row, end_col = end
        start_token = board.rows[start_row][start_col]
        target_token = board.rows[end_row][end_col]

        if target_token != "." and start_token[0] == target_token[0]:
            return False

        piece_type = start_token[1]
        piece_class = self._registry.rules.get(piece_type)
        if piece_class is None:
            return False

        piece = piece_class(start_token[0])
        return piece.is_legal_move(board, start, end)

    def is_same_color(self, piece_a: str, piece_b: str) -> bool:
        return piece_a != "." and piece_b != "." and piece_a[0] == piece_b[0]

    def apply_end_of_move(self, board: Board, end: tuple[int, int]) -> None:
        end_row, end_col = end
        token = board.rows[end_row][end_col]
        if token == ".":
            return
        piece = self._registry.rules.get(token[1])
        if piece is not None:
            piece(token[0]).on_reach_end(board, end)
