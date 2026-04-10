"""Music theory helpers: scales, keys, chords, pitch-class utilities."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

# ── Pitch-class constants ────────────────────────────────────────────

NOTE_NAMES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_NAMES_FLAT  = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Mapping from any common spelling → pitch class 0-11
_NAME_TO_PC: dict[str, int] = {}
for _i, _n in enumerate(NOTE_NAMES_SHARP):
    _NAME_TO_PC[_n] = _i
for _i, _n in enumerate(NOTE_NAMES_FLAT):
    _NAME_TO_PC[_n] = _i
# Extra enharmonics
_NAME_TO_PC.update({
    "E#": 5, "Fb": 4, "B#": 0, "Cb": 11,
    "Db": 1, "D#": 3, "Gb": 6, "Ab": 8, "Bb": 10,
})


def note_name_to_pc(name: str) -> int:
    """Convert a note name like 'C#' or 'Bb' to pitch class 0-11."""
    if name not in _NAME_TO_PC:
        raise ValueError(f"Unknown note name: {name}")
    return _NAME_TO_PC[name]


def midi_to_pc(midi_note: int) -> int:
    """Convert a MIDI note number (0-127) to pitch class 0-11."""
    return midi_note % 12


def pc_to_note_name(pc: int, prefer_flat: bool = False) -> str:
    """Convert pitch class 0-11 to a note name string."""
    table = NOTE_NAMES_FLAT if prefer_flat else NOTE_NAMES_SHARP
    return table[pc % 12]


# ── Scale intervals ──────────────────────────────────────────────────

MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]  # W W H W W W H
MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]  # natural minor


# Keys that conventionally use flats in their spelling
FLAT_KEYS = {"F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb",
             "D", "G", "C", "F", "Bb", "Eb", "Ab"}  # minor flat keys overlap
# More precise: determine by root name
def _prefers_flat(root: str) -> bool:
    """Return True if the key root conventionally spells with flats."""
    return "b" in root or root in ("F",)


# ── Canonical key-aware note spelling ────────────────────────────────

# For each major key root, the correct spelling of each scale degree
_MAJOR_SCALE_SPELLINGS: dict[str, list[str]] = {
    "C":  ["C", "D", "E", "F", "G", "A", "B"],
    "G":  ["G", "A", "B", "C", "D", "E", "F#"],
    "D":  ["D", "E", "F#", "G", "A", "B", "C#"],
    "A":  ["A", "B", "C#", "D", "E", "F#", "G#"],
    "E":  ["E", "F#", "G#", "A", "B", "C#", "D#"],
    "B":  ["B", "C#", "D#", "E", "F#", "G#", "A#"],
    "F#": ["F#", "G#", "A#", "B", "C#", "D#", "E#"],
    "F":  ["F", "G", "A", "Bb", "C", "D", "E"],
    "Bb": ["Bb", "C", "D", "Eb", "F", "G", "A"],
    "Eb": ["Eb", "F", "G", "Ab", "Bb", "C", "D"],
    "Ab": ["Ab", "Bb", "C", "Db", "Eb", "F", "G"],
    "Db": ["Db", "Eb", "F", "Gb", "Ab", "Bb", "C"],
    "Gb": ["Gb", "Ab", "Bb", "Cb", "Db", "Eb", "F"],
}

_MINOR_SCALE_SPELLINGS: dict[str, list[str]] = {
    "A":  ["A", "B", "C", "D", "E", "F", "G"],
    "E":  ["E", "F#", "G", "A", "B", "C", "D"],
    "B":  ["B", "C#", "D", "E", "F#", "G", "A"],
    "F#": ["F#", "G#", "A", "B", "C#", "D", "E"],
    "C#": ["C#", "D#", "E", "F#", "G#", "A", "B"],
    "G#": ["G#", "A#", "B", "C#", "D#", "E", "F#"],
    "D":  ["D", "E", "F", "G", "A", "Bb", "C"],
    "G":  ["G", "A", "Bb", "C", "D", "Eb", "F"],
    "C":  ["C", "D", "Eb", "F", "G", "Ab", "Bb"],
    "F":  ["F", "G", "Ab", "Bb", "C", "Db", "Eb"],
    "Bb": ["Bb", "C", "Db", "Eb", "F", "Gb", "Ab"],
    "Eb": ["Eb", "F", "Gb", "Ab", "Bb", "Cb", "Db"],
}


# ── Data classes ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class KeySpec:
    root: str          # e.g. "C", "F#", "Bb"
    mode: str          # "major" or "minor"

    @property
    def label(self) -> str:
        return f"{self.root} {self.mode}"

    def scale_note_names(self) -> list[str]:
        """Return the 7 scale-degree note names with correct spelling."""
        if self.mode == "major":
            spellings = _MAJOR_SCALE_SPELLINGS.get(self.root)
        else:
            spellings = _MINOR_SCALE_SPELLINGS.get(self.root)

        if spellings is not None:
            return list(spellings)

        # Fallback: build from intervals with generic sharp/flat preference
        intervals = MAJOR_INTERVALS if self.mode == "major" else MINOR_INTERVALS
        root_pc = note_name_to_pc(self.root)
        prefer_flat = _prefers_flat(self.root)
        return [pc_to_note_name((root_pc + iv) % 12, prefer_flat=prefer_flat)
                for iv in intervals]

    def scale_pitch_classes(self) -> list[int]:
        """Return the 7 pitch classes of this key's scale."""
        return [note_name_to_pc(n) for n in self.scale_note_names()]


