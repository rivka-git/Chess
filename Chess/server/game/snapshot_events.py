"""Pure snapshot-inspection helpers used by the tick loop."""

from __future__ import annotations


def count_pieces(snapshot) -> int:
    return sum(1 for row in snapshot.board for piece in row if piece is not None)


def has_promotion(before, after) -> bool:
    for row_b, row_a in zip(before.board, after.board):
        for piece_b, piece_a in zip(row_b, row_a):
            if piece_b is None or piece_a is None:
                continue
            if (
                piece_b.token in {"wP", "bP"}
                and piece_a.token in {"wQ", "bQ"}
                and piece_b.token[0] == piece_a.token[0]
            ):
                return True
    return False


def winner_color(snapshot) -> str | None:
    tokens = {piece.token for row in snapshot.board for piece in row if piece is not None}
    if "wK" in tokens and "bK" not in tokens:
        return "w"
    if "bK" in tokens and "wK" not in tokens:
        return "b"
    return None
