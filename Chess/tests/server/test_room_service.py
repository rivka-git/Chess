"""Unit tests for server.rooms.room_service.RoomService."""

import pytest

from server.bus.event_bus import EventBus
from server.game.session_manager import SessionManager
from server.rooms.exceptions import RoomNotFoundError
from server.rooms.room_service import RoomService


@pytest.fixture
def room_service():
    return RoomService(SessionManager(EventBus()))


def test_create_room_returns_a_room_id(room_service):
    room_id = room_service.create_room()
    assert isinstance(room_id, str) and room_id


def test_two_created_rooms_have_different_ids(room_service):
    assert room_service.create_room() != room_service.create_room()


def test_get_room_after_create_returns_the_same_session(room_service):
    room_id = room_service.create_room()
    assert room_service.get_room(room_id).session_id == room_id


def test_get_room_with_unknown_id_raises(room_service):
    with pytest.raises(RoomNotFoundError):
        room_service.get_room("does-not-exist")
