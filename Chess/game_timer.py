"""Game timer managing pending moves and airborne pieces."""

from __future__ import annotations

TRANSIT_DURATION_MS = 1000


class GameTimer:
    """Manage game time, pending moves, and airborne pieces."""

    def __init__(self) -> None:
        """Initialize the game timer."""
        self.time_ms = 0
        self.pending_moves: list[tuple[tuple[int, int], tuple[int, int], int]] = []  # (start, end, arrival_time)
        self.airborne: list[tuple[tuple[int, int], int]] = []  # (position, land_time)

    def add_move(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        """Add a new move to the pending list with arrival time based on distance."""
        distance = max(abs(end[0] - start[0]), abs(end[1] - start[1]))
        arrival_time = self.time_ms + TRANSIT_DURATION_MS * distance
        self.pending_moves.append((start, end, arrival_time))

    def add_airborne(self, position: tuple[int, int]) -> None:
        """Add a piece to the airborne list."""
        land_time = self.time_ms + TRANSIT_DURATION_MS
        self.airborne.append((position, land_time))

    def update(self, milliseconds: int) -> None:
        """Advance the game clock by the provided milliseconds."""
        self.time_ms += milliseconds

    def get_arrived_moves(self) -> list[tuple[tuple[int, int], tuple[int, int], int]]:
        """Return and remove all moves that have arrived."""
        arrived = []
        remaining = []
        for move in self.pending_moves:
            start, end, arrival_time = move
            if self.time_ms >= arrival_time:
                arrived.append(move)
            else:
                remaining.append(move)
        self.pending_moves = remaining
        return arrived

    def get_airborne_positions(self) -> list[tuple[int, int]]:
        """Return positions of pieces still airborne at current time."""
        return [pos for pos, land_time in self.airborne if self.time_ms <= land_time]

    def expire_airborne(self) -> None:
        """Remove airborne pieces whose land time has passed."""
        self.airborne = [(pos, land_time) for pos, land_time in self.airborne if self.time_ms < land_time]

    def is_piece_in_transit(self, position: tuple[int, int]) -> bool:
        """Return whether a piece at the given position is moving."""
        return any(start == position for start, end, arrival_time in self.pending_moves)

    def has_pending_moves(self) -> bool:
        """Return whether there are any pending moves."""
        return bool(self.pending_moves)
