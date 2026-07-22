"""Unit tests for AppFactory: verifies DI wiring and injectable overrides."""

import sqlite3

import pytest

from server.auth.password_hasher import PasswordHasher
from server.matchmaking.matchmaking_queue import MatchmakingQueue
from server.net.dispatch import Dispatcher
from server.net.ws_server import AppFactory
from server.matchmaking.matchmaker_service import MatchmakerService


class FastHasher(PasswordHasher):
    def __init__(self):
        super().__init__(iterations=1)


class TrackingQueue(MatchmakingQueue):
    instantiated = False

    def __init__(self):
        super().__init__()
        TrackingQueue.instantiated = True


def test_build_returns_dispatcher_and_matchmaker():
    factory = AppFactory(db_path=":memory:", password_hasher=FastHasher())
    dispatcher, matchmaker = factory.build()
    assert isinstance(dispatcher, Dispatcher)
    assert isinstance(matchmaker, MatchmakerService)


def test_db_conn_is_accessible_on_factory():
    factory = AppFactory(db_path=":memory:", password_hasher=FastHasher())
    assert isinstance(factory.db_conn, sqlite3.Connection)


def test_injected_password_hasher_is_used_not_default():
    hasher = FastHasher()
    factory = AppFactory(db_path=":memory:", password_hasher=hasher)
    assert factory._password_hasher is hasher


def test_injected_queue_is_used_not_default():
    queue = TrackingQueue()
    TrackingQueue.instantiated = False  # reset after __init__ above
    factory = AppFactory(db_path=":memory:", password_hasher=FastHasher(), queue=queue)
    assert factory._queue is queue
    assert not TrackingQueue.instantiated  # no extra instantiation happened


def test_default_password_hasher_created_when_none_given():
    factory = AppFactory(db_path=":memory:")
    assert isinstance(factory._password_hasher, PasswordHasher)


def test_default_queue_created_when_none_given():
    factory = AppFactory(db_path=":memory:", password_hasher=FastHasher())
    assert isinstance(factory._queue, MatchmakingQueue)


def test_build_can_be_called_with_in_memory_db():
    factory = AppFactory(db_path=":memory:", password_hasher=FastHasher())
    # should not raise
    dispatcher, matchmaker = factory.build()
    assert dispatcher is not None
