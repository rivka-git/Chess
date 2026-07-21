"""Unit tests for server.persistence.game_history_recorder.GameHistoryRecorder."""

import sqlite3

import pytest

from server.bus import events
from server.bus.event_bus import EventBus
from server.persistence.db import ensure_schema
from server.persistence.game_history_recorder import GameHistoryRecorder
from server.persistence.game_repository import GameRepository
from server.persistence.move_repository import MoveRepository


@pytest.fixture
def setup():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    games = GameRepository(conn)
    moves = MoveRepository(conn)
    bus = EventBus()
    GameHistoryRecorder(games, moves, bus)
    return games, moves, bus


def test_game_started_creates_a_game_row(setup):
    games, moves, bus = setup
    bus.publish(events.GAME_STARTED, {"room_id": "r1", "white": "alice", "black": "bob"})

    alice_games = games.get_games_for_player("alice")
    assert len(alice_games) == 1
    assert alice_games[0]["white_username"] == "alice"
    assert alice_games[0]["black_username"] == "bob"
    assert alice_games[0]["ended_at"] is None


def test_moves_are_recorded_in_order_for_the_started_game(setup):
    games, moves, bus = setup
    bus.publish(events.GAME_STARTED, {"room_id": "r1", "white": "alice", "black": "bob"})
    bus.publish(events.MOVE_MADE, {
        "room_id": "r1", "start": (1, 0), "end": (2, 0), "color": "w", "clock_tick": 0.1,
    })
    bus.publish(events.MOVE_MADE, {
        "room_id": "r1", "start": (6, 0), "end": (5, 0), "color": "b", "clock_tick": 0.2,
    })

    game_id = games.get_games_for_player("alice")[0]["id"]
    recorded = moves.get_moves_for_game(game_id)
    assert [m["seq"] for m in recorded] == [1, 2]
    assert (recorded[0]["start_row"], recorded[0]["start_col"]) == (1, 0)
    assert recorded[1]["color"] == "b"


def test_game_ended_sets_winner_reason_and_ended_at(setup):
    games, moves, bus = setup
    bus.publish(events.GAME_STARTED, {"room_id": "r1", "white": "alice", "black": "bob"})
    bus.publish(events.GAME_ENDED, {
        "room_id": "r1", "winner": "white", "reason": "king_captured", "white": "alice", "black": "bob",
    })

    row = games.get_games_for_player("alice")[0]
    assert row["winner"] == "white"
    assert row["reason"] == "king_captured"
    assert row["ended_at"] is not None


def test_move_made_for_unknown_room_is_ignored(setup):
    games, moves, bus = setup
    bus.publish(events.MOVE_MADE, {"room_id": "unknown", "start": (0, 0), "end": (1, 0), "color": "w"})  # must not raise
    assert moves.get_moves_for_player("alice") == []


def test_second_game_in_same_room_after_first_ends_gets_its_own_row(setup):
    games, moves, bus = setup
    bus.publish(events.GAME_STARTED, {"room_id": "r1", "white": "alice", "black": "bob"})
    bus.publish(events.GAME_ENDED, {
        "room_id": "r1", "winner": "white", "reason": "king_captured", "white": "alice", "black": "bob",
    })
    bus.publish(events.GAME_STARTED, {"room_id": "r1", "white": "alice", "black": "carol"})

    alice_games = games.get_games_for_player("alice")
    assert len(alice_games) == 2
    assert alice_games[1]["black_username"] == "carol"
