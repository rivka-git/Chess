"""Handle user input for clicks and jumps."""

from __future__ import annotations

from model.board import Board
from rules.rule_engine import MovementRules
from realtime.motion import GameTimer


class InputHandler:
    """Handle user input: clicks and jumps.

    Coordinates are always board ``(row, col)`` cells -- never pixels.
    Translating a screen position into a cell belongs to whichever adapter
    owns a screen (the UI mouse handler, the CLI script parser); the board
    itself has no notion of how large a cell is drawn.

    ``color`` is optional and defaults to ``None``, which preserves the
    original single shared-selection behavior (one mouse, implicitly
    trusted) used by the local/CLI game. When a ``color`` is supplied,
    selection is tracked per-color and a player may only select/jump their
    own pieces -- this is what lets two independent network clients share
    one board without clobbering each other's selection.
    """

    def __init__(self, game_timer: GameTimer, movement_rules: MovementRules) -> None:
        self.game_timer = game_timer
        self.movement_rules = movement_rules
        self.selected_position: tuple[int, int] | None = None
        self._selection_by_color: dict[str, tuple[int, int] | None] = {}

    def selection_for(self, color: str | None) -> tuple[int, int] | None:
        if color is None:
            return self.selected_position
        return self._selection_by_color.get(color)

    def _set_selection(self, color: str | None, position: tuple[int, int] | None) -> None:
        if color is None:
            self.selected_position = position
        else:
            self._selection_by_color[color] = position

    def handle_click(
        self,
        board: Board,
        row: int,
        col: int,
        on_move_requested: callable,
        color: str | None = None,
    ) -> None:
        if not self._is_inside_board(board, row, col):
            self._set_selection(color, None)
            return

        current_selection = self.selection_for(color)
        if current_selection is None:
            self._on_no_selection(board, row, col, color)
        else:
            self._on_piece_selected(board, row, col, on_move_requested, color, current_selection)

    def _on_no_selection(self, board: Board, row: int, col: int, color: str | None = None) -> None:
        piece = board.rows[row][col]
        if piece != "." and not self.game_timer.is_piece_in_transit((row, col)):
            if color is not None and piece[0] != color:
                return
            self._set_selection(color, (row, col))
            return
        for start, end, *_ in self.game_timer.pending_moves:
            if end == (row, col):
                moving_piece = board.rows[start[0]][start[1]]
                if color is not None and moving_piece != "." and moving_piece[0] != color:
                    return
                self._set_selection(color, start)
                return

    def _on_piece_selected(
        self,
        board: Board,
        row: int,
        col: int,
        on_move_requested: callable,
        color: str | None,
        selected_position: tuple[int, int],
    ) -> None:
        target_position = (row, col)
        target_piece = board.rows[row][col]
        selected_piece = board.rows[selected_position[0]][selected_position[1]]

        if target_position == selected_position:
            self._set_selection(color, None)
            return

        if target_piece != "." and self.movement_rules.is_same_color(selected_piece, target_piece):
            self._set_selection(color, target_position)
            return

        if selected_piece == ".":
            self._set_selection(color, None)
            return

        legal = self.movement_rules.is_legal_move(board, selected_position, target_position)
        in_transit = self.game_timer.is_piece_in_transit(selected_position)
        if legal and not in_transit:
            on_move_requested(selected_position, target_position)

        self._set_selection(color, None)

    def handle_jump(
        self,
        board: Board,
        row: int,
        col: int,
        on_jump_requested: callable,
        color: str | None = None,
    ) -> None:
        if not self._is_inside_board(board, row, col):
            return

        position = (row, col)
        piece = board.rows[row][col]

        if piece == ".":
            return

        if color is not None and piece[0] != color:
            return

        if self.game_timer.is_piece_in_transit(position):
            return

        if self.game_timer.is_piece_airborne(position):
            return

        on_jump_requested(position)

    def _is_own_piece(self, board: Board, start: tuple[int, int], end: tuple[int, int]) -> bool:
        start_piece = board.get_piece(start[0], start[1])
        end_piece = board.get_piece(end[0], end[1])
        return end_piece != "." and self.movement_rules.is_same_color(start_piece, end_piece)

    def _is_inside_board(self, board: Board, row: int, col: int) -> bool:
        return 0 <= row < board.height and 0 <= col < board.width
