"""Exercise engine: session config, prompt generation, input validation, attempt recording."""

from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set, Union

from .theory import (
    KeySpec, NoteTarget, ChordTarget, InversionTarget,
    StaffNoteTarget, StaffChordTarget,
    build_note_pool, build_chord_pool, build_inversion_pool,
    build_staff_note_pool, build_staff_chord_pool,
    midi_to_pc,
)


class ExerciseMode(Enum):
    NOTE = "note"
    CHORD = "chord"
    INVERSION = "inversion"
    STAFF_NOTE_TREBLE = "staff_note_treble"
    STAFF_NOTE_BASS = "staff_note_bass"
    STAFF_CHORD_TREBLE = "staff_chord_treble"
    STAFF_CHORD_BASS = "staff_chord_bass"


@dataclass
class SessionConfig:
    mode: ExerciseMode
    selected_keys: list[KeySpec]
    octave_sensitive: bool = False
    chord_qualities: set[str] = field(default_factory=lambda: {"maj", "min", "dim"})
    question_count: Optional[int] = 20
    timed_duration_sec: Optional[float] = None
    allow_repeats: bool = False
    auto_advance_delay_sec: float = 0.8


Target = Union[NoteTarget, ChordTarget, InversionTarget, StaffNoteTarget, StaffChordTarget]


@dataclass
class AttemptRecord:
    target_label: str
    started_at: float          # time.perf_counter()
    completed_at: Optional[float] = None
    reaction_ms: Optional[float] = None
    correct: bool = False
    incorrect_inputs: int = 0


