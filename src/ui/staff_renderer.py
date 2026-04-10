"""Staff notation renderer using Dear PyGui's drawlist API."""

from __future__ import annotations

import dearpygui.dearpygui as dpg

from ..theory import (
    StaffNoteTarget, StaffChordTarget,
    staff_position_treble, staff_position_bass, _parse_note_name,
)


# ── Layout constants ────────────────────────────────────────────────

STAFF_WIDTH = 500
STAFF_HEIGHT = 220
HALF_SPACE = 10          # pixels per diatonic half-step
NOTE_RADIUS = 7
STEM_LENGTH = 40
STAFF_LEFT = 80          # x-offset where staff lines start (room for clef)
STAFF_RIGHT = STAFF_WIDTH - 30
NOTE_X = STAFF_WIDTH // 2  # horizontal center for noteheads

# Vertical center — bottom staff line y-coordinate
BOTTOM_LINE_Y = STAFF_HEIGHT - 60

# Line colors
STAFF_LINE_COLOR = (120, 125, 145)
LEDGER_LINE_COLOR = (100, 105, 125)
NOTEHEAD_COLOR = (230, 232, 240)
ACCIDENTAL_COLOR = (230, 232, 240)
CLEF_COLOR = (160, 170, 200)
STEM_COLOR = (200, 205, 220)


def _pos_to_y(position: int) -> float:
    """Convert a staff position integer to a y-coordinate (higher position → lower y)."""
    return BOTTOM_LINE_Y - position * HALF_SPACE


