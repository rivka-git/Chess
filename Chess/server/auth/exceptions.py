"""Auth domain errors."""

from __future__ import annotations


class InvalidCredentialsError(Exception):
    """Raised when a username exists but the supplied password does not match it."""
