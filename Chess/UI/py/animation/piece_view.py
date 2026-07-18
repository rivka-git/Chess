from __future__ import annotations
from assets.img import Img
from animation.idle_state import IdleState
from animation.move_state import MoveState
from animation.jump_state import JumpState
from animation.short_rest_state import ShortRestState
from animation.long_rest_state import LongRestState

_STATE_CLASSES = {
    "idle": IdleState,
    "move": MoveState,
    "jump": JumpState,
    "short_rest": ShortRestState,
    "long_rest": LongRestState,
}


class PieceView:
    def __init__(self, token: str, row: int, col: int, asset_loader, geometry):
        self.token = token
        self.row = row
        self.col = col
        self._asset_loader = asset_loader
        self.geometry = geometry
        px, py = geometry.cell_to_pixel(row, col)
        self.px = px
        self.py = py
        self._state = None
        self.transition_to("idle", None)

    def transition_to(self, state_name: str, snapshot) -> None:
        piece_key = self._asset_loader.piece_key(self.token)
        data = self._asset_loader.get_state_data(piece_key, state_name)
        self._state = _STATE_CLASSES[state_name](data["config"], data["frames"])
        self._state.on_enter(self, snapshot)

    def update(self, dt: float, snapshot) -> None:
        self._state.update(dt, self, snapshot)

    def get_sprite(self) -> Img:
        return self._state.get_sprite()

    @property
    def state_name(self) -> str:
        return self._state.state_name
