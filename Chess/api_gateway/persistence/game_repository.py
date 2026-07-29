"""Data access for game history (PostgreSQL / asyncpg)."""

from __future__ import annotations

import asyncpg


class GameRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_games_for_player(self, username: str) -> list[asyncpg.Record]:
        async with self._pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM games WHERE white_username = $1 OR black_username = $1 ORDER BY started_at",
                username,
            )
