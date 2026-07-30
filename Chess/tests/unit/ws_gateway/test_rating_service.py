import asyncio

import pytest

from ws_gateway.bus import events
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.persistence.player_repository import Player
from ws_gateway.rating.rating_service import RatingService


class FakePlayerRepository:
    def __init__(self):
        self._store: dict = {}

    def seed(self, username, rating):
        self._store[username] = Player(id=1, username=username, password_hash="h",
                                       password_salt="s", rating=rating, created_at="")

    async def get_by_username(self, username):
        return self._store.get(username)

    async def update_rating(self, username, new_rating):
        p = self._store[username]
        self._store[username] = Player(p.id, p.username, p.password_hash, p.password_salt, new_rating, p.created_at)


async def _flush():
    await asyncio.sleep(0)
    await asyncio.sleep(0)


@pytest.fixture
def setup():
    players = FakePlayerRepository()
    players.seed("alice", 1200)
    players.seed("bob", 1200)
    bus = EventBus()
    RatingService(players, bus)
    return players, bus


@pytest.mark.asyncio
async def test_game_ended_updates_both_players_ratings(setup):
    players, bus = setup
    bus.publish(events.GAME_ENDED, {
        "room_id": "r1", "winner": "white", "reason": "king_captured",
        "white": "alice", "black": "bob",
    })
    await _flush()

    assert (await players.get_by_username("alice")).rating == 1216
    assert (await players.get_by_username("bob")).rating == 1184


@pytest.mark.asyncio
async def test_draw_leaves_equal_ratings_unchanged(setup):
    players, bus = setup
    bus.publish(events.GAME_ENDED, {
        "room_id": "r1", "winner": None, "reason": "stalemate",
        "white": "alice", "black": "bob",
    })
    await _flush()

    assert (await players.get_by_username("alice")).rating == 1200
    assert (await players.get_by_username("bob")).rating == 1200


@pytest.mark.asyncio
async def test_game_ended_publishes_elo_updated_with_before_and_after(setup):
    players, bus = setup
    published = []
    bus.subscribe(events.ELO_UPDATED, lambda payload: published.append(payload))

    bus.publish(events.GAME_ENDED, {
        "room_id": "r1", "winner": "black", "reason": "king_captured",
        "white": "alice", "black": "bob",
    })
    await _flush()

    assert len(published) == 1
    payload = published[0]
    assert payload["white"] == {"username": "alice", "old_rating": 1200, "new_rating": 1184}
    assert payload["black"] == {"username": "bob", "old_rating": 1200, "new_rating": 1216}


@pytest.mark.asyncio
async def test_game_ended_without_usernames_is_ignored(setup):
    players, bus = setup
    bus.publish(events.GAME_ENDED, {"room_id": "r1", "winner": "white", "reason": "king_captured"})
    await _flush()

    assert (await players.get_by_username("alice")).rating == 1200
    assert (await players.get_by_username("bob")).rating == 1200


@pytest.mark.asyncio
async def test_game_ended_with_unknown_player_does_not_raise(setup):
    players, bus = setup
    bus.publish(events.GAME_ENDED, {
        "room_id": "r1", "winner": "white", "reason": "king_captured",
        "white": "alice", "black": "nobody",
    })
    await _flush()

    assert (await players.get_by_username("alice")).rating == 1200
