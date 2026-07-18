from __future__ import annotations
from animation.animation_state import AnimationState


class LongRestState(AnimationState):
    def __init__(self, config: dict, sprite_frames):
        super().__init__("long_rest", config, sprite_frames)
        self._cooldown_until: float = 0.0

    def on_enter(self, piece_view, snapshot) -> None:
        self.elapsed_time = 0.0
        self.current_frame_index = 0
        from config import TRANSIT_DURATION_MS
        self._cooldown_until = snapshot.clock + TRANSIT_DURATION_MS * 2

    def update(self, dt: float, piece_view, snapshot) -> None:
        self._advance_frame(dt)
        if snapshot.clock >= self._cooldown_until:
            piece_view.transition_to("idle", snapshot)
