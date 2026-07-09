"""Controller logic for click, wait, and board printing commands."""

from __future__ import annotations

from board import Board
from movement import MovementRules, MoveExecutor
from game_timer import GameTimer
from collision_resolver import CollisionResolver


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
        self.selected_position: tuple[int, int] | None = None
        self.game_timer = GameTimer()
        self.collision_resolver = CollisionResolver()
        self.time_ms = 0
        self.game_over = False
        self.movement_rules = movement_rules or MovementRules()
        self.move_executor = move_executor or MoveExecutor()

    def click(self, x: int, y: int) -> None:
        """Handle a click at pixel coordinates, converting to a board cell."""
        self._apply_arrived_moves()
        if self.game_over:
            return
        row = y // 100
        col = x // 100

        if not self._is_inside_board(row, col):
            return

        if self.selected_position is None:
            if self.board.rows[row][col] != ".":
                self.selected_position = (row, col)
            return

        target_position = (row, col)
        target_piece = self.board.rows[row][col]

        if target_piece != "." and self._is_own_piece(self.selected_position, target_position):
            self.selected_position = target_position
            return

        if self.movement_rules.is_legal_move(self.board, self.selected_position, target_position):
            # board is locked while any piece is in transit
            if not self.game_timer.has_pending_moves():
                self.game_timer.add_move(self.selected_position, target_position)
        self.selected_position = None

    def jump(self, x: int, y: int) -> None:
        """Make a piece jump, staying airborne for 1000ms to capture arriving enemies."""
        self._apply_arrived_moves()
        if self.game_over:
            return
        row = y // 100
        col = x // 100
        if not self._is_inside_board(row, col):
            return
        position = (row, col)
        if self.board.rows[row][col] == ".":
            return
        if self.game_timer.is_piece_in_transit(position):
            return
        if any(pos == position for pos, land_time in self.game_timer.airborne):
            return
        self.game_timer.add_airborne(position)

    def wait(self, milliseconds: int) -> None:
        """Advance the game clock by the provided number of milliseconds."""
        self.game_timer.update(milliseconds)
        self.time_ms = self.game_timer.time_ms
        self._apply_arrived_moves()

    def _promote_pawns(self) -> None:
        """Promote any pawn that has reached the last row to a queen."""
        for col in range(self.board.width):
            if self.board.rows[0][col] == "wP":
                self.board.rows[0][col] = "wQ"
            if self.board.rows[self.board.height - 1][col] == "bP":
                self.board.rows[self.board.height - 1][col] = "bQ"

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
            king_present_before = self._kings_on_board()
            self.move_executor.apply_move(self.board, start, end)
            self._promote_pawns()
            if self._a_king_was_captured(king_present_before):
                self.game_over = True
        
        self.game_timer.expire_airborne()

    def print_board(self) -> str:
        """Return the current settled board state after completed moves."""
        self._apply_arrived_moves()
        return self.board.to_canonical_string()

    @property
    def pending_moves(self) -> list[tuple[tuple[int, int], tuple[int, int], int]]:
        """Return pending moves from the game timer."""
        return self.game_timer.pending_moves

    @property
    def airborne(self) -> list[tuple[tuple[int, int], int]]:
        """Return airborne pieces from the game timer."""
        return self.game_timer.airborne

    def _kings_on_board(self) -> set[str]:
        """Return the set of king tokens currently present on the board."""
        pieces = {cell for row in self.board.rows for cell in row}
        return pieces & {"wK", "bK"}

    def _a_king_was_captured(self, kings_before: set[str]) -> bool:
        """Return whether a king that was present before a move is now gone."""
        return bool(kings_before - self._kings_on_board())

    def _is_own_piece(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        """Return whether the destination contains a piece of the same color."""
        start_piece = self.board.rows[start[0]][start[1]]
        end_piece = self.board.rows[end[0]][end[1]]
        return end_piece != "." and self.movement_rules.is_same_color(start_piece, end_piece)

    def _is_inside_board(self, row: int, col: int) -> bool:
        """Return whether the coordinates fall within the board bounds."""
        return 0 <= row < self.board.height and 0 <= col < self.board.width
