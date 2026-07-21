"""In-memory matchmaking queue: pure data structure, no networking/asyncio,
so pairing/timeout rules can be tested without a running event loop."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

RATING_RANGE = 100
TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class QueueEntry:
    username: str
    rating: int
    connection: Any
    joined_at: float


class MatchmakingQueue:
    def __init__(self) -> None:
        self._entries: dict[str, QueueEntry] = {}

    def add(self, username: str, rating: int, connection: Any, joined_at: float | None = None) -> None:
        self._entries[username] = QueueEntry(
            username, rating, connection, joined_at if joined_at is not None else time.monotonic()
        )

    def remove(self, username: str) -> None:
        self._entries.pop(username, None)

    def find_match(self, rating: int) -> QueueEntry | None:
        """Closest-rating waiting entry within RATING_RANGE, or None."""
        candidates = [entry for entry in self._entries.values() if abs(entry.rating - rating) <= RATING_RANGE]
        if not candidates:
            return None
        return min(candidates, key=lambda entry: abs(entry.rating - rating))

    def expired(self, now: float | None = None) -> list[QueueEntry]:
        now = now if now is not None else time.monotonic()
        return [entry for entry in self._entries.values() if now - entry.joined_at >= TIMEOUT_SECONDS]
