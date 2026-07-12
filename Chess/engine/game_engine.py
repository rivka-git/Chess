"""Core game engine: state management and game loop."""

from __future__ import annotations

from model.board import Board
from rules.rule_engine import MovementRules, MoveExecutor
from realtime.motion import GameTimer
from realtime.real_time_arbiter import CollisionResolver
from input.input_handler import InputHandler


class GameEndDetector:
    """Detect when the game has ended."""

    def is_game_over(self, board: Board) -> bool:
        pieces = {cell for row in board.rows for cell in row}
        return len(pieces & {"wK", "bK"}) == 1


class GameEngine:
    """Manage board interaction and game state."""

    def __init__(
        self,
        rows: list[list[str]] | None = None,
        movement_rules: MovementRules | None = None,
        move_executor: MoveExecutor | None = None,
        game_timer: GameTimer | None = None,
        collision_resolver: CollisionResolver | None = None,
        game_end_detector: GameEndDetector | None = None,
    ) -> None:
        self.board = Board(rows or [["."]]) 
        self.movement_rules = movement_rules or MovementRules()
        self.move_executor = move_executor or MoveExecutor()
        self.game_timer = game_timer or GameTimer()
        self.collision_resolver = collision_resolver or CollisionResolver()
        self.game_end_detector = game_end_detector or GameEndDetector()
        self.input_handler = InputHandler(self.game_timer, self.movement_rules)

        self.time_ms = 0
        self.game_over = False
        self._initial_king_count = sum(
            1 for row in self.board.rows for cell in row if cell in {"wK", "bK"}
        )

    def click(self, x: int, y: int) -> None:
        # Ensures board is up to date before processing input (relevant for real-time play)
        self._apply_arrived_moves()
        if self.game_over:
            return
        self.input_handler.handle_click(self.board, x, y, self._on_move_requested)

    def _on_move_requested(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        self.game_timer.add_move(start, end)

    def jump(self, x: int, y: int) -> None:
        # Ensures board is up to date before processing input (relevant for real-time play)
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

        for move in arrived_moves:
            if self.game_over:
                break
            kings_before = sum(1 for row in self.board.rows for cell in row if cell in {"wK", "bK"})
            executed = self.collision_resolver.resolve_collisions(
                self.board, [move], airborne_positions, self.move_executor
            )
            for start, end in executed:
                self.movement_rules.promote_pawns(self.board, end)
                kings_after = sum(1 for row in self.board.rows for cell in row if cell in {"wK", "bK"})
                if kings_after < kings_before:
                    self.game_over = True
                    break

        self.game_timer.expire_airborne()

    def print_board(self) -> str:
        return self.board.to_canonical_string()
