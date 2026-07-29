"""Redis-backed matchmaking queue.

Layout in Redis:
  mm:entry:{username}  → Hash  { rating, joined_at }
  mm:connections       → in-process dict (connections cannot be serialised)

The connection object lives only in memory; Redis stores the metadata needed
for matching and timeout detection so the queue survives a process restart
(connections will be gone, but the sweep will clean up stale entries).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import redis.asyncio as aioredis

RATING_RANGE = 100
TIMEOUT_SECONDS = 60
_KEY_PREFIX = "mm:entry:"


@dataclass
class QueueEntry:
    username: str
    rating: int
    connection: Any
    joined_at: float


class RedisMatchmakingQueue:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis
        # connections cannot be stored in Redis — kept in-process
        self._connections: dict[str, QueueEntry] = {}

    async def add(self, username: str, rating: int, connection: Any) -> None:
        joined_at = time.time()
        entry = QueueEntry(username, rating, connection, joined_at)
        self._connections[username] = entry
        await self._redis.hset(
            f"{_KEY_PREFIX}{username}",
            mapping={"rating": rating, "joined_at": joined_at},
        )
        await self._redis.expire(f"{_KEY_PREFIX}{username}", TIMEOUT_SECONDS + 10)

    async def remove(self, username: str) -> None:
        self._connections.pop(username, None)
        await self._redis.delete(f"{_KEY_PREFIX}{username}")

    async def find_match(self, rating: int) -> QueueEntry | None:
        """Returns the closest-rating waiting entry within RATING_RANGE, or None."""
        candidates: list[QueueEntry] = []
        for entry in self._connections.values():
            if abs(entry.rating - rating) <= RATING_RANGE:
                candidates.append(entry)
        if not candidates:
            return None
        return min(candidates, key=lambda e: abs(e.rating - rating))

    async def expired(self) -> list[QueueEntry]:
        now = time.time()
        return [e for e in self._connections.values() if now - e.joined_at >= TIMEOUT_SECONDS]
