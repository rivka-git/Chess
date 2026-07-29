"""PostgreSQL connection pool bootstrap for the WebSocket Gateway."""

from __future__ import annotations

import os

import asyncpg

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://chess:chess@localhost:5432/chess",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id            SERIAL PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    rating        INTEGER NOT NULL DEFAULT 1200,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS games (
    id              SERIAL PRIMARY KEY,
    room_id         TEXT NOT NULL,
    white_username  TEXT NOT NULL,
    black_username  TEXT NOT NULL,
    winner          TEXT,
    reason          TEXT,
    started_at      TIMESTAMPTZ NOT NULL,
    ended_at        TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_games_white ON games(white_username);
CREATE INDEX IF NOT EXISTS idx_games_black ON games(black_username);

CREATE TABLE IF NOT EXISTS moves (
    id          SERIAL PRIMARY KEY,
    game_id     INTEGER NOT NULL REFERENCES games(id),
    seq         INTEGER NOT NULL,
    color       TEXT NOT NULL,
    start_row   INTEGER NOT NULL,
    start_col   INTEGER NOT NULL,
    end_row     INTEGER NOT NULL,
    end_col     INTEGER NOT NULL,
    clock_tick  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_moves_game ON moves(game_id);
"""


async def create_pool() -> asyncpg.Pool:
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute(_SCHEMA)
    return pool
