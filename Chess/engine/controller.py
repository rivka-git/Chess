"""Controller and snapshot dataclasses shared by the server and UI.

Lives in engine/ so both server/ and UI/py/ can import from here
without either depending on the other.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from config import TRANSIT_DURATION_MS
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
    clock: float
    board: list[list[PieceSnapshot | None]]
    pending_moves: list[PendingMoveSnapshot] = field(default_factory=list)
    jumps: list[JumpSnapshot] = field(default_factory=list)
    selected_position: tuple[int, int] | None = None
    legal_targets: list[tuple[int, int]] = field(default_factory=list)
    game_over: bool = False


class Controller:
    """Bridge user input to the game engine and expose state snapshots."""

    def __init__(self, engine: GameEngine) -> None:
        self._engine = engine

    def move(self, x: int, y: int, color: str | None = None) -> None:
        self._engine.click(x, y, color=color)

    def jump(self, x: int, y: int, color: str | None = None) -> None:
        self._engine.jump(x, y, color=color)

    def click(self, x: int, y: int) -> None:
        # Backward-compatible alias for old input naming.
        self.move(x, y)

    def move_rowcol(self, row: int, col: int, cell_size: int, color: str | None = None) -> None:
        """Server-facing: accepts grid coordinates instead of pixels."""
        x = col * cell_size + cell_size // 2
        y = row * cell_size + cell_size // 2
        self._engine.click(x, y, color=color)

    def jump_rowcol(self, row: int, col: int, cell_size: int, color: str | None = None) -> None:
        """Server-facing: accepts grid coordinates instead of pixels."""
        x = col * cell_size + cell_size // 2
        y = row * cell_size + cell_size // 2
        self._engine.jump(x, y, color=color)

    def update(self, dt_ms: float) -> None:
        self._engine.wait(int(dt_ms))

    def get_snapshot(self, viewer_color: str | None = None) -> GameSnapshot:
        engine = self._engine
        selected_position = engine.input_handler.selection_for(viewer_color)
        return GameSnapshot(
            clock=float(engine.time_ms),
            board=self._build_board_snapshot(),
            pending_moves=self._build_pending_moves_snapshot(),
            jumps=self._build_jumps_snapshot(),
            selected_position=selected_position,
            legal_targets=self._compute_legal_targets(selected_position),
            game_over=engine.game_over,
        )

    def _build_board_snapshot(self) -> list[list[PieceSnapshot | None]]:
        board = self._engine.board
        result: list[list[PieceSnapshot | None]] = []
        for r in range(board.height):
            row: list[PieceSnapshot | None] = []
            for c in range(board.width):
                token = board.rows[r][c]
                row.append(None if token == "." else PieceSnapshot(token=token, row=r, col=c, cooldown_until=0.0))
            result.append(row)
        return result

    def _build_pending_moves_snapshot(self) -> list[PendingMoveSnapshot]:
        pending = []
        for start, end, arrival_time, _token, _start_time in self._engine.game_timer.pending_moves:
            distance = max(abs(end[0] - start[0]), abs(end[1] - start[1]))
            pending.append(PendingMoveSnapshot(
                start=start,
                end=end,
                start_clock=float(arrival_time - TRANSIT_DURATION_MS * distance),
                arrival_clock=float(arrival_time),
            ))
        return pending

    def _build_jumps_snapshot(self) -> list[JumpSnapshot]:
        return [
            JumpSnapshot(
                position=pos,
                start_clock=float(land_time - TRANSIT_DURATION_MS),
                land_clock=float(land_time),
            )
            for pos, land_time in self._engine.game_timer.airborne
        ]

    def _compute_legal_targets(
        self,
        selected_position: tuple[int, int] | None,
    ) -> list[tuple[int, int]]:
        if selected_position is None:
            return []
        if self._engine.game_over:
            return []
        if self._engine.game_timer.is_piece_in_transit(selected_position):
            return []

        row, col = selected_position
        token = self._engine.board.rows[row][col]
        if token == ".":
            return []

        targets: list[tuple[int, int]] = []
        for target_row in range(self._engine.board.height):
            for target_col in range(self._engine.board.width):
                target = (target_row, target_col)
                if self._engine.movement_rules.is_legal_move(
                    self._engine.board,
                    selected_position,
                    target,
                ):
                    targets.append(target)
        return targets
