"""Data access for game history: one row per game, from start to finish."""

from __future__ import annotations

import sqlite3


class GameRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create_game(self, room_id: str, white_username: str, black_username: str, started_at: str) -> int:
        cursor = self._conn.execute(
            "INSERT INTO games (room_id, white_username, black_username, started_at) "
            "VALUES (?, ?, ?, ?)",
            (room_id, white_username, black_username, started_at),
        )
        self._conn.commit()
        return cursor.lastrowid

    def finish_game(self, game_id: int, winner: str | None, reason: str, ended_at: str) -> None:
        self._conn.execute(
            "UPDATE games SET winner = ?, reason = ?, ended_at = ? WHERE id = ?",
            (winner, reason, ended_at, game_id),
        )
        self._conn.commit()

    def get_games_for_player(self, username: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM games WHERE white_username = ? OR black_username = ? "
            "ORDER BY started_at",
            (username, username),
        ).fetchall()
