"""Unit tests for server.rating.rating_service.RatingService."""

import sqlite3

import pytest

from server.bus import events
from server.bus.event_bus import EventBus
from server.persistence.db import ensure_schema
from server.persistence.player_repository import PlayerRepository
from server.rating.rating_service import RatingService


@pytest.fixture
def setup():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    players = PlayerRepository(conn)
    players.create("alice", "h", "s", rating=1200)
    players.create("bob", "h", "s", rating=1200)
    bus = EventBus()
    RatingService(players, bus)
    return players, bus


def test_game_ended_updates_both_players_ratings(setup):
    players, bus = setup
    bus.publish(events.GAME_ENDED, {
        "room_id": "r1", "winner": "white", "reason": "king_captured",
        "white": "alice", "black": "bob",
    })

    assert players.get_by_username("alice").rating == 1216
    assert players.get_by_username("bob").rating == 1184


def test_draw_leaves_equal_ratings_unchanged(setup):
    players, bus = setup
    bus.publish(events.GAME_ENDED, {
        "room_id": "r1", "winner": None, "reason": "stalemate",
        "white": "alice", "black": "bob",
    })

    assert players.get_by_username("alice").rating == 1200
    assert players.get_by_username("bob").rating == 1200


def test_game_ended_publishes_elo_updated_with_before_and_after(setup):
    players, bus = setup
    published = []
    bus.subscribe(events.ELO_UPDATED, lambda payload: published.append(payload))

    bus.publish(events.GAME_ENDED, {
        "room_id": "r1", "winner": "black", "reason": "king_captured",
        "white": "alice", "black": "bob",
    })

    assert len(published) == 1
    payload = published[0]
    assert payload["white"] == {"username": "alice", "old_rating": 1200, "new_rating": 1184}
    assert payload["black"] == {"username": "bob", "old_rating": 1200, "new_rating": 1216}


def test_game_ended_without_usernames_is_ignored(setup):
    players, bus = setup
    bus.publish(events.GAME_ENDED, {"room_id": "r1", "winner": "white", "reason": "king_captured"})

    assert players.get_by_username("alice").rating == 1200
    assert players.get_by_username("bob").rating == 1200


def test_game_ended_with_unknown_player_does_not_raise(setup):
    players, bus = setup
    bus.publish(events.GAME_ENDED, {
        "room_id": "r1", "winner": "white", "reason": "king_captured",
        "white": "alice", "black": "nobody",
    })  # must not raise

    assert players.get_by_username("alice").rating == 1200
