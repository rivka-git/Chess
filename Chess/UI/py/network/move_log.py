"""Builds an ordered move history on the client purely by observing successive
server snapshots: whenever a new pending move appears, it's recorded. The
mover's color is read from the previous snapshot (where the piece still sat on
its start square). Thread-safe because snapshots arrive on the socket thread
while the renderer reads the log on the main thread."""

from __future__ import annotations

import threading

from netcommon.coordinates import rowcol_to_square


def _color_at(snapshot, position) -> str:
    row, col = position
    board = snapshot.board
    if 0 <= row < len(board) and board and 0 <= col < len(board[0]):
        piece = board[row][col]
        if piece is not None:
            return piece.token[0]
    return "?"


class MoveLog:
    def __init__(self) -> None:
        self._entries: list[tuple[int, str, tuple[int, int], tuple[int, int]]] = []
        self._lock = threading.Lock()

    def observe(self, previous, current) -> None:
        previous_ids = {
            (tuple(m.start), tuple(m.end), m.arrival_clock) for m in previous.pending_moves
        }
        for move in current.pending_moves:
            if (tuple(move.start), tuple(move.end), move.arrival_clock) in previous_ids:
                continue
            color = _color_at(previous, move.start)
            with self._lock:
                self._entries.append(
                    (len(self._entries) + 1, color, tuple(move.start), tuple(move.end))
                )

    def entries(self) -> list[tuple[int, str, tuple[int, int], tuple[int, int]]]:
        with self._lock:
            return list(self._entries)

    def lines(self) -> list[str]:
        with self._lock:
            return [
                f"{seq}. {color} {rowcol_to_square(*start)}->{rowcol_to_square(*end)}"
                for seq, color, start, end in self._entries
            ]
