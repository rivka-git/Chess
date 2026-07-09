"""Core game engine: state management and game loop."""

from __future__ import annotations

from model.board import Board
from rules.rule_engine import MovementRules, MoveExecutor, PawnPromoter
from realtime.motion import GameTimer
from realtime.real_time_arbiter import CollisionResolver
from input.input_handler import InputHandler


class GameEndDetector:
    """Detect when the game has ended."""

    def check_king_captured(self, board: Board, kings_before: set[str]) -> bool:
        kings_now = self._get_kings_on_board(board)
        return bool(kings_before - kings_now)

    def _get_kings_on_board(self, board: Board) -> set[str]:
        pieces = {cell for row in board.rows for cell in row}
        return pieces & {"wK", "bK"}


class GameEngine:
    """Manage board interaction and game state."""

    def __init__(
        self,
        rows: list[list[str]] | None = None,
        movement_rules: MovementRules | None = None,
        move_executor: MoveExecutor | None = None,
    ) -> None:
        self.board = Board(rows or [["."]]) 
        self.movement_rules = movement_rules or MovementRules()
        self.move_executor = move_executor or MoveExecutor()

        self.game_timer = GameTimer()
        self.collision_resolver = CollisionResolver()
        self.pawn_promoter = PawnPromoter()
        self.game_end_detector = GameEndDetector()
        self.input_handler = InputHandler(self.game_timer, self.movement_rules)

        self.time_ms = 0
        self.game_over = False

    def click(self, x: int, y: int) -> None:
        self._apply_arrived_moves()
        if self.game_over:
            return
        self.input_handler.handle_click(self.board, x, y, self._on_move_requested)

    def _on_move_requested(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        self.game_timer.add_move(start, end)

    def jump(self, x: int, y: int) -> None:
        self._apply_arrived_moves()
        if self.game_over:
            return
        self.input_handler.handle_jump(self.board, x, y, self._on_jump_requested)

    def _on_jump_requested(self, position: tuple[int, int]) -> None:
        self.game_timer.add_airborne(position)

    def wait(self, milliseconds: int) -> None:
        self.game_timer.update(milliseconds)
        self.time_ms = self.game_timer.time_ms
        self._apply_arrived_moves()

    def _apply_arrived_moves(self) -> None:
        arrived_moves = self.game_timer.get_arrived_moves()
        airborne_positions = self.game_timer.get_airborne_positions()

        moves_to_execute, pieces_destroyed = self.collision_resolver.resolve_collisions(
            self.board, arrived_moves, airborne_positions
        )

        self.collision_resolver.destroy_pieces(self.board, pieces_destroyed)

        for start, end in moves_to_execute:
            kings_before = self.game_end_detector._get_kings_on_board(self.board)
            self.move_executor.apply_move(self.board, start, end)
            self.pawn_promoter.promote_pawns(self.board, start, end)
            if self.game_end_detector.check_king_captured(self.board, kings_before):
                self.game_over = True

        self.game_timer.expire_airborne()

    def print_board(self) -> str:
        return self.board.to_canonical_string()

    @property
    def pending_moves(self) -> list[tuple[tuple[int, int], tuple[int, int], int]]:
        return self.game_timer.pending_moves

    @property
    def airborne(self) -> list[tuple[tuple[int, int], int]]:
        return self.game_timer.airborne

    @property
    def selected_position(self) -> tuple[int, int] | None:
        return self.input_handler.selected_position

    @selected_position.setter
    def selected_position(self, value: tuple[int, int] | None) -> None:
        self.input_handler.selected_position = value
