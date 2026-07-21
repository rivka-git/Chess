"""Unit tests for network.move_log.MoveLog."""

from adapter.controller import GameSnapshot, PendingMoveSnapshot, PieceSnapshot
from network.move_log import MoveLog


def _piece(token, row, col):
    return PieceSnapshot(token=token, row=row, col=col, cooldown_until=0.0)


def _board_with(*pieces):
    board = [[None] * 8 for _ in range(8)]
    for piece in pieces:
        board[piece.row][piece.col] = piece
    return board


def _snapshot(board=None, pending=()):
    return GameSnapshot(clock=0.0, board=board or [[None] * 8 for _ in range(8)], pending_moves=list(pending))


def test_new_pending_move_is_recorded_with_mover_color():
    prev = _snapshot(board=_board_with(_piece("wP", 6, 4)))
    move = PendingMoveSnapshot(start=(6, 4), end=(4, 4), start_clock=0.0, arrival_clock=1000.0)
    current = _snapshot(pending=[move])

    log = MoveLog()
    log.observe(prev, current)

    entries = log.entries()
    assert len(entries) == 1
    seq, color, start, end = entries[0]
    assert (seq, color, start, end) == (1, "w", (6, 4), (4, 4))


def test_already_seen_pending_move_is_not_recorded_twice():
    prev_board = _board_with(_piece("wP", 6, 4))
    move = PendingMoveSnapshot(start=(6, 4), end=(4, 4), start_clock=0.0, arrival_clock=1000.0)
    log = MoveLog()

    log.observe(_snapshot(board=prev_board), _snapshot(pending=[move]))
    # same move still in flight on the next tick -- must not double-count
    log.observe(_snapshot(pending=[move]), _snapshot(pending=[move]))

    assert len(log.entries()) == 1


def test_moves_accumulate_in_order():
    log = MoveLog()
    white = PendingMoveSnapshot(start=(6, 4), end=(4, 4), start_clock=0.0, arrival_clock=1000.0)
    black = PendingMoveSnapshot(start=(1, 4), end=(3, 4), start_clock=0.0, arrival_clock=1200.0)

    log.observe(_snapshot(board=_board_with(_piece("wP", 6, 4))), _snapshot(pending=[white]))
    log.observe(_snapshot(board=_board_with(_piece("bP", 1, 4)), pending=[white]),
                _snapshot(pending=[white, black]))

    seqs = [e[0] for e in log.entries()]
    colors = [e[1] for e in log.entries()]
    assert seqs == [1, 2]
    assert colors == ["w", "b"]


def test_lines_render_algebraic_squares():
    prev = _snapshot(board=_board_with(_piece("wP", 6, 4)))
    move = PendingMoveSnapshot(start=(6, 4), end=(4, 4), start_clock=0.0, arrival_clock=1000.0)
    log = MoveLog()
    log.observe(prev, _snapshot(pending=[move]))

    # row 6 col 4 = e2, row 4 col 4 = e4 on an 8-high board
    assert log.lines() == ["1. w e2->e4"]
