"""Counts down after a player disconnects: ticks once per second (so the
opponent can see a countdown) and then fires a timeout callback. cancel()
exists so a game that ends for another reason first doesn't leave the task
running. The sleep function is injectable so tests need not wait in realtime."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable


class DisconnectTimer:
    def __init__(
        self,
        seconds: int,
        on_tick: Callable[[int], Awaitable[None]],
        on_timeout: Callable[[], Awaitable[None]],
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._seconds = seconds
        self._on_tick = on_tick
        self._on_timeout = on_timeout
        self._sleep = sleep
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    def cancel(self) -> None:
        if self._task is not None:
            self._task.cancel()

    async def _run(self) -> None:
        for remaining in range(self._seconds, 0, -1):
            await self._on_tick(remaining)
            await self._sleep(1)
        await self._on_timeout()
