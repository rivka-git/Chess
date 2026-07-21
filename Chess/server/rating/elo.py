"""Pure ELO rating math -- no I/O, so it can be specified with a plain
input/output truth table (see tests/server/test_elo.py)."""

from __future__ import annotations

_SCORES = {"white": (1.0, 0.0), "black": (0.0, 1.0), "draw": (0.5, 0.5)}


def calculate_new_ratings(white_rating: int, black_rating: int, result: str, k: int = 32) -> tuple[int, int]:
    if result not in _SCORES:
        raise ValueError(f"result must be one of {sorted(_SCORES)}, got {result!r}")
    white_score, black_score = _SCORES[result]

    expected_white = 1 / (1 + 10 ** ((black_rating - white_rating) / 400))
    expected_black = 1 - expected_white

    new_white = round(white_rating + k * (white_score - expected_white))
    new_black = round(black_rating + k * (black_score - expected_black))
    return new_white, new_black
