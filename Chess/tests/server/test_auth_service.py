"""Unit tests for server.auth.auth_service.AuthService."""

import sqlite3

import pytest

from server.auth.auth_service import AuthService
from server.auth.exceptions import InvalidCredentialsError
from server.auth.password_hasher import PasswordHasher
from server.persistence.db import ensure_schema
from server.persistence.player_repository import PlayerRepository


@pytest.fixture
def auth_service():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return AuthService(PlayerRepository(conn), PasswordHasher(iterations=1_000))


def test_login_with_unknown_username_auto_registers_at_default_rating(auth_service):
    player = auth_service.login_or_register("alice", "pw123")
    assert player.username == "alice"
    assert player.rating == 1200


def test_login_with_known_username_and_correct_password_succeeds(auth_service):
    auth_service.login_or_register("alice", "pw123")
    player = auth_service.login_or_register("alice", "pw123")
    assert player.username == "alice"


def test_login_with_known_username_and_wrong_password_raises(auth_service):
    auth_service.login_or_register("alice", "pw123")
    with pytest.raises(InvalidCredentialsError):
        auth_service.login_or_register("alice", "wrong")


def test_second_login_does_not_create_duplicate_account(auth_service):
    first = auth_service.login_or_register("alice", "pw123")
    second = auth_service.login_or_register("alice", "pw123")
    assert first.id == second.id
