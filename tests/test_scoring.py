"""Tests for the scoring module."""

from src.exercise import AttemptRecord
from src.scoring import compute_session_stats


def _make_attempt(label="C", reaction_ms=500.0, correct=True, errors=0):
    return AttemptRecord(
        target_label=label,
        started_at=0.0,
        completed_at=reaction_ms / 1000 if reaction_ms is not None else None,
        reaction_ms=reaction_ms,
        correct=correct,
        incorrect_inputs=errors,
    )


class TestSessionStats:
    def test_perfect_session(self):
        attempts = [_make_attempt("C", 400), _make_attempt("D", 600), _make_attempt("E", 500)]
        stats = compute_session_stats(attempts, best_streak=3)
        assert stats.total_attempts == 3
        assert stats.correct_attempts == 3
        assert stats.accuracy_pct == 100.0
        assert stats.avg_reaction_ms == 500.0
        assert stats.fastest_ms == 400.0
        assert stats.slowest_ms == 600.0
        assert stats.best_streak == 3

    def test_mixed_session(self):
        attempts = [
            _make_attempt("C", 400, correct=True),
            _make_attempt("D", None, correct=False, errors=2),
            _make_attempt("E", 600, correct=True),
        ]
        stats = compute_session_stats(attempts, best_streak=1)
        assert stats.total_attempts == 3
        assert stats.correct_attempts == 2
        assert abs(stats.accuracy_pct - 66.7) < 0.1
        assert stats.avg_reaction_ms == 500.0

    def test_per_item_breakdown(self):
        attempts = [
            _make_attempt("C", 400),
            _make_attempt("C", 600),
            _make_attempt("D", 500),
        ]
        stats = compute_session_stats(attempts)
        assert "C" in stats.per_item
        assert stats.per_item["C"].attempts == 2
        assert stats.per_item["C"].avg_reaction_ms == 500.0
        assert stats.per_item["D"].attempts == 1

    def test_empty_session(self):
        stats = compute_session_stats([])
        assert stats.total_attempts == 0
        assert stats.accuracy_pct == 0.0
        assert stats.avg_reaction_ms is None
