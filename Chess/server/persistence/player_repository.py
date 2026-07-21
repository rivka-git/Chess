"""Data access for player accounts. No auth or rating logic lives here --
this repository only reads and writes rows."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Player:
    id: int
    username: str
    password_hash: str
    password_salt: str
    rating: int
    created_at: str


class PlayerRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create(self, username: str, password_hash: str, password_salt: str, rating: int = 1200) -> Player:
        self._conn.execute(
            "INSERT INTO players (username, password_hash, password_salt, rating, created_at) "
            "VALUES (?, ?, ?, ?, datetime('now'))",
            (username, password_hash, password_salt, rating),
        )
        self._conn.commit()
        return self.get_by_username(username)

    def get_by_username(self, username: str) -> Player | None:
        row = self._conn.execute(
            "SELECT * FROM players WHERE username = ?", (username,)
        ).fetchone()
        return None if row is None else Player(**dict(row))

    def update_rating(self, username: str, new_rating: int) -> None:
        self._conn.execute(
            "UPDATE players SET rating = ? WHERE username = ?", (new_rating, username)
        )
        self._conn.commit()
