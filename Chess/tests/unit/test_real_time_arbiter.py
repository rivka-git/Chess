"""Unit tests for realtime.motion and realtime.real_time_arbiter."""

from core.model.board import Board
from core.realtime.motion import GameTimer
from core.realtime.real_time_arbiter import CollisionResolver


# --- GameTimer ---

def test_timer_starts_at_zero():
    assert GameTimer().time_ms == 0


def test_timer_update():
    timer = GameTimer()
    timer.update(500)
    assert timer.time_ms == 500


def test_add_move_calculates_arrival_time():
    timer = GameTimer()
    timer.add_move((0, 0), (0, 3), "wR")
    assert timer.pending_moves[0][2] == 3000


def test_get_arrived_moves_returns_arrived():
    timer = GameTimer()
    timer.add_move((0, 0), (0, 1), "wR")
    timer.update(1000)
    arrived = timer.get_arrived_moves()
    assert len(arrived) == 1
    assert timer.pending_moves == []


def test_get_arrived_moves_keeps_pending():
    timer = GameTimer()
    timer.add_move((0, 0), (0, 3), "wR")
    timer.update(1000)
    arrived = timer.get_arrived_moves()
    assert arrived == []
    assert len(timer.pending_moves) == 1


def test_add_airborne():
    timer = GameTimer()
    timer.add_airborne((0, 0))
    assert len(timer.airborne) == 1


def test_get_airborne_positions():
    timer = GameTimer()
    timer.add_airborne((0, 0))
    assert (0, 0) in timer.get_airborne_positions()


def test_expire_airborne():
    timer = GameTimer()
    timer.add_airborne((0, 0))
    timer.update(1001)
    timer.expire_airborne()
    assert timer.airborne == []


def test_is_piece_in_transit():
    timer = GameTimer()
    timer.add_move((0, 0), (0, 1), "wR")
    assert timer.is_piece_in_transit((0, 0))
    assert not timer.is_piece_in_transit((0, 1))


def test_has_pending_moves():
    timer = GameTimer()
    assert not timer.has_pending_moves()
    timer.add_move((0, 0), (0, 1), "wR")
    assert timer.has_pending_moves()


# --- CollisionResolver ---

def test_no_collision():
    from core.rules.rule_engine import MoveExecutor
    board = Board([["wR", ".", "."]])
    resolver = CollisionResolver()
    moves = resolver.resolve_collisions(board, [((0, 0), (0, 2), 2000, "wR")], [], MoveExecutor())
    assert moves == [((0, 0), (0, 2))]
    assert board.rows[0][2] == "wR"


def test_collision_with_airborne():
    from core.rules.rule_engine import MoveExecutor
    board = Board([["wR", ".", "bR"]])
    resolver = CollisionResolver()
    moves = resolver.resolve_collisions(
        board, [((0, 2), (0, 0), 2000, "bR")], [(0, 0)], MoveExecutor()
    )
    assert moves == []
    assert board.rows[0][2] == "."
