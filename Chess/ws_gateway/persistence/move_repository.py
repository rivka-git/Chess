"""Data access for individual moves (PostgreSQL / asyncpg)."""

from __future__ import annotations

import asyncpg


class MoveRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def add_move(
        self,
        game_id: int,
        seq: int,
        color: str,
        start: tuple[int, int],
        end: tuple[int, int],
        clock_tick: float,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO moves (game_id, seq, color, start_row, start_col, end_row, end_col, clock_tick) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                game_id, seq, color, start[0], start[1], end[0], end[1], clock_tick,
            )
