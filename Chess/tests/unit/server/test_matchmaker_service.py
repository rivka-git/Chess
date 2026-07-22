"""Unit tests for server.matchmaking.matchmaker_service.MatchmakerService."""

import asyncio
import json

import pytest
import pytest_asyncio

from server.bus.event_bus import EventBus
from server.game.session_manager import SessionManager
from server.matchmaking.matchmaker_service import MatchmakerService
from server.matchmaking.matchmaking_queue import MatchmakingQueue


class FakeWebSocket:
    def __init__(self):
        self.sent = []

    async def send(self, raw):
        self.sent.append(json.loads(raw))


class FakeConnection:
    def __init__(self, username, rating):
        self.username = username
        self.player = type("Player", (), {"rating": rating})()
        self.websocket = FakeWebSocket()
        self.color = None
        self.room_id = None
        self.is_spectator = False

    async def send_json(self, message):
        await self.websocket.send(json.dumps(message))


@pytest_asyncio.fixture(autouse=True)
async def _cancel_background_tasks():
    yield
    current = asyncio.current_task()
    pending = [task for task in asyncio.all_tasks() if task is not current]
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


def make_service():
    return MatchmakerService(MatchmakingQueue(), SessionManager(EventBus()), EventBus())


@pytest.mark.asyncio
async def test_first_player_gets_searching_match_and_is_not_seated():
    service = make_service()
    alice = FakeConnection("alice", 1200)

    await service.handle_find_match(alice)

    assert alice.websocket.sent == [{"type": "searching_match"}]
    assert alice.room_id is None


@pytest.mark.asyncio
async def test_second_compatible_player_completes_the_match():
    service = make_service()
    alice = FakeConnection("alice", 1200)
    bob = FakeConnection("bob", 1250)

    await service.handle_find_match(alice)
    await service.handle_find_match(bob)

    assert alice.color == "w"
    assert bob.color == "b"
    assert alice.room_id == bob.room_id


@pytest.mark.asyncio
async def test_forget_removes_a_waiting_player_so_they_are_not_matched_later():
    service = make_service()
    alice = FakeConnection("alice", 1200)
    bob = FakeConnection("bob", 1200)

    await service.handle_find_match(alice)
    service.forget("alice")
    await service.handle_find_match(bob)

    assert bob.websocket.sent[-1] == {"type": "searching_match"}
    assert bob.room_id is None


@pytest.mark.asyncio
async def test_sweep_expired_notifies_timed_out_waiters():
    service = make_service()
    alice = FakeConnection("alice", 1200)
    service._queue.add("alice", 1200, alice, joined_at=0.0)  # pretend they've been waiting a while

    await service.sweep_expired()

    assert alice.websocket.sent[-1]["type"] == "no_match_found"