@dataclass(frozen=True)
class NoteTarget:
    label: str         # display name, e.g. "F#"
    pitch_class: int   # 0-11


@dataclass(frozen=True)
class ChordTarget:
    root: str
    quality: str       # "maj", "min", "dim"
    label: str         # e.g. "C major"
    pitch_classes: tuple[int, ...]  # sorted pitch-class set

    @property
    def pitch_class_set(self) -> frozenset[int]:
        return frozenset(self.pitch_classes)


@dataclass(frozen=True)
class InversionTarget:
    root: str
    quality: str
    inversion: int     # 0 = root, 1 = 1st, 2 = 2nd
    label: str         # e.g. "C major — 1st inversion"
    pitch_classes: tuple[int, ...]  # sorted pitch-class set
    bass_pitch_class: int           # expected lowest note pitch class

    @property
    def pitch_class_set(self) -> frozenset[int]:
        return frozenset(self.pitch_classes)


@dataclass(frozen=True)
class StaffNoteTarget:
    midi_note: int         # specific MIDI note, e.g. 60 for C4
    note_name: str         # e.g. "C", "F#", "Bb"
    accidental: str        # "", "#", "b"
    octave: int            # e.g. 4
    pitch_class: int       # 0-11

    @property
    def label(self) -> str:
        return f"{self.note_name}{self.octave}"


@dataclass(frozen=True)
class StaffChordTarget:
    root: str
    quality: str
    label: str              # e.g. "C major"
    midi_notes: tuple[int, ...]    # specific MIDI notes, lowest first
    note_names: tuple[str, ...]    # e.g. ("C", "E", "G")
    accidentals: tuple[str, ...]   # e.g. ("", "", "")
    octaves: tuple[int, ...]
    pitch_classes: tuple[int, ...]  # sorted unique pitch classes

    @property
    def pitch_class_set(self) -> frozenset[int]:
        return frozenset(self.pitch_classes)


# ── Chord building helpers ───────────────────────────────────────────

CHORD_INTERVALS: dict[str, tuple[int, ...]] = {
    "maj": (0, 4, 7),
    "min": (0, 3, 7),
    "dim": (0, 3, 6),
}

QUALITY_DISPLAY: dict[str, str] = {
    "maj": "major",
    "min": "minor",
    "dim": "diminished",
}

# Diatonic triad qualities for major scale degrees (1-indexed)
_MAJOR_DIATONIC_QUALITIES = ["maj", "min", "min", "maj", "maj", "min", "dim"]
# Diatonic triad qualities for natural minor scale degrees
_MINOR_DIATONIC_QUALITIES = ["min", "dim", "maj", "min", "min", "maj", "maj"]


def build_chord(root_name: str, quality: str) -> ChordTarget:
    """Build a ChordTarget from root name and quality."""
    root_pc = note_name_to_pc(root_name)
    intervals = CHORD_INTERVALS[quality]
    pcs = tuple(sorted((root_pc + iv) % 12 for iv in intervals))
    label = f"{root_name} {QUALITY_DISPLAY[quality]}"
    return ChordTarget(root=root_name, quality=quality, label=label, pitch_classes=pcs)


