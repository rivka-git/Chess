"""Unit tests for server.matchmaking.matchmaking_queue.MatchmakingQueue --
pure logic, no networking/asyncio involved."""

from server.matchmaking.matchmaking_queue import RATING_RANGE, MatchmakingQueue


def test_find_match_on_empty_queue_returns_none():
    queue = MatchmakingQueue()
    assert queue.find_match(1200) is None


def test_find_match_within_range_returns_the_waiting_entry():
    queue = MatchmakingQueue()
    queue.add("bob", 1250, connection="bob-conn")

    match = queue.find_match(1200)

    assert match.username == "bob"
    assert match.connection == "bob-conn"


def test_find_match_outside_range_returns_none():
    queue = MatchmakingQueue()
    queue.add("bob", 1200 + RATING_RANGE + 1, connection="bob-conn")

    assert queue.find_match(1200) is None


def test_find_match_at_exact_boundary_matches():
    queue = MatchmakingQueue()
    queue.add("bob", 1200 + RATING_RANGE, connection="bob-conn")

    assert queue.find_match(1200) is not None


def test_find_match_prefers_closest_rating():
    queue = MatchmakingQueue()
    queue.add("far", 1280, connection="far-conn")
    queue.add("near", 1210, connection="near-conn")

    match = queue.find_match(1200)

    assert match.username == "near"


def test_remove_takes_entry_out_of_the_queue():
    queue = MatchmakingQueue()
    queue.add("bob", 1200, connection="bob-conn")

    queue.remove("bob")

    assert queue.find_match(1200) is None


def test_remove_unknown_username_does_not_raise():
    queue = MatchmakingQueue()
    queue.remove("nobody")  # must not raise


def test_expired_entries_are_reported_after_timeout():
    queue = MatchmakingQueue()
    queue.add("bob", 1200, connection="bob-conn", joined_at=0.0)

    assert queue.expired(now=59.0) == []
    assert [e.username for e in queue.expired(now=61.0)] == ["bob"]
