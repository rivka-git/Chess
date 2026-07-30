import asyncio

import pytest

from ws_gateway.bus import events
from ws_gateway.bus.event_bus import EventBus
from ws_gateway.persistence.game_history_recorder import GameHistoryRecorder


class FakeGameRepository:
    def __init__(self):
        self._games: list[dict] = []
        self._next_id = 1

    async def create_game(self, room_id, white_username, black_username, started_at):
        game_id = self._next_id
        self._next_id += 1
        self._games.append({
            "id": game_id, "room_id": room_id,
            "white_username": white_username, "black_username": black_username,
            "winner": None, "reason": None, "ended_at": None,
        })
        return game_id

    async def finish_game(self, game_id, winner, reason, ended_at):
        for g in self._games:
            if g["id"] == game_id:
                g["winner"] = winner
                g["reason"] = reason
                g["ended_at"] = ended_at

    def get_games_for_player(self, username):
        return [g for g in self._games if g["white_username"] == username or g["black_username"] == username]


class FakeMoveRepository:
    def __init__(self):
        self._moves: list[dict] = []

    async def add_move(self, game_id, seq, color, start, end, clock_tick):
        self._moves.append({"game_id": game_id, "seq": seq, "color": color,
                            "start_row": start[0], "start_col": start[1],
                            "end_row": end[0], "end_col": end[1]})

    def get_moves_for_game(self, game_id):
        return sorted([m for m in self._moves if m["game_id"] == game_id], key=lambda m: m["seq"])


@pytest.fixture
def setup():
    games = FakeGameRepository()
    moves = FakeMoveRepository()
    bus = EventBus()
    GameHistoryRecorder(games, moves, bus)
    return games, moves, bus


async def _flush():
    """Let asyncio.create_task callbacks run."""
    await asyncio.sleep(0)
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_game_started_creates_a_game_row(setup):
    games, moves, bus = setup
    bus.publish(events.GAME_STARTED, {"room_id": "r1", "white": "alice", "black": "bob"})
    await _flush()

    alice_games = games.get_games_for_player("alice")
    assert len(alice_games) == 1
    assert alice_games[0]["white_username"] == "alice"
    assert alice_games[0]["black_username"] == "bob"
    assert alice_games[0]["ended_at"] is None


@pytest.mark.asyncio
async def test_moves_are_recorded_in_order_for_the_started_game(setup):
    games, moves, bus = setup
    bus.publish(events.GAME_STARTED, {"room_id": "r1", "white": "alice", "black": "bob"})
    await _flush()
    bus.publish(events.MOVE_MADE, {"room_id": "r1", "start": (1, 0), "end": (2, 0), "color": "w", "clock_tick": 0.1})
    bus.publish(events.MOVE_MADE, {"room_id": "r1", "start": (6, 0), "end": (5, 0), "color": "b", "clock_tick": 0.2})
    await _flush()

    game_id = games.get_games_for_player("alice")[0]["id"]
    recorded = moves.get_moves_for_game(game_id)
    assert [m["seq"] for m in recorded] == [1, 2]
    assert (recorded[0]["start_row"], recorded[0]["start_col"]) == (1, 0)
    assert recorded[1]["color"] == "b"


@pytest.mark.asyncio
async def test_game_ended_sets_winner_reason_and_ended_at(setup):
    games, moves, bus = setup
    bus.publish(events.GAME_STARTED, {"room_id": "r1", "white": "alice", "black": "bob"})
    await _flush()
    bus.publish(events.GAME_ENDED, {"room_id": "r1", "winner": "white", "reason": "king_captured", "white": "alice", "black": "bob"})
    await _flush()

    row = games.get_games_for_player("alice")[0]
    assert row["winner"] == "white"
    assert row["reason"] == "king_captured"
    assert row["ended_at"] is not None


@pytest.mark.asyncio
async def test_move_made_for_unknown_room_is_ignored(setup):
    games, moves, bus = setup
    bus.publish(events.MOVE_MADE, {"room_id": "unknown", "start": (0, 0), "end": (1, 0), "color": "w"})
    await _flush()
    assert moves.get_moves_for_game(1) == []


@pytest.mark.asyncio
async def test_second_game_in_same_room_after_first_ends_gets_its_own_row(setup):
    games, moves, bus = setup
    bus.publish(events.GAME_STARTED, {"room_id": "r1", "white": "alice", "black": "bob"})
    await _flush()
    bus.publish(events.GAME_ENDED, {"room_id": "r1", "winner": "white", "reason": "king_captured", "white": "alice", "black": "bob"})
    await _flush()
    bus.publish(events.GAME_STARTED, {"room_id": "r1", "white": "alice", "black": "carol"})
    await _flush()

    alice_games = games.get_games_for_player("alice")
    assert len(alice_games) == 2
    assert alice_games[1]["black_username"] == "carol"