def build_inversion_target(root_name: str, quality: str, inversion: int) -> InversionTarget:
    """Build an InversionTarget for a given chord and inversion number."""
    root_pc = note_name_to_pc(root_name)
    intervals = CHORD_INTERVALS[quality]
    pcs = tuple(sorted((root_pc + iv) % 12 for iv in intervals))

    # Bass note for each inversion
    bass_pc = (root_pc + intervals[inversion]) % 12

    inv_labels = {0: "root position", 1: "1st inversion", 2: "2nd inversion"}
    label = f"{root_name} {QUALITY_DISPLAY[quality]} — {inv_labels[inversion]}"

    return InversionTarget(
        root=root_name,
        quality=quality,
        inversion=inversion,
        label=label,
        pitch_classes=pcs,
        bass_pitch_class=bass_pc,
    )


# ── Pool builders ────────────────────────────────────────────────────

def build_note_pool(keys: list[KeySpec]) -> list[NoteTarget]:
    """Build a deduplicated list of NoteTargets from the union of selected keys."""
    seen_pcs: set[int] = set()
    pool: list[NoteTarget] = []
    for key in keys:
        for name in key.scale_note_names():
            pc = note_name_to_pc(name)
            if pc not in seen_pcs:
                seen_pcs.add(pc)
                pool.append(NoteTarget(label=name, pitch_class=pc))
    return pool


def build_chord_pool(
    keys: list[KeySpec],
    allowed_qualities: set[str] | None = None,
) -> list[ChordTarget]:
    """Build a deduplicated list of ChordTargets from the diatonic triads of selected keys."""
    if allowed_qualities is None:
        allowed_qualities = {"maj", "min", "dim"}

    seen: set[tuple[int, ...]] = set()
    pool: list[ChordTarget] = []

    for key in keys:
        names = key.scale_note_names()
        qualities = (_MAJOR_DIATONIC_QUALITIES if key.mode == "major"
                     else _MINOR_DIATONIC_QUALITIES)

        for degree_idx, (note_name, quality) in enumerate(zip(names, qualities)):
            if quality not in allowed_qualities:
                continue
            chord = build_chord(note_name, quality)
            if chord.pitch_classes not in seen:
                seen.add(chord.pitch_classes)
                pool.append(chord)

    return pool


def build_inversion_pool(
    keys: list[KeySpec],
    allowed_qualities: set[str] | None = None,
) -> list[InversionTarget]:
    """Build a pool of InversionTargets (all inversions for each diatonic chord)."""
    if allowed_qualities is None:
        allowed_qualities = {"maj", "min", "dim"}

    seen: set[tuple[tuple[int, ...], int]] = set()
    pool: list[InversionTarget] = []

    for key in keys:
        names = key.scale_note_names()
        qualities = (_MAJOR_DIATONIC_QUALITIES if key.mode == "major"
                     else _MINOR_DIATONIC_QUALITIES)

        for note_name, quality in zip(names, qualities):
            if quality not in allowed_qualities:
                continue
            num_inversions = len(CHORD_INTERVALS[quality])
            for inv in range(num_inversions):
                target = build_inversion_target(note_name, quality, inv)
                dedup_key = (target.pitch_classes, inv)
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    pool.append(target)

    return pool


# ── All available key roots ──────────────────────────────────────────

ALL_MAJOR_KEYS = [KeySpec(root=r, mode="major") for r in
                  ["C", "G", "D", "A", "E", "B", "F#", "F", "Bb", "Eb", "Ab", "Db", "Gb"]]

ALL_MINOR_KEYS = [KeySpec(root=r, mode="minor") for r in
                  ["A", "E", "B", "F#", "C#", "G#", "D", "G", "C", "F", "Bb", "Eb"]]


# ── Staff position utilities ────────────────────────────────────────

_LETTER_INDEX = {"C": 0, "D": 1, "E": 2, "F": 3, "G": 4, "A": 5, "B": 6}

# Clef ranges: (min_midi, max_midi)
TREBLE_RANGE = (60, 84)   # C4 to C6
BASS_RANGE   = (36, 60)   # C2 to C4


def _parse_note_name(name: str) -> tuple[str, str]:
    """Split a note name into (letter, accidental).  'F#' -> ('F', '#'), 'Bb' -> ('B', 'b')."""
    if len(name) == 1:
        return name, ""
    return name[0], name[1:]


def staff_position_treble(letter: str, octave: int) -> int:
    """Compute staff position for treble clef.  Bottom line (E4) = 0."""
    return (octave - 4) * 7 + _LETTER_INDEX[letter] - 2


def staff_position_bass(letter: str, octave: int) -> int:
    """Compute staff position for bass clef.  Bottom line (G2) = 0."""
    return (octave - 2) * 7 + _LETTER_INDEX[letter] - 4


def midi_to_octave(midi_note: int) -> int:
    """Standard MIDI octave: C4 = 60."""
    return midi_note // 12 - 1


