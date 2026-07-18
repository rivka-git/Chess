from __future__ import annotations
from animation.animation_state import AnimationState


class MoveState(AnimationState):
    def __init__(self, config: dict, sprite_frames):
        super().__init__("move", config, sprite_frames)

    def on_enter(self, piece_view, snapshot) -> None:
        self.elapsed_time = 0.0
        self.current_frame_index = 0

    def update(self, dt: float, piece_view, snapshot) -> None:
        self._advance_frame(dt)

        move = next(
            (m for m in snapshot.pending_moves if m.start == (piece_view.row, piece_view.col)),
            None
        )
        if move is None:
            # Move completed - piece is now at destination
            piece_view.transition_to("long_rest", snapshot)
            return

        duration = move.arrival_clock - move.start_clock
        if duration <= 0:
            t = 1.0
        else:
            t = min((snapshot.clock - move.start_clock) / duration, 1.0)

        geom = piece_view.geometry
        sx, sy = geom.cell_to_pixel(move.start[0], move.start[1])
        ex, ey = geom.cell_to_pixel(move.end[0], move.end[1])
        piece_view.px = int(sx + (ex - sx) * t)
        piece_view.py = int(sy + (ey - sy) * t)

        if t >= 1.0:
            piece_view.row, piece_view.col = move.end
            piece_view.transition_to("long_rest", snapshot)
