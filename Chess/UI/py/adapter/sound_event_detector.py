"""Wraps a controller and plays sounds based on game-state changes."""

from __future__ import annotations

from typing import Protocol


class ControllerLike(Protocol):
    def move(self, x: int, y: int) -> None: ...
    def jump(self, x: int, y: int) -> None: ...
    def update(self, dt_ms: float) -> None: ...
    def get_snapshot(self): ...


class SoundEffectsLike(Protocol):
    def play_move(self) -> None: ...
    def play_illegal_move(self) -> None: ...
    def play_capture(self) -> None: ...
    def play_promotion(self) -> None: ...
    def play_game_over(self) -> None: ...


class SoundEventDetector:
    """Wraps a controller and plays sounds based on observed game-state changes."""

    def __init__(
        self,
        controller: ControllerLike,
        sound_effects: SoundEffectsLike,
        cell_size: int,
    ) -> None:
        self._controller = controller
        self._sounds = sound_effects
        self._cell_size = cell_size

    # --- ControllerLike delegation ---

    def get_snapshot(self):
        return self._controller.get_snapshot()

    def move(self, x: int, y: int) -> None:
        snapshot_before = self._controller.get_snapshot()
        pending_before = len(snapshot_before.pending_moves)
        selected_before = snapshot_before.selected_position

        self._controller.move(x, y)

        snapshot_after = self._controller.get_snapshot()
        if len(snapshot_after.pending_moves) > pending_before:
            self._sounds.play_move()
        elif self._is_illegal_move(selected_before, snapshot_after, x, y):
            self._sounds.play_illegal_move()

    def jump(self, x: int, y: int) -> None:
        self._controller.jump(x, y)

    def update(self, dt_ms: float) -> None:
        snapshot_before = self._controller.get_snapshot()
        pieces_before = self._count_pieces(snapshot_before)
        game_over_before = snapshot_before.game_over

        self._controller.update(dt_ms)

        snapshot_after = self._controller.get_snapshot()
        self._check_state_sounds(snapshot_before, snapshot_after, pieces_before, game_over_before)

    def on_new_snapshot(self, snapshot_before, snapshot_after) -> None:
        """Called by RemoteController when a new server snapshot arrives."""
        if len(snapshot_after.pending_moves) > len(snapshot_before.pending_moves):
            self._sounds.play_move()
        self._check_state_sounds(
            snapshot_before, snapshot_after,
            self._count_pieces(snapshot_before),
            snapshot_before.game_over,
        )

    def _check_state_sounds(self, snapshot_before, snapshot_after, pieces_before, game_over_before) -> None:
        if self._count_pieces(snapshot_after) < pieces_before:
            self._sounds.play_capture()
        if self._has_promotion(snapshot_before, snapshot_after):
            self._sounds.play_promotion()
        if not game_over_before and snapshot_after.game_over:
            self._sounds.play_game_over()

    # --- Private helpers ---

    def _is_illegal_move(
        self,
        selected_before: tuple[int, int] | None,
        snapshot_after,
        x: int,
        y: int,
    ) -> bool:
        if selected_before is None:
            return False
        if snapshot_after.selected_position is not None:
            return False
        board = snapshot_after.board
        row = y // self._cell_size
        col = x // self._cell_size
        if not (0 <= row < len(board) and 0 <= col < len(board[0] if board else [])):
            return False
        return (row, col) != selected_before

    @staticmethod
    def _count_pieces(snapshot) -> int:
        return sum(1 for row in snapshot.board for piece in row if piece is not None)

    @staticmethod
    def _has_promotion(snapshot_before, snapshot_after) -> bool:
        for row_b, row_a in zip(snapshot_before.board, snapshot_after.board):
            for piece_b, piece_a in zip(row_b, row_a):
                if piece_b is None or piece_a is None:
                    continue
                if (
                    piece_b.token in {"wP", "bP"}
                    and piece_a.token in {"wQ", "bQ"}
                    and piece_b.token[0] == piece_a.token[0]
                ):
                    return True
        return False

