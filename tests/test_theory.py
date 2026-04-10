"""Tests for the music theory module."""

import pytest
from src.theory import (
    note_name_to_pc, midi_to_pc, pc_to_note_name,
    KeySpec, NoteTarget, ChordTarget,
    build_chord, build_note_pool, build_chord_pool,
    build_inversion_target, build_inversion_pool,
    CHORD_INTERVALS,
)


# ── Pitch-class conversion ──────────────────────────────────────────

class TestPitchClassConversion:
    def test_c_is_0(self):
        assert note_name_to_pc("C") == 0

    def test_sharps(self):
        assert note_name_to_pc("C#") == 1
        assert note_name_to_pc("F#") == 6

    def test_flats(self):
        assert note_name_to_pc("Bb") == 10
        assert note_name_to_pc("Eb") == 3

    def test_enharmonic(self):
        assert note_name_to_pc("C#") == note_name_to_pc("Db")
        assert note_name_to_pc("F#") == note_name_to_pc("Gb")

    def test_midi_to_pc(self):
        assert midi_to_pc(60) == 0   # C4
        assert midi_to_pc(69) == 9   # A4
        assert midi_to_pc(61) == 1   # C#4

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            note_name_to_pc("X")


# ── Scales ───────────────────────────────────────────────────────────

class TestScales:
    def test_c_major_scale(self):
        key = KeySpec(root="C", mode="major")
        names = key.scale_note_names()
        assert names == ["C", "D", "E", "F", "G", "A", "B"]

    def test_c_major_pitch_classes(self):
        key = KeySpec(root="C", mode="major")
        pcs = key.scale_pitch_classes()
        assert pcs == [0, 2, 4, 5, 7, 9, 11]

    def test_g_major_scale(self):
        key = KeySpec(root="G", mode="major")
        names = key.scale_note_names()
        assert names == ["G", "A", "B", "C", "D", "E", "F#"]

    def test_f_major_scale(self):
        key = KeySpec(root="F", mode="major")
        names = key.scale_note_names()
        assert names == ["F", "G", "A", "Bb", "C", "D", "E"]

    def test_a_minor_scale(self):
        key = KeySpec(root="A", mode="minor")
        names = key.scale_note_names()
        assert names == ["A", "B", "C", "D", "E", "F", "G"]

    def test_d_minor_scale(self):
        key = KeySpec(root="D", mode="minor")
        names = key.scale_note_names()
        assert names == ["D", "E", "F", "G", "A", "Bb", "C"]

    def test_scale_has_7_notes(self):
        key = KeySpec(root="Eb", mode="major")
        assert len(key.scale_note_names()) == 7
        assert len(key.scale_pitch_classes()) == 7

    def test_all_major_keys_have_7_unique_pcs(self):
        from src.theory import ALL_MAJOR_KEYS
        for key in ALL_MAJOR_KEYS:
            pcs = key.scale_pitch_classes()
            assert len(set(pcs)) == 7, f"{key.label} has duplicate pitch classes"

    def test_all_minor_keys_have_7_unique_pcs(self):
        from src.theory import ALL_MINOR_KEYS
        for key in ALL_MINOR_KEYS:
            pcs = key.scale_pitch_classes()
            assert len(set(pcs)) == 7, f"{key.label} has duplicate pitch classes"


# ── Chords ───────────────────────────────────────────────────────────

class TestChords:
    def test_c_major_chord(self):
        chord = build_chord("C", "maj")
        assert chord.label == "C major"
        assert set(chord.pitch_classes) == {0, 4, 7}

    def test_a_minor_chord(self):
        chord = build_chord("A", "min")
        assert chord.label == "A minor"
        assert set(chord.pitch_classes) == {9, 0, 4}

    def test_b_diminished_chord(self):
        chord = build_chord("B", "dim")
        assert chord.label == "B diminished"
        assert set(chord.pitch_classes) == {11, 2, 5}

    def test_chord_pitch_class_set(self):
        chord = build_chord("C", "maj")
        assert chord.pitch_class_set == frozenset({0, 4, 7})


# ── Pool builders ────────────────────────────────────────────────────

class TestNotePools:
    def test_c_major_note_pool(self):
        keys = [KeySpec(root="C", mode="major")]
        pool = build_note_pool(keys)
        labels = {n.label for n in pool}
        assert labels == {"C", "D", "E", "F", "G", "A", "B"}

    def test_multi_key_dedup(self):
        keys = [KeySpec(root="C", mode="major"), KeySpec(root="G", mode="major")]
        pool = build_note_pool(keys)
        pcs = [n.pitch_class for n in pool]
        # C major: C D E F G A B  +  G major adds F# only
        assert len(set(pcs)) == len(pcs), "Should have no duplicate pitch classes"
        assert 6 in pcs, "F# (pc=6) should be in the pool from G major"


