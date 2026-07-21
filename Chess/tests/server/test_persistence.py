"""Unit tests for server.persistence: schema bootstrap + the three repositories.

Every test uses an in-memory SQLite connection -- fast, isolated, no file cleanup.
"""

import sqlite3

import pytest

from server.persistence.db import ensure_schema
from server.persistence.game_repository import GameRepository
from server.persistence.move_repository import MoveRepository
from server.persistence.player_repository import PlayerRepository


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    ensure_schema(connection)
    yield connection
    connection.close()


def test_ensure_schema_is_idempotent(conn):
    ensure_schema(conn)  # must not raise on a second call
    tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"players", "games", "moves"} <= tables


# --- PlayerRepository ---

def test_create_player_defaults_rating_to_1200(conn):
    repo = PlayerRepository(conn)
    player = repo.create("alice", "hash", "salt")
    assert player.username == "alice"
    assert player.rating == 1200


def test_get_by_username_returns_none_when_missing(conn):
    repo = PlayerRepository(conn)
    assert repo.get_by_username("nobody") is None


def test_get_by_username_returns_created_player(conn):
    repo = PlayerRepository(conn)
    repo.create("bob", "h", "s")
    found = repo.get_by_username("bob")
    assert found is not None
    assert found.username == "bob"
    assert found.password_hash == "h"
    assert found.password_salt == "s"


def test_create_duplicate_username_raises(conn):
    repo = PlayerRepository(conn)
    repo.create("carol", "h", "s")
    with pytest.raises(sqlite3.IntegrityError):
        repo.create("carol", "h2", "s2")


def test_update_rating_persists(conn):
    repo = PlayerRepository(conn)
    repo.create("dave", "h", "s")
    repo.update_rating("dave", 1350)
    assert repo.get_by_username("dave").rating == 1350


# --- GameRepository ---

def test_create_game_returns_incrementing_id(conn):
    repo = GameRepository(conn)
    game_id = repo.create_game("room-1", "alice", "bob", "2026-01-01T00:00:00")
    assert isinstance(game_id, int)


def test_finish_game_sets_winner_reason_and_ended_at(conn):
    repo = GameRepository(conn)
    game_id = repo.create_game("room-1", "alice", "bob", "2026-01-01T00:00:00")
    repo.finish_game(game_id, winner="white", reason="king_captured", ended_at="2026-01-01T00:05:00")
    row = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
    assert row["winner"] == "white"
    assert row["reason"] == "king_captured"
    assert row["ended_at"] == "2026-01-01T00:05:00"


def test_get_games_for_player_matches_white_or_black(conn):
    repo = GameRepository(conn)
    repo.create_game("room-1", "alice", "bob", "t1")
    repo.create_game("room-2", "carol", "alice", "t2")
    repo.create_game("room-3", "carol", "dave", "t3")
    games = repo.get_games_for_player("alice")
    assert {g["room_id"] for g in games} == {"room-1", "room-2"}


# --- MoveRepository ---

def test_add_move_and_get_moves_for_game_orders_by_seq(conn):
    game_repo = GameRepository(conn)
    move_repo = MoveRepository(conn)
    game_id = game_repo.create_game("room-1", "alice", "bob", "t1")

    move_repo.add_move(game_id, seq=2, color="b", start=(6, 1), end=(5, 1), clock_tick=1.5)
    move_repo.add_move(game_id, seq=1, color="w", start=(1, 0), end=(2, 0), clock_tick=0.5)

    moves = move_repo.get_moves_for_game(game_id)
    assert [m["seq"] for m in moves] == [1, 2]
    assert (moves[0]["start_row"], moves[0]["start_col"]) == (1, 0)
    assert (moves[0]["end_row"], moves[0]["end_col"]) == (2, 0)


def test_get_moves_for_player_joins_across_games(conn):
    game_repo = GameRepository(conn)
    move_repo = MoveRepository(conn)
    game1 = game_repo.create_game("room-1", "alice", "bob", "t1")
    game2 = game_repo.create_game("room-2", "carol", "alice", "t2")
    game3 = game_repo.create_game("room-3", "carol", "dave", "t3")

    move_repo.add_move(game1, 1, "w", (0, 0), (1, 0), 0.1)
    move_repo.add_move(game2, 1, "b", (6, 0), (5, 0), 0.1)
    move_repo.add_move(game3, 1, "w", (0, 0), (1, 0), 0.1)

    moves = move_repo.get_moves_for_player("alice")
    assert len(moves) == 2
    assert {m["game_id"] for m in moves} == {game1, game2}
