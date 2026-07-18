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
        self._initial_king_count = self.board.count_kings()

    @classmethod
    def from_board(cls, board: Board) -> GameEngine:
        return cls(rows=[list(row) for row in board.rows])

    def click(self, x: int, y: int) -> None:
        self._apply_arrived_moves()
        if self.game_over:
            return
        self.input_handler.handle_click(self.board, x, y, self._on_move_requested)

    def _on_move_requested(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        self.game_timer.add_move(start, end, self.board.rows[start[0]][start[1]])

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

        # Keep only the earliest-arriving move per destination
        seen_ends: set[tuple[int, int]] = set()
        filtered: list = []
        for move in sorted(arrived_moves, key=lambda m: (m[4], arrived_moves.index(m))):
            if move[1] not in seen_ends:
                seen_ends.add(move[1])
                filtered.append(move)

        for move in filtered:
            if self.game_over:
                break
            start, end, arrival_time, token, start_time = move
            # Cancel moves whose start is the destination of this move (head-on collision)
            self.game_timer.pending_moves = [
                m for m in self.game_timer.pending_moves if m[1] != end and m[0] != end
            ]
            # Also cancel from filtered (already-arrived moves)
            filtered = [m for m in filtered if m[0] != end]
            kings_before = self.board.count_kings()
            executed = self.collision_resolver.resolve_collisions(
                self.board, [move], airborne_positions, self.move_executor
            )
            for start, end in executed:
                self.movement_rules.apply_end_of_move(self.board, end)
                kings_after = self.board.count_kings()
                if kings_after < kings_before:
                    self.game_over = True
                    break

        self.game_timer.expire_airborne()

    def print_board(self) -> str:
        return self.board.to_canonical_string()
