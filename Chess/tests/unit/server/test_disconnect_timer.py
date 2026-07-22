"""Unit tests for server.game.disconnect_timer.DisconnectTimer.

A no-op sleep is injected so the countdown runs to completion instantly
instead of taking real seconds.
"""

import asyncio

import pytest

from server.game.disconnect_timer import DisconnectTimer


async def _instant_sleep(_seconds):
    pass


@pytest.mark.asyncio
async def test_counts_down_each_second_then_times_out():
    ticks = []
    timed_out = []

    async def on_tick(remaining):
        ticks.append(remaining)

    async def on_timeout():
        timed_out.append(True)

    timer = DisconnectTimer(3, on_tick=on_tick, on_timeout=on_timeout, sleep=_instant_sleep)
    timer.start()
    await asyncio.sleep(0)  # let the task run to completion
    while ticks == [] or not timed_out:
        await asyncio.sleep(0)

    assert ticks == [3, 2, 1]
    assert timed_out == [True]


@pytest.mark.asyncio
async def test_cancel_prevents_timeout():
    timed_out = []

    async def on_tick(remaining):
        await asyncio.sleep(0.01)

    async def on_timeout():
        timed_out.append(True)

    timer = DisconnectTimer(5, on_tick=on_tick, on_timeout=on_timeout)
    timer.start()
    await asyncio.sleep(0)
    timer.cancel()
    await asyncio.sleep(0.05)

    assert timed_out == []
