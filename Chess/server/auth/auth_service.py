"""Login/registration. Chosen semantics for this project (see CTD26 plan):
an unknown username auto-registers at the default rating rather than
requiring a separate sign-up step."""

from __future__ import annotations

from server.auth.exceptions import InvalidCredentialsError
from server.auth.password_hasher import PasswordHasher
from server.persistence.player_repository import Player, PlayerRepository


class AuthService:
    def __init__(self, player_repository: PlayerRepository, password_hasher: PasswordHasher) -> None:
        self._players = player_repository
        self._hasher = password_hasher

    def login_or_register(self, username: str, password: str) -> Player:
        existing = self._players.get_by_username(username)
        if existing is None:
            password_hash, salt = self._hasher.hash(password)
            return self._players.create(username, password_hash, salt)
        if not self._hasher.verify(password, existing.password_hash, existing.password_salt):
            raise InvalidCredentialsError(f"Wrong password for {username!r}")
        return existing