class TestChordPools:
    def test_c_major_diatonic_chords(self):
        keys = [KeySpec(root="C", mode="major")]
        pool = build_chord_pool(keys)
        labels = {c.label for c in pool}
        expected = {"C major", "D minor", "E minor", "F major", "G major", "A minor", "B diminished"}
        assert labels == expected

    def test_quality_filter(self):
        keys = [KeySpec(root="C", mode="major")]
        pool = build_chord_pool(keys, allowed_qualities={"maj"})
        for chord in pool:
            assert chord.quality == "maj"

    def test_multi_key_chord_dedup(self):
        keys = [KeySpec(root="C", mode="major"), KeySpec(root="G", mode="major")]
        pool = build_chord_pool(keys)
        pc_sets = [c.pitch_classes for c in pool]
        assert len(pc_sets) == len(set(pc_sets)), "Should have no duplicate chords by pitch class"


# ── Inversions ───────────────────────────────────────────────────────

class TestInversions:
    def test_c_major_root_position(self):
        inv = build_inversion_target("C", "maj", 0)
        assert inv.bass_pitch_class == 0  # C
        assert "root position" in inv.label

    def test_c_major_first_inversion(self):
        inv = build_inversion_target("C", "maj", 1)
        assert inv.bass_pitch_class == 4  # E
        assert "1st inversion" in inv.label

    def test_c_major_second_inversion(self):
        inv = build_inversion_target("C", "maj", 2)
        assert inv.bass_pitch_class == 7  # G
        assert "2nd inversion" in inv.label

    def test_all_inversions_same_pitch_classes(self):
        pcs = set()
        for i in range(3):
            inv = build_inversion_target("C", "maj", i)
            pcs.add(inv.pitch_class_set)
        assert len(pcs) == 1, "All inversions should have the same pitch class set"

    def test_inversion_pool_size(self):
        keys = [KeySpec(root="C", mode="major")]
        pool = build_inversion_pool(keys)
        # 7 diatonic chords × 3 inversions each = 21
        assert len(pool) == 21


# ── Staff position ──────────────────────────────────────────────────

from src.theory import (
    staff_position_treble, staff_position_bass, midi_to_octave,
    build_staff_note_pool, build_staff_chord_pool, StaffNoteTarget, StaffChordTarget,
)


class TestStaffPosition:
    def test_treble_e4_bottom_line(self):
        assert staff_position_treble("E", 4) == 0

    def test_treble_c4_below_staff(self):
        assert staff_position_treble("C", 4) == -2

    def test_treble_f5_top_line(self):
        assert staff_position_treble("F", 5) == 8

    def test_treble_g4_second_line(self):
        assert staff_position_treble("G", 4) == 2

    def test_bass_g2_bottom_line(self):
        assert staff_position_bass("G", 2) == 0

    def test_bass_a3_top_line(self):
        assert staff_position_bass("A", 3) == 8

    def test_bass_c4_above_staff(self):
        assert staff_position_bass("C", 4) == 10

    def test_midi_to_octave(self):
        assert midi_to_octave(60) == 4   # C4
        assert midi_to_octave(69) == 4   # A4
        assert midi_to_octave(48) == 3   # C3


class TestStaffNotePools:
    def test_c_major_treble_pool(self):
        keys = [KeySpec(root="C", mode="major")]
        pool = build_staff_note_pool(keys, "treble")
        # C4-C6 range, C major scale: C D E F G A B across ~2 octaves
        assert len(pool) > 0
        for t in pool:
            assert isinstance(t, StaffNoteTarget)
            assert 60 <= t.midi_note <= 84

    def test_c_major_bass_pool(self):
        keys = [KeySpec(root="C", mode="major")]
        pool = build_staff_note_pool(keys, "bass")
        assert len(pool) > 0
        for t in pool:
            assert 36 <= t.midi_note <= 60

    def test_staff_note_has_octave(self):
        keys = [KeySpec(root="C", mode="major")]
        pool = build_staff_note_pool(keys, "treble")
        c4 = [t for t in pool if t.midi_note == 60]
        assert len(c4) == 1
        assert c4[0].octave == 4
        assert c4[0].note_name == "C"
        assert c4[0].label == "C4"

    def test_g_major_has_fsharp(self):
        keys = [KeySpec(root="G", mode="major")]
        pool = build_staff_note_pool(keys, "treble")
        fsharp_notes = [t for t in pool if t.note_name == "F#"]
        assert len(fsharp_notes) > 0
        for t in fsharp_notes:
            assert t.accidental == "#"


class TestStaffChordPools:
    def test_c_major_treble_chords(self):
        keys = [KeySpec(root="C", mode="major")]
        pool = build_staff_chord_pool(keys, "treble")
        assert len(pool) > 0
        for t in pool:
            assert isinstance(t, StaffChordTarget)
            assert len(t.midi_notes) == 3
            assert all(60 <= m <= 84 for m in t.midi_notes)

    def test_chord_notes_ascending(self):
        keys = [KeySpec(root="C", mode="major")]
        pool = build_staff_chord_pool(keys, "treble")
        for t in pool:
            assert t.midi_notes == tuple(sorted(t.midi_notes))

    def test_quality_filter(self):
        keys = [KeySpec(root="C", mode="major")]
        pool = build_staff_chord_pool(keys, "treble", allowed_qualities={"maj"})
        for t in pool:
            assert t.quality == "maj"