class StaffRenderer:
    """Manages a Dear PyGui drawlist that renders music notation."""

    def __init__(self, parent: int | str, tag: str = "staff_drawlist") -> None:
        self.tag = tag
        self.parent = parent
        self._drawlist_id: int | None = None

    def build(self) -> None:
        """Create the drawlist widget."""
        if dpg.does_item_exist(self.tag):
            dpg.delete_item(self.tag)
        self._drawlist_id = dpg.add_drawlist(
            width=STAFF_WIDTH, height=STAFF_HEIGHT,
            tag=self.tag, parent=self.parent,
        )

    def clear(self) -> None:
        """Remove all drawn items from the drawlist."""
        if self._drawlist_id is not None and dpg.does_item_exist(self.tag):
            dpg.delete_item(self.tag, children_only=True)

    # ── Public API ───────────────────────────────────────────────

    def draw_note(self, target: StaffNoteTarget, clef: str) -> None:
        """Draw a single note on the staff."""
        self.clear()
        self._draw_staff_lines()
        self._draw_clef_label(clef)

        letter, acc = _parse_note_name(target.note_name)
        if clef == "treble":
            pos = staff_position_treble(letter, target.octave)
        else:
            pos = staff_position_bass(letter, target.octave)

        y = _pos_to_y(pos)
        self._draw_ledger_lines(pos)
        self._draw_notehead(NOTE_X, y)
        self._draw_stem(NOTE_X, y, pos)
        if acc:
            self._draw_accidental(NOTE_X, y, acc)

    def draw_chord(self, target: StaffChordTarget, clef: str) -> None:
        """Draw a chord (stacked noteheads) on the staff."""
        self.clear()
        self._draw_staff_lines()
        self._draw_clef_label(clef)

        positions = []
        for name, octave in zip(target.note_names, target.octaves):
            letter, acc = _parse_note_name(name)
            if clef == "treble":
                pos = staff_position_treble(letter, octave)
            else:
                pos = staff_position_bass(letter, octave)
            positions.append((pos, acc))

        # Draw ledger lines for the full range of chord notes
        all_pos = [p for p, _ in positions]
        min_pos = min(all_pos)
        max_pos = max(all_pos)
        self._draw_ledger_lines_range(min_pos, max_pos)

        # Check for seconds — offset noteheads that are 1 step apart
        sorted_notes = sorted(positions, key=lambda x: x[0])
        offsets = self._compute_notehead_offsets(sorted_notes)

        # Draw noteheads and accidentals
        for (pos, acc), x_off in zip(sorted_notes, offsets):
            y = _pos_to_y(pos)
            x = NOTE_X + x_off
            self._draw_notehead(x, y)
            if acc:
                self._draw_accidental(x, y, acc)

        # Draw a single stem spanning all notes
        if sorted_notes:
            lowest_pos = sorted_notes[0][0]
            highest_pos = sorted_notes[-1][0]
            avg_pos = (lowest_pos + highest_pos) / 2
            # Stem up if below middle, stem down if above
            if avg_pos <= 4:
                # Stem up from highest note
                top_y = _pos_to_y(highest_pos)
                dpg.draw_line(
                    (NOTE_X + NOTE_RADIUS, top_y),
                    (NOTE_X + NOTE_RADIUS, top_y - STEM_LENGTH),
                    color=STEM_COLOR, thickness=2, parent=self.tag,
                )
            else:
                # Stem down from lowest note
                bot_y = _pos_to_y(lowest_pos)
                dpg.draw_line(
                    (NOTE_X - NOTE_RADIUS, bot_y),
                    (NOTE_X - NOTE_RADIUS, bot_y + STEM_LENGTH),
                    color=STEM_COLOR, thickness=2, parent=self.tag,
                )

    # ── Staff drawing primitives ─────────────────────────────────

    def _draw_staff_lines(self) -> None:
        """Draw the 5 horizontal staff lines."""
        for i in range(5):
            pos = i * 2  # positions 0, 2, 4, 6, 8
            y = _pos_to_y(pos)
            dpg.draw_line(
                (STAFF_LEFT, y), (STAFF_RIGHT, y),
                color=STAFF_LINE_COLOR, thickness=1.5, parent=self.tag,
            )

    def _draw_clef_label(self, clef: str) -> None:
        """Draw a clef symbol on the left side of the staff using drawing primitives."""
        if clef == "treble":
            self._draw_treble_clef()
        else:
            self._draw_bass_clef()

    def _draw_treble_clef(self) -> None:
        """Draw a stylized treble clef using bezier curves and lines."""
        cx = STAFF_LEFT + 22
        # Key y-coordinates on the staff
        y_bot = _pos_to_y(-3)     # below staff
        y_g   = _pos_to_y(2)      # G line (2nd line)
        y_mid = _pos_to_y(4)      # middle line
        y_top = _pos_to_y(10)     # above staff

        col = CLEF_COLOR
        th = 2.2

        # Vertical spine
        dpg.draw_line((cx, y_bot), (cx, y_top), color=col, thickness=th, parent=self.tag)

        # Bottom curl (small circle at bottom of spine)
        curl_r = 5
        dpg.draw_circle((cx + curl_r, y_bot - 1), curl_r, color=col, thickness=th, parent=self.tag)

        # Upper S-curve: right bulge (above middle line)
        bulge_r = 14
        dpg.draw_bezier_cubic(
            (cx, _pos_to_y(8)),         # start at top line
            (cx + bulge_r + 8, _pos_to_y(7)),  # control 1
            (cx + bulge_r + 8, _pos_to_y(5)),  # control 2
            (cx, _pos_to_y(4)),         # end at middle line
            color=col, thickness=th, parent=self.tag,
        )

        # Lower S-curve: left bulge (below middle line)
        dpg.draw_bezier_cubic(
            (cx, _pos_to_y(4)),         # start at middle line
            (cx - bulge_r - 4, _pos_to_y(3)),  # control 1
            (cx - bulge_r - 4, _pos_to_y(1)),  # control 2
            (cx, _pos_to_y(0)),         # end at bottom line
            color=col, thickness=th, parent=self.tag,
        )

    def _draw_bass_clef(self) -> None:
        """Draw a stylized bass clef using bezier curves and dots."""
        cx = STAFF_LEFT + 18
        col = CLEF_COLOR
        th = 2.2

        # Main curve starting from F line (4th line, position 6)
        y_f = _pos_to_y(6)
        dpg.draw_bezier_cubic(
            (cx, y_f),                            # start on F line
            (cx + 22, _pos_to_y(7)),              # control 1 — sweep right/up
            (cx + 22, _pos_to_y(3)),              # control 2 — curve down
            (cx - 2, _pos_to_y(1)),               # end — lower left
            color=col, thickness=th, parent=self.tag,
        )

        # Dot on F line
        dpg.draw_circle((cx - 4, y_f), 3, color=col, fill=col, parent=self.tag)

        # Two dots to the right of the curve (between 3rd and 4th lines)
        dot_x = cx + 26
        dpg.draw_circle((dot_x, _pos_to_y(7)), 2.5, color=col, fill=col, parent=self.tag)
        dpg.draw_circle((dot_x, _pos_to_y(5)), 2.5, color=col, fill=col, parent=self.tag)

    def _draw_notehead(self, x: float, y: float) -> None:
        """Draw a filled oval notehead."""
        # Slight horizontal ellipse for music notation look
        dpg.draw_ellipse(
            (x - NOTE_RADIUS, y - NOTE_RADIUS + 2),
            (x + NOTE_RADIUS, y + NOTE_RADIUS - 2),
            color=NOTEHEAD_COLOR, fill=NOTEHEAD_COLOR,
            parent=self.tag,
        )

    def _draw_stem(self, x: float, y: float, position: int) -> None:
        """Draw a stem from a notehead."""
        if position <= 4:
            # Stem up (right side)
            dpg.draw_line(
                (x + NOTE_RADIUS, y),
                (x + NOTE_RADIUS, y - STEM_LENGTH),
                color=STEM_COLOR, thickness=2, parent=self.tag,
            )
        else:
            # Stem down (left side)
            dpg.draw_line(
                (x - NOTE_RADIUS, y),
                (x - NOTE_RADIUS, y + STEM_LENGTH),
                color=STEM_COLOR, thickness=2, parent=self.tag,
            )

    def _draw_accidental(self, x: float, y: float, acc: str) -> None:
        """Draw an accidental symbol to the left of the notehead."""
        if acc == "#":
            symbol = "#"
        elif acc == "b":
            symbol = "b"
        else:
            return
        dpg.draw_text(
            (x - NOTE_RADIUS - 18, y - 10), symbol,
            color=ACCIDENTAL_COLOR, size=18, parent=self.tag,
        )

    def _draw_ledger_lines(self, position: int) -> None:
        """Draw ledger lines for a single note if it's above or below the staff."""
        ledger_half_width = 18
        cx = NOTE_X

        if position < 0:
            # Below the staff: draw at each even position from 0 down to the note
            for p in range(0, position - 1, -2):
                if p < 0:
                    y = _pos_to_y(p)
                    dpg.draw_line(
                        (cx - ledger_half_width, y), (cx + ledger_half_width, y),
                        color=LEDGER_LINE_COLOR, thickness=1.5, parent=self.tag,
                    )
        elif position > 8:
            # Above the staff: draw at each even position from 8 up to the note
            for p in range(10, position + 1, 2):
                y = _pos_to_y(p)
                dpg.draw_line(
                    (cx - ledger_half_width, y), (cx + ledger_half_width, y),
                    color=LEDGER_LINE_COLOR, thickness=1.5, parent=self.tag,
                )

        # Special case: note exactly ON a ledger line (even positions outside 0-8)
        if position % 2 == 0 and (position < 0 or position > 8):
            y = _pos_to_y(position)
            dpg.draw_line(
                (cx - ledger_half_width, y), (cx + ledger_half_width, y),
                color=LEDGER_LINE_COLOR, thickness=1.5, parent=self.tag,
            )

    def _draw_ledger_lines_range(self, min_pos: int, max_pos: int) -> None:
        """Draw ledger lines covering a range of positions (for chords)."""
        ledger_half_width = 22
        cx = NOTE_X

        if min_pos < 0:
            for p in range(-2, min_pos - 1, -2):
                y = _pos_to_y(p)
                dpg.draw_line(
                    (cx - ledger_half_width, y), (cx + ledger_half_width, y),
                    color=LEDGER_LINE_COLOR, thickness=1.5, parent=self.tag,
                )
        if max_pos > 8:
            for p in range(10, max_pos + 1, 2):
                y = _pos_to_y(p)
                dpg.draw_line(
                    (cx - ledger_half_width, y), (cx + ledger_half_width, y),
                    color=LEDGER_LINE_COLOR, thickness=1.5, parent=self.tag,
                )

    @staticmethod
    def _compute_notehead_offsets(sorted_notes: list[tuple[int, str]]) -> list[int]:
        """Compute x-offsets for noteheads in a chord to avoid overlap on seconds."""
        offsets = [0] * len(sorted_notes)
        for i in range(1, len(sorted_notes)):
            prev_pos = sorted_notes[i - 1][0]
            curr_pos = sorted_notes[i][0]
            if curr_pos - prev_pos == 1:
                # Adjacent notes — offset this one to the right
                offsets[i] = NOTE_RADIUS * 2 + 2
        return offsets
