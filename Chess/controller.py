"""Controller logic for click, wait, and board printing commands."""

from __future__ import annotations

from board import Board
from movement import MovementRules, MoveExecutor
from game_timer import GameTimer
from collision_resolver import CollisionResolver
from pawn_promoter import PawnPromoter
from game_end_detector import GameEndDetector
from input_handler import InputHandler


class Controller:
    """Manage simple board interaction for iteration 2."""

    def __init__(
        self,
        rows: list[list[str]] | None = None,
        movement_rules: MovementRules | None = None,
        move_executor: MoveExecutor | None = None,
    ) -> None:
        """Create a controller around a board representation."""
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
        """Handle a click at pixel coordinates, converting to a board cell."""
        self._apply_arrived_moves()
        if self.game_over:
            return
        self.input_handler.handle_click(self.board, x, y, self._on_move_requested)

    def _on_move_requested(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        """Called when the input handler wants to queue a move."""
        self.game_timer.add_move(start, end)

    def jump(self, x: int, y: int) -> None:
        """Make a piece jump, staying airborne for 1000ms to capture arriving enemies."""
        self._apply_arrived_moves()
        if self.game_over:
            return
        self.input_handler.handle_jump(self.board, x, y, self._on_jump_requested)

    def _on_jump_requested(self, position: tuple[int, int]) -> None:
        """Called when the input handler wants to queue a jump."""
        self.game_timer.add_airborne(position)

    def wait(self, milliseconds: int) -> None:
        """Advance the game clock by the provided number of milliseconds."""
        self.game_timer.update(milliseconds)
        self.time_ms = self.game_timer.time_ms
        self._apply_arrived_moves()

    def _apply_arrived_moves(self) -> None:
        """Apply all pending moves whose arrival time has been reached."""
        arrived_moves = self.game_timer.get_arrived_moves()
        airborne_positions = self.game_timer.get_airborne_positions()
        
        moves_to_execute, pieces_destroyed = self.collision_resolver.resolve_collisions(
            self.board, arrived_moves, airborne_positions
        )
        
        # Destroy pieces that collided with jumpers
        self.collision_resolver.destroy_pieces(self.board, pieces_destroyed)
        
        # Execute moves that didn't collide
        for start, end in moves_to_execute:
            kings_before = self.game_end_detector._get_kings_on_board(self.board)
            self.move_executor.apply_move(self.board, start, end)
            self.pawn_promoter.promote_pawns(self.board, start, end)
            if self.game_end_detector.check_king_captured(self.board, kings_before):
                self.game_over = True
        
        self.game_timer.expire_airborne()

    def print_board(self) -> str:
        """Return the current settled board state after completed moves."""
        return self.board.to_canonical_string()

    @property
    def pending_moves(self) -> list[tuple[tuple[int, int], tuple[int, int], int]]:
        """Return pending moves from the game timer."""
        return self.game_timer.pending_moves

    @property
    def airborne(self) -> list[tuple[tuple[int, int], int]]:
        """Return airborne pieces from the game timer."""
        return self.game_timer.airborne

    @property
    def selected_position(self) -> tuple[int, int] | None:
        """Return the currently selected position from input handler."""
        return self.input_handler.selected_position

    @selected_position.setter
    def selected_position(self, value: tuple[int, int] | None) -> None:
        """Set the currently selected position in input handler."""
        self.input_handler.selected_position = value
