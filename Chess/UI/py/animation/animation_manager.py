from __future__ import annotations
from animation.piece_view import PieceView


class AnimationManager:
    def __init__(self, asset_loader, geometry):
        self._asset_loader = asset_loader
        self._geometry = geometry
        self._pieces: dict[tuple[int, int], PieceView] = {}

    def sync_pieces(self, snapshot) -> None:
        """Spawn/remove PieceView instances to match the snapshot board."""
        current_keys = set()
        for row in snapshot.board:
            for cell in row:
                if cell is None:
                    continue
                key = (cell.row, cell.col)
                current_keys.add(key)
                existing = self._pieces.get(key)
                if existing is None or existing.token != cell.token:
                    self._pieces[key] = PieceView(
                        cell.token, cell.row, cell.col, self._asset_loader, self._geometry
                    )
        # Remove pieces no longer on board
        for key in list(self._pieces):
            if key not in current_keys:
                del self._pieces[key]

    def update(self, dt: float, snapshot) -> None:
        for pv in self._pieces.values():
            pv.update(dt, snapshot)

    @property
    def pieces(self):
        return self._pieces.values()
