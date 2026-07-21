"""View saved game and move history from the SQLite DB (read-only).

Usage (run from the Chess/ folder):
  python -m server.history_cli                # list every game
  python -m server.history_cli <username>     # a player's games + their moves

A player's "move history" is not a separate store -- it's just the moves of
the games they played, so this reads the same games/moves tables the server
writes during play.
"""

from __future__ import annotations

import pathlib
import sys

_CHESS_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_CHESS_ROOT) not in sys.path:
    sys.path.insert(0, str(_CHESS_ROOT))

from server.persistence.db import connect  # noqa: E402
from server.persistence.game_repository import GameRepository  # noqa: E402
from server.persistence.move_repository import MoveRepository  # noqa: E402
from server.server_config import DB_PATH  # noqa: E402


def _format_game(game) -> str:
    winner = game["winner"] or "-"
    ended = game["ended_at"] or "in progress"
    return (
        f"Game #{game['id']}  room={game['room_id']}\n"
        f"  {game['white_username']} (white)  vs  {game['black_username']} (black)\n"
        f"  winner: {winner}   reason: {game['reason'] or '-'}\n"
        f"  {game['started_at']}  ->  {ended}"
    )


def _format_move(move) -> str:
    start = f"({move['start_row']},{move['start_col']})"
    end = f"({move['end_row']},{move['end_col']})"
    return f"    {move['seq']:>3}. {move['color']}  {start} -> {end}   t={move['clock_tick']:.0f}ms"


def show_all_games(games: GameRepository) -> None:
    rows = games.get_all_games()
    if not rows:
        print("No games recorded yet.")
        return
    print(f"=== All games ({len(rows)}) ===")
    for game in rows:
        print(_format_game(game))
        print()


def show_player_history(games: GameRepository, moves: MoveRepository, username: str) -> None:
    rows = games.get_games_for_player(username)
    if not rows:
        print(f"No games recorded for {username!r}.")
        return
    print(f"=== History for {username} ({len(rows)} game(s)) ===")
    for game in rows:
        print(_format_game(game))
        game_moves = moves.get_moves_for_game(game["id"])
        if game_moves:
            print("  moves:")
            for move in game_moves:
                print(_format_move(move))
        else:
            print("  (no moves recorded)")
        print()


def main() -> None:
    conn = connect(DB_PATH)
    games = GameRepository(conn)
    moves = MoveRepository(conn)
    if len(sys.argv) > 1:
        show_player_history(games, moves, sys.argv[1])
    else:
        show_all_games(games)


if __name__ == "__main__":
    main()
