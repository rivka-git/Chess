"""Room domain errors."""

from __future__ import annotations


class RoomNotFoundError(Exception):
    """Raised when joining a room id that has no active session."""
