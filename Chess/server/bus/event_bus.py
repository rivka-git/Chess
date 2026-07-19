"""Synchronous in-process publish/subscribe event bus."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)

Handler = Callable[[dict[str, Any]], None]


class EventBus:
    """Decouples "something happened" from "who reacts to it"."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        payload = payload if payload is not None else {}
        for handler in self._subscribers[event_type]:
            try:
                handler(payload)
            except Exception:
                # One misbehaving subscriber must not block others or the publisher.
                logger.exception("Event handler for %r raised an exception", event_type)
