"""Tests for broadcaster.broadcast_state and TickLoop."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from server.bus import events
from server.bus.event_bus import EventBus
from server.game.broadcaster import broadcast_state
from server.game.tick_loop import TickLoop
from server.server_config import TICK_MS


def _patched_run(loop: TickLoop):
    """Returns a version of _run() with sleep=0 so tests don't wait TICK_MS."""
    async def _run():
        while True:
            await asyncio.sleep(0)
            snapshot_before = loop._controller.get_snapshot()
            loop._controller.update(TICK_MS)
            snapshot_after = loop._controller.get_snapshot()
            loop._publish_tick_events(snapshot_before, snapshot_after)
            await loop._broadcast()
            if snapshot_after.game_over:
                break
    return _run


# --- broadcaster ---

@pytest.mark.asyncio
async def test_broadcast_state_sends_to_all_connections():
    conn_w = AsyncMock()
    conn_b = AsyncMock()
    connections = {"w": conn_w, "b": conn_b}

    snapshot = MagicMock()
    snapshot.clock = 0
    snapshot.board = []
    snapshot.pending_moves = []
    snapshot.jumps = []
    snapshot.selected_position = None
    snapshot.legal_targets = []
    snapshot.game_over = False

    await broadcast_state(connections, lambda color: snapshot)

    conn_w.send_json.assert_called_once()
    conn_b.send_json.assert_called_once()
    assert conn_w.send_json.call_args[0][0]["type"] == "state"
    assert conn_b.send_json.call_args[0][0]["type"] == "state"


@pytest.mark.asyncio
async def test_broadcast_state_skips_failed_connection():
    conn_ok = AsyncMock()
    conn_bad = AsyncMock()
    conn_bad.send_json.side_effect = Exception("disconnected")
    connections = {"w": conn_ok, "b": conn_bad}

    snapshot = MagicMock()
    snapshot.clock = 0
    snapshot.board = []
    snapshot.pending_moves = []
    snapshot.jumps = []
    snapshot.selected_position = None
    snapshot.legal_targets = []
    snapshot.game_over = False

    await broadcast_state(connections, lambda color: snapshot)

    conn_ok.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_broadcast_state_empty_connections():
    await broadcast_state({}, lambda color: MagicMock())


# --- tick_loop ---

def _make_snapshot(game_over=False, piece_count=2):
    snapshot = MagicMock()
    snapshot.game_over = game_over
    pieces = [MagicMock() for _ in range(piece_count)]
    snapshot.board = [pieces]
    snapshot.pending_moves = []
    snapshot.jumps = []
    snapshot.selected_position = None
    snapshot.legal_targets = []
    snapshot.clock = 0
    return snapshot


@pytest.mark.asyncio
async def test_tick_loop_publishes_game_ended_when_game_over():
    bus = EventBus()
    ended = []
    bus.subscribe(events.GAME_ENDED, lambda p: ended.append(p))

    snapshot_before = _make_snapshot(game_over=False)
    snapshot_after = _make_snapshot(game_over=True)

    controller = MagicMock()
    controller.get_snapshot.side_effect = [snapshot_before, snapshot_after, snapshot_after]
    controller.update = MagicMock()

    conn = AsyncMock()
    connections = {"w": conn}

    loop = TickLoop("room1", controller, connections, bus)
    loop._run = _patched_run(loop)

    task = asyncio.create_task(loop._run())
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert any(e.get("reason") == "king_captured" for e in ended)


@pytest.mark.asyncio
async def test_tick_loop_publishes_piece_captured():
    bus = EventBus()
    captured = []
    bus.subscribe(events.PIECE_CAPTURED, lambda p: captured.append(p))

    snapshot_before = _make_snapshot(piece_count=2)
    snapshot_after = _make_snapshot(piece_count=1, game_over=True)

    controller = MagicMock()
    controller.get_snapshot.side_effect = [snapshot_before, snapshot_after, snapshot_after]
    controller.update = MagicMock()

    conn = AsyncMock()
    loop = TickLoop("room1", controller, {"w": conn}, bus)
    loop._run = _patched_run(loop)

    task = asyncio.create_task(loop._run())
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert len(captured) >= 1


def test_tick_loop_stop_cancels_task():
    bus = EventBus()
    controller = MagicMock()
    loop = TickLoop("room1", controller, {}, bus)
    mock_task = MagicMock()
    loop._task = mock_task
    loop.stop()
    mock_task.cancel.assert_called_once()


def test_tick_loop_stop_with_no_task_does_not_raise():
    bus = EventBus()
    loop = TickLoop("room1", MagicMock(), {}, bus)
    loop.stop()  # _task is None
