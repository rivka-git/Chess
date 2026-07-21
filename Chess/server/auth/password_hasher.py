"""Password hashing via PBKDF2-HMAC-SHA256 (stdlib hashlib -- no third-party
dependency needed for this project's scope)."""

from __future__ import annotations

import hashlib
import hmac
import os

DEFAULT_ITERATIONS = 200_000


class PasswordHasher:
    def __init__(self, iterations: int = DEFAULT_ITERATIONS) -> None:
        self._iterations = iterations

    def hash(self, password: str) -> tuple[str, str]:
        salt = os.urandom(16).hex()
        return self._derive(password, salt), salt

    def verify(self, password: str, password_hash: str, salt: str) -> bool:
        return hmac.compare_digest(self._derive(password, salt), password_hash)

    def _derive(self, password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), self._iterations
        ).hex()
