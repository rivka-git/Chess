"""Board representation for simple text board fixtures."""

from __future__ import annotations

from typing import Sequence


class Board:
    """Represent a board parsed from a text fixture."""

    def __init__(self, rows: Sequence[Sequence[str]]) -> None:
        if not rows:
            raise ValueError("Board cannot be empty.")

        normalized_rows = [list(row) for row in rows if list(row)]
        if not normalized_rows:
            raise ValueError("Board cannot be empty.")

        width = len(normalized_rows[0])
        if width == 0:
            raise ValueError("Board rows must not be empty.")

        if any(len(row) != width for row in normalized_rows):
            raise ValueError("ROW_WIDTH_MISMATCH")

        self.rows = normalized_rows
        self.height = len(self.rows)
        self.width = width

    def to_canonical_string(self) -> str:
        return "\n".join(" ".join(row) for row in self.rows)
