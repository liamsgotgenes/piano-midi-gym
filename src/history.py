"""Session history persistence — JSON files in ~/.midi_trainer/history/."""

from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .exercise import AttemptRecord, SessionConfig, ExerciseMode
from .scoring import SessionStats, compute_session_stats
from .theory import KeySpec

HISTORY_DIR = Path.home() / ".midi_trainer" / "history"


def _ensure_dir() -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _config_to_dict(config: SessionConfig) -> dict[str, Any]:
    return {
        "mode": config.mode.value,
        "selected_keys": [{"root": k.root, "mode": k.mode} for k in config.selected_keys],
        "octave_sensitive": config.octave_sensitive,
        "chord_qualities": sorted(config.chord_qualities),
        "question_count": config.question_count,
        "timed_duration_sec": config.timed_duration_sec,
        "allow_repeats": config.allow_repeats,
    }


def _attempt_to_dict(a: AttemptRecord) -> dict[str, Any]:
    return {
        "target_label": a.target_label,
        "reaction_ms": a.reaction_ms,
        "correct": a.correct,
        "incorrect_inputs": a.incorrect_inputs,
    }


def _stats_to_dict(stats: SessionStats) -> dict[str, Any]:
    return {
        "total_attempts": stats.total_attempts,
        "correct_attempts": stats.correct_attempts,
        "accuracy_pct": round(stats.accuracy_pct, 1),
        "avg_reaction_ms": round(stats.avg_reaction_ms, 1) if stats.avg_reaction_ms else None,
        "median_reaction_ms": round(stats.median_reaction_ms, 1) if stats.median_reaction_ms else None,
        "fastest_ms": round(stats.fastest_ms, 1) if stats.fastest_ms else None,
        "slowest_ms": round(stats.slowest_ms, 1) if stats.slowest_ms else None,
        "best_streak": stats.best_streak,
    }


def save_session(
    config: SessionConfig,
    attempts: list[AttemptRecord],
    best_streak: int,
) -> Path:
    """Save a completed session to a JSON file. Returns the file path."""
    _ensure_dir()
    stats = compute_session_stats(attempts, best_streak)
    ts = datetime.now()
    filename = ts.strftime("session_%Y%m%d_%H%M%S.json")

    data = {
        "timestamp": ts.isoformat(),
        "config": _config_to_dict(config),
        "stats": _stats_to_dict(stats),
        "attempts": [_attempt_to_dict(a) for a in attempts],
    }

    path = HISTORY_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_session_list() -> list[dict[str, Any]]:
    """Load summary info for all saved sessions, newest first."""
    _ensure_dir()
    sessions = []
    for p in sorted(HISTORY_DIR.glob("session_*.json"), reverse=True):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions.append({
                "filename": p.name,
                "timestamp": data.get("timestamp", ""),
                "mode": data.get("config", {}).get("mode", ""),
                "accuracy_pct": data.get("stats", {}).get("accuracy_pct", 0),
                "avg_reaction_ms": data.get("stats", {}).get("avg_reaction_ms"),
                "total_attempts": data.get("stats", {}).get("total_attempts", 0),
            })
        except Exception:
            continue
    return sessions


def load_session_detail(filename: str) -> Optional[dict[str, Any]]:
    """Load full session data from a specific file."""
    path = HISTORY_DIR / filename
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
