"""Data access for individual moves. get_moves_for_player is a query over the
same games+moves tables required for game history -- a player's personal move
history is not a separate stored concept."""

from __future__ import annotations

import sqlite3


class MoveRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add_move(
        self,
        game_id: int,
        seq: int,
        color: str,
        start: tuple[int, int],
        end: tuple[int, int],
        clock_tick: float,
    ) -> None:
        self._conn.execute(
            "INSERT INTO moves (game_id, seq, color, start_row, start_col, end_row, end_col, clock_tick) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (game_id, seq, color, start[0], start[1], end[0], end[1], clock_tick),
        )
        self._conn.commit()

    def get_moves_for_game(self, game_id: int) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM moves WHERE game_id = ? ORDER BY seq", (game_id,)
        ).fetchall()

    def get_moves_for_player(self, username: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            """
            SELECT moves.* FROM moves
            JOIN games ON games.id = moves.game_id
            WHERE games.white_username = ? OR games.black_username = ?
            ORDER BY moves.game_id, moves.seq
            """,
            (username, username),
        ).fetchall()
