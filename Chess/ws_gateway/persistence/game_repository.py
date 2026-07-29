"""Data access for game history (PostgreSQL / asyncpg)."""

from __future__ import annotations

import asyncpg


class GameRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create_game(self, room_id: str, white_username: str, black_username: str, started_at: str) -> int:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO games (room_id, white_username, black_username, started_at) "
                "VALUES ($1, $2, $3, $4) RETURNING id",
                room_id, white_username, black_username, started_at,
            )
        return row["id"]

    async def finish_game(self, game_id: int, winner: str | None, reason: str, ended_at: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE games SET winner = $1, reason = $2, ended_at = $3 WHERE id = $4",
                winner, reason, ended_at, game_id,
            )
