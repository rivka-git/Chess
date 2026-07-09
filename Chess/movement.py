"""Movement rules and move execution logic for chess pieces."""

from __future__ import annotations

from board import Board


class MoveExecutor:
    """Execute a validated move on the board."""

    def apply_move(self, board: Board, start: tuple[int, int], end: tuple[int, int]) -> None:
        """Move a piece from start to end, replacing any captured piece."""
        start_row, start_col = start
        end_row, end_col = end
        piece = board.rows[start_row][start_col]
        board.rows[start_row][start_col] = "."
        board.rows[end_row][end_col] = piece


class MovementRules:
    """Encapsulate movement validation for chess pieces."""

    def __init__(self) -> None:
        self._piece_rules: dict[str, MoveChecker] = {
            "K": MovementRules._king_move,
            "R": MovementRules._rook_move,
            "B": MovementRules._bishop_move,
            "Q": MovementRules._queen_move,
            "N": MovementRules._knight_move,
            "P": MovementRules._pawn_move,
        }

    def register(self, piece_type: str, checker: object) -> None:
        """Register a custom movement rule for a piece type."""
        self._piece_rules[piece_type] = checker

    def is_legal_move(self, board: Board, start: tuple[int, int], end: tuple[int, int]) -> bool:
        """Return whether the requested move is legal according to the current rules."""
        start_row, start_col = start
        end_row, end_col = end

        if start == end:
            return False

        start_piece = board.rows[start_row][start_col]
        target_piece = board.rows[end_row][end_col]
        if target_piece != "." and self._get_piece_color(start_piece) == self._get_piece_color(target_piece):
            return False

        piece_type = self._get_piece_type(start_piece)
        row_delta = end_row - start_row
        col_delta = end_col - start_col
        abs_row = abs(row_delta)
        abs_col = abs(col_delta)

        checker = self._piece_rules.get(piece_type)
        if checker is None:
            return False
        return checker(self, board, start, end, row_delta, col_delta, abs_row, abs_col)

    def _king_move(self, board: Board, start: tuple[int, int], end: tuple[int, int], row_delta: int, col_delta: int, abs_row: int, abs_col: int) -> bool:
        return (abs_row, abs_col) in {(0, 1), (1, 0), (1, 1)}

    def _rook_move(self, board: Board, start: tuple[int, int], end: tuple[int, int], row_delta: int, col_delta: int, abs_row: int, abs_col: int) -> bool:
        return (row_delta == 0 or col_delta == 0) and self._is_path_clear(board, start, end)

    def _bishop_move(self, board: Board, start: tuple[int, int], end: tuple[int, int], row_delta: int, col_delta: int, abs_row: int, abs_col: int) -> bool:
        return abs_row == abs_col and self._is_path_clear(board, start, end)

    def _queen_move(self, board: Board, start: tuple[int, int], end: tuple[int, int], row_delta: int, col_delta: int, abs_row: int, abs_col: int) -> bool:
        return (
            (row_delta == 0 or col_delta == 0 or abs_row == abs_col)
            and self._is_path_clear(board, start, end)
        )

    def _knight_move(self, board: Board, start: tuple[int, int], end: tuple[int, int], row_delta: int, col_delta: int, abs_row: int, abs_col: int) -> bool:
        return {abs_row, abs_col} == {1, 2}

    def _pawn_move(self, board: Board, start: tuple[int, int], end: tuple[int, int], row_delta: int, col_delta: int, abs_row: int, abs_col: int) -> bool:
        start_row, start_col = start
        end_row, end_col = end
        color = self._get_piece_color(board.rows[start_row][start_col])
        # negative direction means white moves up (decreasing row index)
        direction = -1 if color == "w" else 1
        # white starts at the bottom row, black at the top
        start_rank = board.height - 1 if color == "w" else 0
        target = board.rows[end_row][end_col]

        if col_delta == 0 and row_delta == direction:
            return target == "."
        if col_delta == 0 and row_delta == 2 * direction and start_row == start_rank:
            mid = board.rows[start_row + direction][start_col]
            return target == "." and mid == "."
        if abs_col == 1 and row_delta == direction:
            return target != "." and self._get_piece_color(target) != color
        return False

    def _is_path_clear(self, board: Board, start: tuple[int, int], end: tuple[int, int]) -> bool:
        """Return whether every intermediate square is empty for a sliding move."""
        start_row, start_col = start
        end_row, end_col = end

        if start_row == end_row:
            step = 1 if end_col > start_col else -1
            for col in range(start_col + step, end_col, step):
                if board.rows[start_row][col] != ".":
                    return False
            return True

        if start_col == end_col:
            step = 1 if end_row > start_row else -1
            for row in range(start_row + step, end_row, step):
                if board.rows[row][start_col] != ".":
                    return False
            return True

        if abs(end_row - start_row) == abs(end_col - start_col):
            row_step = 1 if end_row > start_row else -1
            col_step = 1 if end_col > start_col else -1
            row = start_row + row_step
            col = start_col + col_step
            while (row, col) != (end_row, end_col):
                if board.rows[row][col] != ".":
                    return False
                row += row_step
                col += col_step
            return True

        return False

    def _get_piece_type(self, piece: str) -> str:
        """Return the chess piece type for a board token."""
        # tokens are either 'wK'/'bR'/... (2 chars) or bare single chars
        return piece[1] if len(piece) > 1 else piece

    def is_same_color(self, piece_a: str, piece_b: str) -> bool:
        """Return whether two pieces share the same color."""
        color_a = self._get_piece_color(piece_a)
        return color_a is not None and color_a == self._get_piece_color(piece_b)

    def _get_piece_color(self, piece: str) -> str | None:
        """Return the color of the represented piece, if any."""
        return piece[0] if piece != "." else None
