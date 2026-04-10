"""Tests for the exercise engine."""

import pytest
from src.theory import KeySpec, note_name_to_pc
from src.exercise import ExerciseSession, ExerciseMode, SessionConfig


def _make_config(mode=ExerciseMode.NOTE, keys=None, count=5):
    if keys is None:
        keys = [KeySpec(root="C", mode="major")]
    return SessionConfig(mode=mode, selected_keys=keys, question_count=count)


class TestNoteExercise:
    def test_session_start_returns_target(self):
        session = ExerciseSession(_make_config())
        target = session.start()
        assert target is not None

    def test_pool_size_c_major(self):
        session = ExerciseSession(_make_config())
        assert session.pool_size == 7

    def test_correct_note_validates(self):
        session = ExerciseSession(_make_config())
        target = session.start()
        # Find a MIDI note that matches the target pitch class
        midi_note = 60 + target.pitch_class
        result = session.validate_note(midi_note)
        assert result is True

    def test_incorrect_note_fails(self):
        session = ExerciseSession(_make_config())
        target = session.start()
        # Play a note that definitely doesn't match
        wrong_pc = (target.pitch_class + 1) % 12
        midi_note = 60 + wrong_pc
        result = session.validate_note(midi_note)
        assert result is False

    def test_session_finishes_after_count(self):
        config = _make_config(count=3)
        session = ExerciseSession(config)
        session.start()

        for _ in range(3):
            t = session.current_target
            if t is None:
                break
            midi_note = 60 + t.pitch_class
            session.validate_note(midi_note)
            session.next_target()

        assert session.questions_answered == 3

    def test_streak_tracking(self):
        session = ExerciseSession(_make_config(count=5))
        session.start()

        # Get two correct
        for _ in range(2):
            t = session.current_target
            session.validate_note(60 + t.pitch_class)
            session.next_target()

        assert session.streak == 2
        assert session.best_streak == 2

    def test_avoid_immediate_repeat(self):
        config = _make_config(count=50)
        session = ExerciseSession(config)
        session.start()

        prev = session.current_target
        repeats = 0
        for _ in range(49):
            session.validate_note(60 + session.current_target.pitch_class)
            session.next_target()
            if session.current_target == prev:
                repeats += 1
            prev = session.current_target

        # With 7 notes in pool, we should almost never have immediate repeats
        assert repeats < 5


class TestChordExercise:
    def test_chord_session_start(self):
        config = _make_config(mode=ExerciseMode.CHORD)
        session = ExerciseSession(config)
        target = session.start()
        assert target is not None

    def test_correct_chord_validates(self):
        config = _make_config(mode=ExerciseMode.CHORD)
        session = ExerciseSession(config)
        target = session.start()
        pcs = target.pitch_class_set
        result = session.validate_chord(set(pcs))
        assert result is True


class TestInversionExercise:
    def test_inversion_session_start(self):
        config = _make_config(mode=ExerciseMode.INVERSION)
        session = ExerciseSession(config)
        target = session.start()
        assert target is not None

    def test_correct_inversion_validates(self):
        config = _make_config(mode=ExerciseMode.INVERSION)
        session = ExerciseSession(config)
        target = session.start()
        pcs = target.pitch_class_set
        # Simulate lowest note matching the expected bass
        lowest_midi = 48 + target.bass_pitch_class
        result = session.validate_inversion(set(pcs), lowest_midi)
        assert result is True

    def test_wrong_bass_note_fails(self):
        config = _make_config(mode=ExerciseMode.INVERSION)
        session = ExerciseSession(config)
        target = session.start()
        pcs = target.pitch_class_set
        # Use wrong bass note
        wrong_bass = 48 + ((target.bass_pitch_class + 1) % 12)
        result = session.validate_inversion(set(pcs), wrong_bass)
        assert result is False
