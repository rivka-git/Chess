from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol
from engine.game_engine import GameEngine


class SoundEffectsLike(Protocol):
    def play_move(self) -> None: ...
    def play_illegal_move(self) -> None: ...
    def play_capture(self) -> None: ...
    def play_promotion(self) -> None: ...
    def play_game_over(self) -> None: ...


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
    selected_position: tuple[int, int] | None = None
    legal_targets: list[tuple[int, int]] = field(default_factory=list)
    game_over: bool = False


class Controller:
    def __init__(self, engine: GameEngine, sound_effects: SoundEffectsLike | None = None) -> None:
        self._engine = engine
        self._sound_effects = sound_effects

    def move(self, x: int, y: int) -> None:
        pending_before = len(self._engine.game_timer.pending_moves)
        selected_before = self._engine.input_handler.selected_position
        self._engine.click(x, y)
        pending_after = len(self._engine.game_timer.pending_moves)
        if pending_after > pending_before:
            self._play("play_move")
            return

        if self._is_illegal_move_attempt(selected_before, x, y):
            self._play("play_illegal_move")

    def jump(self, x: int, y: int) -> None:
        self._engine.jump(x, y)

    def click(self, x: int, y: int) -> None:
        # Backward-compatible alias for old input naming.
        self.move(x, y)

    def update(self, dt_ms: float) -> None:
        board_before = tuple(tuple(row) for row in self._engine.board.rows)
        pieces_before = self._count_pieces(board_before)
        game_over_before = self._engine.game_over
        self._engine.wait(int(dt_ms))
        board_after = tuple(tuple(row) for row in self._engine.board.rows)
        if board_before != board_after:
            pieces_after = self._count_pieces(board_after)
            if pieces_after < pieces_before:
                self._play("play_capture")
            if self._has_promotion(board_before, board_after):
                self._play("play_promotion")
        if not game_over_before and self._engine.game_over:
            self._play("play_game_over")

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

        selected_position = engine.input_handler.selected_position
        legal_targets = self._compute_legal_targets(selected_position)

        return GameSnapshot(
            clock=clock,
            board=board_snap,
            pending_moves=pending,
            jumps=jumps,
            selected_position=selected_position,
            legal_targets=legal_targets,
            game_over=engine.game_over,
        )

    def _is_illegal_move_attempt(
        self,
        selected_before: tuple[int, int] | None,
        x: int,
        y: int,
    ) -> bool:
        if selected_before is None:
            return False
        selected_after = self._engine.input_handler.selected_position
        if selected_after is not None:
            return False
        row = y // self._engine.input_handler.cell_size
        col = x // self._engine.input_handler.cell_size
        if not (0 <= row < self._engine.board.height and 0 <= col < self._engine.board.width):
            return False
        return (row, col) != selected_before

    @staticmethod
    def _count_pieces(board_rows: tuple[tuple[str, ...], ...]) -> int:
        return sum(1 for row in board_rows for token in row if token != ".")

    @staticmethod
    def _has_promotion(
        before_rows: tuple[tuple[str, ...], ...],
        after_rows: tuple[tuple[str, ...], ...],
    ) -> bool:
        for before_row, after_row in zip(before_rows, after_rows):
            for before_token, after_token in zip(before_row, after_row):
                if before_token in {"wP", "bP"} and after_token in {"wQ", "bQ"}:
                    if before_token[0] == after_token[0]:
                        return True
        return False

    def _play(self, method_name: str) -> None:
        if self._sound_effects is None:
            return
        getattr(self._sound_effects, method_name)()

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
