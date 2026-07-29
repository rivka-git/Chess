"""Data access for player accounts (PostgreSQL / asyncpg)."""

from __future__ import annotations

from dataclasses import dataclass

import asyncpg


@dataclass(frozen=True)
class Player:
    id: int
    username: str
    password_hash: str
    password_salt: str
    rating: int
    created_at: str


class PlayerRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, username: str, password_hash: str, password_salt: str, rating: int = 1200) -> Player:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO players (username, password_hash, password_salt, rating, created_at) "
                "VALUES ($1, $2, $3, $4, now()) RETURNING *",
                username, password_hash, password_salt, rating,
            )
        return _row_to_player(row)

    async def get_by_username(self, username: str) -> Player | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM players WHERE username = $1", username)
        return None if row is None else _row_to_player(row)

    async def update_rating(self, username: str, new_rating: int) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("UPDATE players SET rating = $1 WHERE username = $2", new_rating, username)


def _row_to_player(row: asyncpg.Record) -> Player:
    return Player(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
        password_salt=row["password_salt"],
        rating=row["rating"],
        created_at=str(row["created_at"]),
    )
