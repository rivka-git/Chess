"""Login/registration logic for the API Gateway (async)."""

from __future__ import annotations

from api_gateway.auth.exceptions import InvalidCredentialsError
from api_gateway.auth.password_hasher import PasswordHasher
from api_gateway.persistence.player_repository import Player, PlayerRepository


class AuthService:
    def __init__(self, player_repository: PlayerRepository, password_hasher: PasswordHasher) -> None:
        self._players = player_repository
        self._hasher = password_hasher

    async def login_or_register(self, username: str, password: str) -> Player:
        existing = await self._players.get_by_username(username)
        if existing is None:
            password_hash, salt = self._hasher.hash(password)
            return await self._players.create(username, password_hash, salt)
        if not self._hasher.verify(password, existing.password_hash, existing.password_salt):
            raise InvalidCredentialsError(f"Wrong password for {username!r}")
        return existing
