"""Drives every pre-game request/response exchange with the server (login,
then find_match or create_room/join_room) before handing the connection off
to the real in-game message handler. Each exchange is "send one thing, block
for one of a few expected reply types"; anything else that arrives in the
meantime is buffered so nothing is lost by the time RemoteController takes
over (building the GUI app takes long enough that post-seating messages
would otherwise arrive and be dropped)."""

from __future__ import annotations

import threading
from typing import Callable


class HomeGate:
    def __init__(self, ws_client) -> None:
        self._ws = ws_client
        self._lock = threading.Lock()
        self._arrived = threading.Event()
        self._awaiting: tuple[str, ...] = ()
        self._match: dict | None = None
        self._buffered: list[dict] = []
        ws_client.start(self._on_message)

    @property
    def ws_client(self):
        return self._ws

    def send(self, message: dict) -> None:
        self._ws.send(message)

    def wait_for(self, *message_types: str) -> dict:
        """Blocks until a message whose type is one of message_types arrives.
        A matching message that already arrived (before this call, e.g. the
        background socket thread delivered the reply before we started
        waiting) is taken from the buffer instead of blocking. Non-matching
        messages stay buffered, in order, for later replay via handoff()."""
        with self._lock:
            for index, buffered in enumerate(self._buffered):
                if buffered.get("type") in message_types:
                    return self._buffered.pop(index)
            self._awaiting = message_types
            self._match = None
            self._arrived.clear()
        self._arrived.wait()
        with self._lock:
            message = self._match
            self._awaiting = ()
            self._match = None
        return message

    def handoff(self, on_message: Callable[[dict], None]) -> None:
        """Replays anything buffered during the home-screen exchanges into
        on_message. Call this right after the connection has been repointed
        at its real handler (e.g. via ws_client.set_message_handler)."""
        with self._lock:
            buffered, self._buffered = self._buffered, []
        for message in buffered:
            on_message(message)

    def _on_message(self, message: dict) -> None:
        matched = False
        with self._lock:
            if message.get("type") in self._awaiting and self._match is None:
                self._match = message
                matched = True
            else:
                self._buffered.append(message)
        if matched:
            self._arrived.set()
