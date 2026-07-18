from __future__ import annotations
from animation.animation_state import AnimationState


class IdleState(AnimationState):
    def __init__(self, config: dict, sprite_frames):
        super().__init__("idle", config, sprite_frames)

    def on_enter(self, piece_view, snapshot) -> None:
        self.elapsed_time = 0.0
        self.current_frame_index = 0
        px, py = piece_view.geometry.cell_to_pixel(piece_view.row, piece_view.col)
        piece_view.px, piece_view.py = px, py

    def update(self, dt: float, piece_view, snapshot) -> None:
        self._advance_frame(dt)

        # Check transition to MoveState
        for move in snapshot.pending_moves:
            if move.start == (piece_view.row, piece_view.col):
                piece_view.transition_to("move", snapshot)
                return

        # Check transition to JumpState
        for jump in snapshot.jumps:
            if jump.position == (piece_view.row, piece_view.col):
                piece_view.transition_to("jump", snapshot)
                return
