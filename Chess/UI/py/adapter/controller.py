from __future__ import annotations
from dataclasses import dataclass, field
from engine.game_engine import GameEngine


@dataclass
class PendingMoveSnapshot:
    start: tuple[int, int]
    end: tuple[int, int]
    start_clock: float      # ms when move was queued
    arrival_clock: float    # ms when piece arrives


@dataclass
class JumpSnapshot:
    position: tuple[int, int]
    start_clock: float
    land_clock: float


@dataclass
class PieceSnapshot:
    token: str              # e.g. "wK", "bQ"
    row: int
    col: int
    cooldown_until: float   # ms; 0 if no cooldown


@dataclass
class GameSnapshot:
    clock: float                                        # current game time in ms
    board: list[list[PieceSnapshot | None]]             # None = empty cell
    pending_moves: list[PendingMoveSnapshot] = field(default_factory=list)
    jumps: list[JumpSnapshot] = field(default_factory=list)
    game_over: bool = False


class Controller:
    def __init__(self, engine: GameEngine) -> None:
        self._engine = engine
        # Track when each move was queued so we can expose start_clock
        self._move_start_clocks: dict[tuple, float] = {}

    def move(self, x: int, y: int) -> None:
        self._engine.click(x, y)

    def jump(self, x: int, y: int) -> None:
        self._engine.jump(x, y)

    def click(self, x: int, y: int) -> None:
        # Backward-compatible alias for old input naming.
        self.move(x, y)

    def update(self, dt_ms: float) -> None:
        self._engine.wait(int(dt_ms))

    def get_snapshot(self) -> GameSnapshot:
        engine = self._engine
        clock = float(engine.time_ms)
        board_snap: list[list[PieceSnapshot | None]] = []
        for r in range(engine.board.height):
            snap_row: list[PieceSnapshot | None] = []
            for c in range(engine.board.width):
                token = engine.board.rows[r][c]
                if token == ".":
                    snap_row.append(None)
                else:
                    snap_row.append(PieceSnapshot(token=token, row=r, col=c, cooldown_until=0.0))
            board_snap.append(snap_row)

        pending = []
        for start, end, arrival_time, _token, _start_time in engine.game_timer.pending_moves:
            from config import TRANSIT_DURATION_MS
            distance = max(abs(end[0] - start[0]), abs(end[1] - start[1]))
            duration = TRANSIT_DURATION_MS * distance
            start_clock = float(arrival_time - duration)
            pending.append(PendingMoveSnapshot(
                start=start, end=end,
                start_clock=start_clock,
                arrival_clock=float(arrival_time)
            ))

        jumps = []
        for pos, land_time in engine.game_timer.airborne:
            from config import TRANSIT_DURATION_MS
            jumps.append(JumpSnapshot(
                position=pos,
                start_clock=float(land_time - TRANSIT_DURATION_MS),
                land_clock=float(land_time)
            ))

        return GameSnapshot(
            clock=clock,
            board=board_snap,
            pending_moves=pending,
            jumps=jumps,
            game_over=engine.game_over,
        )
