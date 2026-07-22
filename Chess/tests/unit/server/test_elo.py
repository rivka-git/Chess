"""Unit tests for server.rating.elo.calculate_new_ratings -- a pure function,
specified here as a plain input/output truth table."""

import pytest

from server.rating.elo import calculate_new_ratings


def test_equal_ratings_white_wins_gains_half_k():
    assert calculate_new_ratings(1200, 1200, "white") == (1216, 1184)


def test_equal_ratings_black_wins_gains_half_k():
    assert calculate_new_ratings(1200, 1200, "black") == (1184, 1216)


def test_equal_ratings_draw_is_unchanged():
    assert calculate_new_ratings(1200, 1200, "draw") == (1200, 1200)


def test_big_underdog_win_moves_ratings_a_lot():
    new_white, new_black = calculate_new_ratings(1000, 1600, "white")
    assert (new_white, new_black) == (1031, 1569)
    assert new_white - 1000 > 16  # much bigger swing than the equal-ratings case


def test_expected_favorite_win_moves_ratings_a_little():
    new_white, new_black = calculate_new_ratings(1600, 1000, "white")
    assert (new_white, new_black) == (1601, 999)
    assert new_white - 1600 < 16  # much smaller swing than the equal-ratings case


def test_favorite_losing_moves_ratings_a_lot():
    assert calculate_new_ratings(1600, 1000, "black") == (1569, 1031)


def test_unequal_ratings_draw_pulls_toward_each_other():
    new_white, new_black = calculate_new_ratings(1000, 1400, "draw")
    assert new_white > 1000
    assert new_black < 1400


def test_ratings_are_zero_sum_under_default_k():
    new_white, new_black = calculate_new_ratings(1250, 1180, "white")
    assert (new_white - 1250) + (new_black - 1180) == 0


def test_invalid_result_raises():
    with pytest.raises(ValueError):
        calculate_new_ratings(1200, 1200, "purple")
