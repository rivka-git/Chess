import pytest

from ws_gateway.auth.auth_service import AuthService
from ws_gateway.auth.exceptions import InvalidCredentialsError
from ws_gateway.auth.password_hasher import PasswordHasher
from ws_gateway.persistence.player_repository import Player


def _make_player(username, password, hasher, rating=1200):
    h, s = hasher.hash(password)
    return Player(id=1, username=username, password_hash=h, password_salt=s, rating=rating, created_at="")


class FakePlayerRepository:
    def __init__(self):
        self._store: dict = {}
        self._next_id = 1

    async def get_by_username(self, username):
        return self._store.get(username)

    async def create(self, username, password_hash, password_salt, rating=1200):
        player = Player(id=self._next_id, username=username, password_hash=password_hash,
                        password_salt=password_salt, rating=rating, created_at="")
        self._next_id += 1
        self._store[username] = player
        return player

    async def update_rating(self, username, new_rating):
        p = self._store[username]
        self._store[username] = Player(p.id, p.username, p.password_hash, p.password_salt, new_rating, p.created_at)


@pytest.fixture
def auth_service():
    return AuthService(FakePlayerRepository(), PasswordHasher(iterations=1_000))


@pytest.mark.asyncio
async def test_login_with_unknown_username_auto_registers_at_default_rating(auth_service):
    player = await auth_service.login_or_register("alice", "pw123")
    assert player.username == "alice"
    assert player.rating == 1200


@pytest.mark.asyncio
async def test_login_with_known_username_and_correct_password_succeeds(auth_service):
    await auth_service.login_or_register("alice", "pw123")
    player = await auth_service.login_or_register("alice", "pw123")
    assert player.username == "alice"


@pytest.mark.asyncio
async def test_login_with_known_username_and_wrong_password_raises(auth_service):
    await auth_service.login_or_register("alice", "pw123")
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login_or_register("alice", "wrong")


@pytest.mark.asyncio
async def test_second_login_does_not_create_duplicate_account(auth_service):
    first = await auth_service.login_or_register("alice", "pw123")
    second = await auth_service.login_or_register("alice", "pw123")
    assert first.id == second.id