class ExerciseSession:
    """Manages a single practice session."""

    def __init__(self, config: SessionConfig) -> None:
        self.config = config
        self._pool: list[Target] = self._build_pool()
        self.attempts: list[AttemptRecord] = []
        self.current_target: Optional[Target] = None
        self.current_attempt: Optional[AttemptRecord] = None
        self._started = False
        self._finished = False
        self.session_start_time: Optional[float] = None
        self.streak: int = 0
        self.best_streak: int = 0
        self._last_target: Optional[Target] = None

    # ── Pool building ────────────────────────────────────────────

    def _build_pool(self) -> list[Target]:
        keys = self.config.selected_keys
        if self.config.mode == ExerciseMode.NOTE:
            return build_note_pool(keys)
        elif self.config.mode == ExerciseMode.CHORD:
            return build_chord_pool(keys, self.config.chord_qualities)
        elif self.config.mode == ExerciseMode.INVERSION:
            return build_inversion_pool(keys, self.config.chord_qualities)
        elif self.config.mode == ExerciseMode.STAFF_NOTE_TREBLE:
            return build_staff_note_pool(keys, "treble")
        elif self.config.mode == ExerciseMode.STAFF_NOTE_BASS:
            return build_staff_note_pool(keys, "bass")
        elif self.config.mode == ExerciseMode.STAFF_CHORD_TREBLE:
            return build_staff_chord_pool(keys, "treble", self.config.chord_qualities)
        elif self.config.mode == ExerciseMode.STAFF_CHORD_BASS:
            return build_staff_chord_pool(keys, "bass", self.config.chord_qualities)
        return []

    @property
    def pool_size(self) -> int:
        return len(self._pool)

    @property
    def is_finished(self) -> bool:
        return self._finished

    @property
    def total_questions(self) -> Optional[int]:
        return self.config.question_count

    @property
    def questions_answered(self) -> int:
        return len(self.attempts)

    # ── Session flow ─────────────────────────────────────────────

    def start(self) -> Optional[Target]:
        """Start the session and return the first target."""
        if not self._pool:
            return None
        self._started = True
        self.session_start_time = time.perf_counter()
        return self.next_target()

    def next_target(self) -> Optional[Target]:
        """Generate and return the next target, or None if session is over."""
        if self._finished or not self._pool:
            return None

        # Check question-count limit
        if (self.config.question_count is not None
                and self.questions_answered >= self.config.question_count):
            self._finished = True
            return None

        # Check time limit
        if (self.config.timed_duration_sec is not None
                and self.session_start_time is not None):
            elapsed = time.perf_counter() - self.session_start_time
            if elapsed >= self.config.timed_duration_sec:
                self._finished = True
                return None

        # Pick random target, avoid immediate repeat if pool allows
        target = self._pick_random()
        self.current_target = target
        self.current_attempt = AttemptRecord(
            target_label=self._target_label(target),
            started_at=time.perf_counter(),
        )
        return target

    def _pick_random(self) -> Target:
        """Pick a random target, avoiding immediate repeat when possible."""
        if len(self._pool) == 1 or self.config.allow_repeats:
            return random.choice(self._pool)

        candidates = [t for t in self._pool if t != self._last_target]
        if not candidates:
            candidates = self._pool
        choice = random.choice(candidates)
        self._last_target = choice
        return choice

    @staticmethod
    def _target_label(target: Target) -> str:
        if isinstance(target, (NoteTarget, StaffNoteTarget)):
            return target.label
        elif isinstance(target, (ChordTarget, InversionTarget, StaffChordTarget)):
            return target.label
        return str(target)

    # ── Validation ───────────────────────────────────────────────

    def validate_note(self, midi_note: int) -> bool:
        """Validate a single note input. Returns True if correct."""
        if self.current_target is None or self.current_attempt is None:
            return False
        if not isinstance(self.current_target, NoteTarget):
            return False

        played_pc = midi_to_pc(midi_note)
        correct = played_pc == self.current_target.pitch_class

        if correct:
            self._record_correct()
        else:
            self.current_attempt.incorrect_inputs += 1

        return correct

    def validate_chord(self, pressed_pitch_classes: set[int]) -> bool:
        """Validate a chord input (set of currently held pitch classes). Returns True if correct."""
        if self.current_target is None or self.current_attempt is None:
            return False
        if not isinstance(self.current_target, ChordTarget):
            return False

        expected = self.current_target.pitch_class_set
        correct = pressed_pitch_classes == expected

        if correct:
            self._record_correct()

        return correct

    def validate_inversion(self, pressed_pitch_classes: set[int], lowest_midi_note: Optional[int]) -> bool:
        """Validate an inversion input. Checks pitch classes AND bass note."""
        if self.current_target is None or self.current_attempt is None:
            return False
        if not isinstance(self.current_target, InversionTarget):
            return False

        expected_pcs = self.current_target.pitch_class_set
        pcs_correct = pressed_pitch_classes == expected_pcs

        bass_correct = False
        if lowest_midi_note is not None:
            bass_correct = midi_to_pc(lowest_midi_note) == self.current_target.bass_pitch_class

        correct = pcs_correct and bass_correct

        if correct:
            self._record_correct()

        return correct

    def record_incorrect_attempt(self) -> None:
        """Record an incorrect input (for chord/inversion modes where we check on each note change)."""
        if self.current_attempt is not None:
            self.current_attempt.incorrect_inputs += 1

    def _record_correct(self) -> None:
        """Finalize the current attempt as correct."""
        if self.current_attempt is None:
            return
        now = time.perf_counter()
        self.current_attempt.completed_at = now
        self.current_attempt.reaction_ms = (now - self.current_attempt.started_at) * 1000
        self.current_attempt.correct = True
        self.attempts.append(self.current_attempt)
        self.streak += 1
        if self.streak > self.best_streak:
            self.best_streak = self.streak

    def skip_current(self) -> None:
        """Skip the current target (count as missed)."""
        if self.current_attempt is None:
            return
        self.current_attempt.correct = False
        self.current_attempt.completed_at = time.perf_counter()
        self.attempts.append(self.current_attempt)
        self.streak = 0

    def validate_staff_note(self, midi_note: int) -> bool:
        """Validate a single note input (octave-sensitive). Returns True if correct."""
        if self.current_target is None or self.current_attempt is None:
            return False
        if not isinstance(self.current_target, StaffNoteTarget):
            return False

        correct = midi_note == self.current_target.midi_note

        if correct:
            self._record_correct()
        else:
            self.current_attempt.incorrect_inputs += 1

        return correct

    def validate_staff_chord(self, pressed_midi_notes: set[int]) -> bool:
        """Validate a chord input (octave-sensitive, exact MIDI notes). Returns True if correct."""
        if self.current_target is None or self.current_attempt is None:
            return False
        if not isinstance(self.current_target, StaffChordTarget):
            return False

        expected = set(self.current_target.midi_notes)
        correct = pressed_midi_notes == expected

        if correct:
            self._record_correct()

        return correct

    def finish(self) -> None:
        """Force-finish the session."""
        self._finished = True
