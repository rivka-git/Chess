from __future__ import annotations
from config import CELL_SIZE_PX


class BoardGeometry:
    def __init__(self, cell_size: int = CELL_SIZE_PX):
        self.cell_size = cell_size

    def cell_to_pixel(self, row: int, col: int) -> tuple[int, int]:
        """Return top-left pixel (x, y) for a board cell."""
        return col * self.cell_size, row * self.cell_size

    def pixel_to_cell(self, x: int, y: int) -> tuple[int, int]:
        """Return (row, col) for a pixel coordinate."""
        return y // self.cell_size, x // self.cell_size
