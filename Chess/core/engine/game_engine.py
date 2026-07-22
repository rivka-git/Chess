"""Core game engine: state management and game loop."""

from __future__ import annotations

from core.model.board import Board
from core.rules.rule_engine import MovementRules, MoveExecutor
from core.realtime.motion import GameTimer
from core.realtime.real_time_arbiter import CollisionResolver
from core.realtime.in_transit_collision_resolver import InTransitCollisionResolver
from core.realtime.move_arbiter import MoveArbiter
from input.input_handler import InputHandler
from core.rules.post_move_effects import PostMoveEffects


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
        in_transit_collision_resolver: InTransitCollisionResolver | None = None,
        move_arbiter: MoveArbiter | None = None,
        input_handler: InputHandler | None = None,
        post_move_effects: PostMoveEffects | None = None,
    ) -> None:
        self.board = Board(rows or [["."]]) 
        self.movement_rules = movement_rules or MovementRules()
        self.move_executor = move_executor or MoveExecutor()
        self.game_timer = game_timer or GameTimer()
        self.collision_resolver = collision_resolver or CollisionResolver()
        self.game_end_detector = game_end_detector or GameEndDetector()
        self.in_transit_collision_resolver = in_transit_collision_resolver or InTransitCollisionResolver()
        self.move_arbiter = move_arbiter or MoveArbiter()
        self.input_handler = input_handler or InputHandler(self.game_timer, self.movement_rules)
        self.post_move_effects = post_move_effects or PostMoveEffects()

        self.time_ms = 0
        self.game_over = False
        self._initial_king_count = self.board.count_kings()

    @classmethod
    def from_board(cls, board: Board) -> GameEngine:
        return cls(rows=[list(row) for row in board.rows])

    def click(self, row: int, col: int, color: str | None = None) -> None:
        self._apply_arrived_moves()
        if self.game_over:
            return
        self.input_handler.handle_click(self.board, row, col, self._on_move_requested, color=color)

    def _on_move_requested(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        self.game_timer.add_move(start, end, self.board.rows[start[0]][start[1]])

    def jump(self, row: int, col: int, color: str | None = None) -> None:
        self._apply_arrived_moves()
        if self.game_over:
            return
        self.input_handler.handle_jump(self.board, row, col, self._on_jump_requested, color=color)

    def _on_jump_requested(self, position: tuple[int, int]) -> None:
        self.game_timer.add_airborne(position)

    def wait(self, milliseconds: int) -> None:
        previous_time_ms = self.game_timer.time_ms
        self.game_timer.update(milliseconds)
        self.time_ms = self.game_timer.time_ms
        self.game_timer.pending_moves = self.in_transit_collision_resolver.resolve(
            self.board, self.game_timer.pending_moves, self.move_executor, previous_time_ms, self.time_ms
        )
        self._apply_arrived_moves()

    def _apply_arrived_moves(self) -> None:
        arrived_moves = self.game_timer.get_arrived_moves()
        airborne_positions = self.game_timer.get_airborne_positions()

        filtered = self.move_arbiter.filter_arrived(arrived_moves)

        for move in filtered:
            if self.game_over:
                break
            start, end, arrival_time, token, start_time = move
            self.game_timer.pending_moves = self.move_arbiter.cancel_head_on(
                self.game_timer.pending_moves, end
            )
            filtered = [m for m in filtered if m[0] != end]
            kings_before = self.board.count_kings()
            executed = self.collision_resolver.resolve_collisions(
                self.board, [move], airborne_positions, self.move_executor
            )
            for arrived_start, arrived_end in executed:
                self.post_move_effects.apply(self.board, arrived_end)
            if self.board.count_kings() < kings_before:
                self.game_over = True

        self.game_timer.expire_airborne()

    def print_board(self) -> str:
        return self.board.to_canonical_string()
