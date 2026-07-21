"""SQLite schema bootstrap: the one place table definitions live."""

from __future__ import annotations

import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    rating INTEGER NOT NULL DEFAULT 1200,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    white_username TEXT NOT NULL,
    black_username TEXT NOT NULL,
    winner TEXT,
    reason TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_games_white ON games(white_username);
CREATE INDEX IF NOT EXISTS idx_games_black ON games(black_username);

CREATE TABLE IF NOT EXISTS moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    seq INTEGER NOT NULL,
    color TEXT NOT NULL,
    start_row INTEGER NOT NULL,
    start_col INTEGER NOT NULL,
    end_row INTEGER NOT NULL,
    end_col INTEGER NOT NULL,
    clock_tick REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_moves_game ON moves(game_id);
"""


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()


def connect(db_path: str) -> sqlite3.Connection:
    """Opens (creating if needed) the SQLite file at db_path with the schema applied."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn
