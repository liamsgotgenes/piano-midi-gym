"""Session and per-item scoring / statistics."""

from __future__ import annotations
import statistics
from dataclasses import dataclass, field
from typing import Optional

from .exercise import AttemptRecord


@dataclass
class SessionStats:
    total_attempts: int = 0
    correct_attempts: int = 0
    accuracy_pct: float = 0.0
    avg_reaction_ms: Optional[float] = None
    median_reaction_ms: Optional[float] = None
    fastest_ms: Optional[float] = None
    slowest_ms: Optional[float] = None
    best_streak: int = 0
    per_item: dict[str, ItemStats] = field(default_factory=dict)


@dataclass
class ItemStats:
    label: str
    attempts: int = 0
    correct: int = 0
    errors: int = 0
    avg_reaction_ms: Optional[float] = None
    times: list[float] = field(default_factory=list)


def compute_session_stats(attempts: list[AttemptRecord], best_streak: int = 0) -> SessionStats:
    """Compute aggregate statistics from a list of attempt records."""
    stats = SessionStats()
    stats.total_attempts = len(attempts)
    stats.correct_attempts = sum(1 for a in attempts if a.correct)
    stats.best_streak = best_streak

    if stats.total_attempts > 0:
        stats.accuracy_pct = (stats.correct_attempts / stats.total_attempts) * 100

    correct_times = [a.reaction_ms for a in attempts if a.correct and a.reaction_ms is not None]

    if correct_times:
        stats.avg_reaction_ms = statistics.mean(correct_times)
        stats.median_reaction_ms = statistics.median(correct_times)
        stats.fastest_ms = min(correct_times)
        stats.slowest_ms = max(correct_times)

    # Per-item breakdown
    item_data: dict[str, ItemStats] = {}
    for a in attempts:
        if a.target_label not in item_data:
            item_data[a.target_label] = ItemStats(label=a.target_label)
        item = item_data[a.target_label]
        item.attempts += 1
        if a.correct:
            item.correct += 1
            if a.reaction_ms is not None:
                item.times.append(a.reaction_ms)
        item.errors += a.incorrect_inputs

    for item in item_data.values():
        if item.times:
            item.avg_reaction_ms = statistics.mean(item.times)

    stats.per_item = item_data
    return stats
