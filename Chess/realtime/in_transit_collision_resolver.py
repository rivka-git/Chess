"""Resolution of collisions between pieces moving simultaneously."""

from __future__ import annotations

from config import TRANSIT_DURATION_MS
from model.board import Board
from rules.rule_engine import MoveExecutor


class InTransitCollisionResolver:
    """Stop pieces that collide mid-path, placing each at its last valid square."""

    def resolve(
        self,
        board: Board,
        pending_moves: list,
        move_executor: MoveExecutor,
        previous_time_ms: int,
        current_time_ms: int,
    ) -> list:
        """Apply in-transit collisions and return the updated pending_moves list."""
        if not pending_moves:
            return pending_moves

        events = self._collect_collision_events(pending_moves, current_time_ms)
        if not events:
            return pending_moves

        removed_moves: set[tuple] = set()
        for _, move_a, move_b, stop_a, stop_b in events:
            if move_a in removed_moves or move_b in removed_moves:
                continue
            if move_a not in pending_moves or move_b not in pending_moves:
                continue

            start_a, _, _, token_a, _ = move_a
            start_b, _, _, token_b, _ = move_b

            if board.rows[start_a[0]][start_a[1]] != token_a:
                continue
            if board.rows[start_b[0]][start_b[1]] != token_b:
                continue

            if stop_a != start_a:
                move_executor.apply_move(board, start_a, stop_a)
            if stop_b != start_b:
                move_executor.apply_move(board, start_b, stop_b)

            removed_moves.add(move_a)
            removed_moves.add(move_b)

        if not removed_moves:
            return pending_moves
        return [move for move in pending_moves if move not in removed_moves]

    def _collect_collision_events(
        self, pending_moves: list, current_time_ms: int
    ) -> list[tuple]:
        events: list[tuple] = []
        for index_a in range(len(pending_moves)):
            for index_b in range(index_a + 1, len(pending_moves)):
                collision = self._compute_collision_event(
                    pending_moves[index_a],
                    pending_moves[index_b],
                    current_time_ms,
                )
                if collision is not None:
                    events.append(collision)
        events.sort(key=lambda item: item[0])
        return events

    def _compute_collision_event(
        self,
        move_a: tuple,
        move_b: tuple,
        current_time_ms: int,
    ) -> tuple | None:
        start_a, end_a, _, token_a, start_time_a = move_a
        start_b, end_b, _, token_b, start_time_b = move_b
        if token_a == "." or token_b == ".":
            return None

        path_a = self._path_steps(start_a, end_a)
        path_b = self._path_steps(start_b, end_b)

        # Each piece is "in transit" to path[k] during the interval
        # [start_time + (k-1)*D,  start_time + k*D].
        # Two pieces collide when both head to the same cell in overlapping
        # intervals, i.e. |t_a - t_b| < D.  We return the earliest such
        # collision whose moment has already passed (≤ current_time_ms).
        best: tuple | None = None
        for step_a in range(1, len(path_a)):
            t_a = start_time_a + step_a * TRANSIT_DURATION_MS
            for step_b in range(1, len(path_b)):
                if path_a[step_a] != path_b[step_b]:
                    continue
                t_b = start_time_b + step_b * TRANSIT_DURATION_MS
                if abs(t_a - t_b) >= TRANSIT_DURATION_MS:
                    continue
                collision_time = min(t_a, t_b)
                if collision_time > current_time_ms:
                    continue
                if best is None or collision_time < best[0]:
                    best = (
                        collision_time,
                        move_a, move_b,
                        path_a[step_a - 1],
                        path_b[step_b - 1],
                    )
        return best

    @staticmethod
    def _path_steps(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        row_delta = end[0] - start[0]
        col_delta = end[1] - start[1]
        steps = max(abs(row_delta), abs(col_delta))
        if steps == 0:
            return [start]
        row_step = (row_delta > 0) - (row_delta < 0)
        col_step = (col_delta > 0) - (col_delta < 0)
        return [
            (start[0] + row_step * step_index, start[1] + col_step * step_index)
            for step_index in range(steps + 1)
        ]