def _spell_midi_note(midi_note: int, key: KeySpec) -> tuple[str, str, int]:
    """Return (note_name, accidental, octave) for a MIDI note using key-aware spelling."""
    pc = midi_to_pc(midi_note)
    octave = midi_to_octave(midi_note)
    scale_names = key.scale_note_names()
    scale_pcs = key.scale_pitch_classes()

    # Find matching scale degree
    for name, spc in zip(scale_names, scale_pcs):
        if spc == pc:
            letter, acc = _parse_note_name(name)
            return name, acc, octave
    # Fallback (shouldn't happen for scale-only pools)
    name = pc_to_note_name(pc, prefer_flat=_prefers_flat(key.root))
    letter, acc = _parse_note_name(name)
    return name, acc, octave


# ── Staff pool builders ─────────────────────────────────────────────

def build_staff_note_pool(
    keys: list[KeySpec],
    clef: str,  # "treble" or "bass"
) -> list[StaffNoteTarget]:
    """Build a pool of StaffNoteTargets across the given clef range."""
    midi_lo, midi_hi = TREBLE_RANGE if clef == "treble" else BASS_RANGE

    # Build a set of allowed pitch classes, and map pc -> (note_name, key)
    pc_info: dict[int, tuple[str, str]] = {}  # pc -> (note_name, accidental)
    allowed_pcs: set[int] = set()
    for key in keys:
        for name in key.scale_note_names():
            pc = note_name_to_pc(name)
            if pc not in pc_info:
                letter, acc = _parse_note_name(name)
                pc_info[pc] = (name, acc)
            allowed_pcs.add(pc)

    pool: list[StaffNoteTarget] = []
    seen: set[int] = set()
    for midi in range(midi_lo, midi_hi + 1):
        pc = midi_to_pc(midi)
        if pc in allowed_pcs and midi not in seen:
            seen.add(midi)
            name, acc = pc_info[pc]
            octave = midi_to_octave(midi)
            pool.append(StaffNoteTarget(
                midi_note=midi,
                note_name=name,
                accidental=acc,
                octave=octave,
                pitch_class=pc,
            ))
    return pool


def build_staff_chord_pool(
    keys: list[KeySpec],
    clef: str,  # "treble" or "bass"
    allowed_qualities: set[str] | None = None,
) -> list[StaffChordTarget]:
    """Build a pool of StaffChordTargets (root-position close voicings) in the clef range."""
    if allowed_qualities is None:
        allowed_qualities = {"maj", "min", "dim"}
    midi_lo, midi_hi = TREBLE_RANGE if clef == "treble" else BASS_RANGE

    seen: set[tuple[int, ...]] = set()
    pool: list[StaffChordTarget] = []

    for key in keys:
        names = key.scale_note_names()
        qualities = (_MAJOR_DIATONIC_QUALITIES if key.mode == "major"
                     else _MINOR_DIATONIC_QUALITIES)

        for degree_name, quality in zip(names, qualities):
            if quality not in allowed_qualities:
                continue

            root_pc = note_name_to_pc(degree_name)
            intervals = CHORD_INTERVALS[quality]

            # Find all root positions within range
            for root_midi in range(midi_lo, midi_hi + 1):
                if midi_to_pc(root_midi) != root_pc:
                    continue
                # Build the triad from this root
                chord_midis = []
                chord_names = []
                chord_accs = []
                chord_octs = []
                valid = True
                for iv in intervals:
                    m = root_midi + iv
                    if m > midi_hi:
                        valid = False
                        break
                    pc = midi_to_pc(m)
                    # Find spelling from scale
                    name, acc, octave = _spell_midi_note(m, key)
                    chord_midis.append(m)
                    chord_names.append(name)
                    chord_accs.append(acc)
                    chord_octs.append(octave)
                if not valid or len(chord_midis) != 3:
                    continue

                midi_tuple = tuple(chord_midis)
                if midi_tuple in seen:
                    continue
                seen.add(midi_tuple)

                pcs = tuple(sorted(set(midi_to_pc(m) for m in chord_midis)))
                label = f"{degree_name} {QUALITY_DISPLAY[quality]}"
                pool.append(StaffChordTarget(
                    root=degree_name,
                    quality=quality,
                    label=label,
                    midi_notes=midi_tuple,
                    note_names=tuple(chord_names),
                    accidentals=tuple(chord_accs),
                    octaves=tuple(chord_octs),
                    pitch_classes=pcs,
                ))

    return pool
