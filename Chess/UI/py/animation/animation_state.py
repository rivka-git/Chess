from __future__ import annotations
from abc import ABC, abstractmethod
from assets.img import Img


class AnimationState(ABC):
    def __init__(self, state_name: str, config: dict, sprite_frames: list[Img]):
        self.state_name = state_name
        self.config = config
        self.sprite_frames = sprite_frames
        self.elapsed_time = 0.0
        self.current_frame_index = 0

    @abstractmethod
    def on_enter(self, piece_view, snapshot) -> None:
        pass

    @abstractmethod
    def update(self, dt: float, piece_view, snapshot) -> None:
        pass

    def get_sprite(self) -> Img:
        return self.sprite_frames[self.current_frame_index]

    def _advance_frame(self, dt: float) -> bool:
        """Advance animation frame. Returns True if last frame was just finished."""
        fps = self.config["graphics"]["frames_per_sec"]
        self.elapsed_time += dt
        frame_duration = 1.0 / fps if fps > 0 else 1.0
        self.current_frame_index = int(self.elapsed_time / frame_duration) % len(self.sprite_frames)
        finished = not self.config["graphics"]["is_loop"] and self.elapsed_time >= frame_duration * len(self.sprite_frames)
        if finished:
            self.current_frame_index = len(self.sprite_frames) - 1
        return finished
