"""Unit tests for server.auth.password_hasher.PasswordHasher."""

import pytest

from server.auth.password_hasher import PasswordHasher


@pytest.fixture
def hasher():
    # Low iteration count: these tests check correctness, not brute-force
    # resistance, so there's no reason to pay production-strength cost here.
    return PasswordHasher(iterations=1_000)


def test_verify_succeeds_for_correct_password(hasher):
    password_hash, salt = hasher.hash("hunter2")
    assert hasher.verify("hunter2", password_hash, salt)


def test_verify_fails_for_wrong_password(hasher):
    password_hash, salt = hasher.hash("hunter2")
    assert not hasher.verify("wrong", password_hash, salt)


def test_same_password_different_salt_yields_different_hash(hasher):
    hash1, salt1 = hasher.hash("hunter2")
    hash2, salt2 = hasher.hash("hunter2")
    assert salt1 != salt2
    assert hash1 != hash2


def test_hash_does_not_contain_plaintext_password(hasher):
    password_hash, _ = hasher.hash("hunter2")
    assert "hunter2" not in password_hash


def test_default_iterations_is_at_least_owasp_minimum():
    assert PasswordHasher()._iterations >= 200_000
