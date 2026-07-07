"""Board representation for simple text board fixtures."""

from __future__ import annotations

from typing import Sequence


class Board:
    """Represent a board parsed from a text fixture.

    The board stores rows as lists of cell tokens and exposes its dimensions so
    it can be printed back in a canonical form.
    """

    def __init__(self, rows: Sequence[Sequence[str]]) -> None:
        """Create a board from a sequence of row token lists."""
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
        """Return the board in the canonical text format."""
        return "\n".join(" ".join(row) for row in self.rows)
