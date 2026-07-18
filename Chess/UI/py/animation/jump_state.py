from __future__ import annotations
from animation.animation_state import AnimationState

ARC_HEIGHT_CELLS = 0.5  # parabola peak height in cell units


class JumpState(AnimationState):
    def __init__(self, config: dict, sprite_frames):
        super().__init__("jump", config, sprite_frames)

    def on_enter(self, piece_view, snapshot) -> None:
        self.elapsed_time = 0.0
        self.current_frame_index = 0

    def update(self, dt: float, piece_view, snapshot) -> None:
        finished = self._advance_frame(dt)

        jump = next(
            (j for j in snapshot.jumps if j.position == (piece_view.row, piece_view.col)),
            None
        )
        if jump is not None:
            duration = jump.land_clock - jump.start_clock
            t = min((snapshot.clock - jump.start_clock) / duration, 1.0) if duration > 0 else 1.0
            geom = piece_view.geometry
            bx, by = geom.cell_to_pixel(piece_view.row, piece_view.col)
            arc_offset = int(ARC_HEIGHT_CELLS * geom.cell_size * 4 * t * (1 - t))
            piece_view.px = bx
            piece_view.py = by - arc_offset

        if finished:
            piece_view.transition_to("short_rest", snapshot)
