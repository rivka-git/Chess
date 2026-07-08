"""Controller logic for click, wait, and board printing commands."""

from __future__ import annotations

from board import Board
from movement import MovementRules


class Controller:
    """Manage simple board interaction for iteration 2."""

    def __init__(
        self,
        rows: list[list[str]] | None = None,
        movement_rules: MovementRules | None = None,
    ) -> None:
        """Create a controller around a board representation."""
        self.board = Board(rows or [["."]])
        self.selected_position: tuple[int, int] | None = None
        self.pending_moves: list[tuple[tuple[int, int], tuple[int, int]]] = []
        self.airborne: list[tuple[tuple[int, int], int]] = []
        self.time_ms = 0
        self.game_over = False
        self.movement_rules = movement_rules or MovementRules()

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
            if not self.pending_moves:
                arrival_time = self.time_ms + 1000
                self.pending_moves.append((self.selected_position, target_position, arrival_time))
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
        if self._is_piece_in_transit(position):
            return
        if any(pos == position for pos, land_time in self.airborne):
            return
        self.airborne.append((position, self.time_ms + 1000))

    def wait(self, milliseconds: int) -> None:
        """Advance the game clock by the provided number of milliseconds."""
        self.time_ms += milliseconds
        self._apply_arrived_moves()

    def _promote_pawns(self) -> None:
        """Promote any pawn that has reached the last row to a queen."""
        for col in range(self.board.width):
            if self.board.rows[0][col] == "wP":
                self.board.rows[0][col] = "wQ"
            if self.board.rows[self.board.height - 1][col] == "bP":
                self.board.rows[self.board.height - 1][col] = "bQ"

    def _is_piece_in_transit(self, position: tuple[int, int]) -> bool:
        """Return whether a piece at the given position is already moving."""
        return any(start == position for start, end, arrival_time in self.pending_moves)

    def _apply_arrived_moves(self) -> None:
        """Apply all pending moves whose arrival time has been reached."""
        remaining = []
        for move in self.pending_moves:
            start, end, arrival_time = move
            if self.time_ms >= arrival_time:
                airborne_positions = [pos for pos, land_time in self.airborne if self.time_ms <= land_time]
                if end in airborne_positions:
                    self.board.rows[start[0]][start[1]] = "."
                else:
                    pieces_before = [cell for row in self.board.rows for cell in row]
                    self.movement_rules.apply_move(self.board, start, end)
                    self._promote_pawns()
                    pieces_after = [cell for row in self.board.rows for cell in row]
                    if ("wK" in pieces_before and "wK" not in pieces_after) or \
                       ("bK" in pieces_before and "bK" not in pieces_after):
                        self.game_over = True
            else:
                remaining.append(move)
        self.pending_moves = remaining
        self.airborne = [(pos, land_time) for pos, land_time in self.airborne if self.time_ms < land_time]

    def _is_king_captured(self) -> bool:
        """Return whether a king that was on the board has been captured."""
        pieces = [cell for row in self.board.rows for cell in row]
        return "bK" not in pieces or "wK" not in pieces

    def print_board(self) -> str:
        """Return the current settled board state after completed moves."""
        self._apply_arrived_moves()
        return self.board.to_canonical_string()

    def _is_own_piece(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        """Return whether the destination contains a piece of the same color."""
        start_piece = self.board.rows[start[0]][start[1]]
        end_piece = self.board.rows[end[0]][end[1]]
        return (
            end_piece != "."
            and self.movement_rules._get_piece_color(start_piece) is not None
            and self.movement_rules._get_piece_color(start_piece) == self.movement_rules._get_piece_color(end_piece)
        )

    def _is_inside_board(self, row: int, col: int) -> bool:
        """Return whether the coordinates fall within the board bounds."""
        return 0 <= row < self.board.height and 0 <= col < self.board.width
