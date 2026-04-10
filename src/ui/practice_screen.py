"""Practice screen: live drill UI with target display, timer, feedback."""

from __future__ import annotations
import time
import threading
from typing import Callable, Optional

import dearpygui.dearpygui as dpg

from ..exercise import ExerciseSession, ExerciseMode, SessionConfig, Target
from ..midi_input import MidiInputManager
from ..theory import (
    NoteTarget, ChordTarget, InversionTarget,
    StaffNoteTarget, StaffChordTarget,
    pc_to_note_name, midi_to_pc,
)
from .staff_renderer import StaffRenderer
from .theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, ACCENT_BLUE, CYAN_HIGHLIGHT,
    GREEN_SUCCESS, RED_ERROR, YELLOW_WARN,
)

STAFF_MODES = {
    ExerciseMode.STAFF_NOTE_TREBLE, ExerciseMode.STAFF_NOTE_BASS,
    ExerciseMode.STAFF_CHORD_TREBLE, ExerciseMode.STAFF_CHORD_BASS,
}


class PracticeScreen:
    """Renders the live practice drill UI."""

    TAG = "practice_screen"

    def __init__(
        self,
        midi: MidiInputManager,
        on_session_end: Callable[[ExerciseSession], None],
        font_large: int = 0,
        font_medium: int = 0,
        font_heading: int = 0,
    ) -> None:
        self.midi = midi
        self.on_session_end = on_session_end
        self.font_large = font_large
        self.font_medium = font_medium
        self.font_heading = font_heading
        self.session: Optional[ExerciseSession] = None
        self._feedback_timer: Optional[float] = None
        self._feedback_type: Optional[str] = None  # "correct" or "incorrect"
        self._waiting_advance = False
        self._advance_at: Optional[float] = None
        self._staff_renderer: Optional[StaffRenderer] = None
        self._is_staff_mode = False

    # ── Build UI ─────────────────────────────────────────────────

    def build(self) -> None:
        if dpg.does_item_exist(self.TAG):
            dpg.delete_item(self.TAG)

        with dpg.group(tag=self.TAG, parent="primary_window"):

            # ── Top bar card ─────────────────────────────────────
            with dpg.child_window(height=50, border=True, tag="practice_topbar"):
                dpg.bind_item_theme("practice_topbar", "theme_card")
                with dpg.group(horizontal=True):
                    dpg.add_text("", tag="progress_text", color=TEXT_SECONDARY)
                    dpg.add_spacer(width=20)
                    progress_bar = dpg.add_progress_bar(
                        default_value=0.0, tag="progress_bar",
                        width=200, overlay="0%",
                    )
                    dpg.bind_item_theme(progress_bar, "theme_progress")
                    dpg.add_spacer(width=30)
                    streak_id = dpg.add_text("Streak: 0", tag="streak_text", color=YELLOW_WARN)
                    if self.font_heading:
                        dpg.bind_item_font(streak_id, self.font_heading)
                    dpg.add_spacer(width=30)
                    quit_btn = dpg.add_button(label="End Session", callback=self._on_quit)
                    dpg.bind_item_theme(quit_btn, "theme_btn_danger")

            dpg.add_spacer(height=20)

            # ── Central target area ──────────────────────────────
            with dpg.child_window(height=340, border=True, tag="practice_target_card"):
                dpg.bind_item_theme("practice_target_card", "theme_card_accent")

                dpg.add_spacer(height=10)
                dpg.add_text("Play:", color=TEXT_MUTED, indent=30)
                dpg.add_spacer(height=4)

                # Text target display (for non-staff modes)
                with dpg.group(tag="text_target_group"):
                    target_id = dpg.add_text("", tag="target_label", color=TEXT_PRIMARY, indent=30)
                    if self.font_large:
                        dpg.bind_item_font(target_id, self.font_large)

                # Staff target display (for staff modes)
                with dpg.group(tag="staff_target_group", show=False):
                    self._staff_renderer = StaffRenderer(
                        parent="staff_target_group", tag="staff_drawlist",
                    )
                    self._staff_renderer.build()

                dpg.add_spacer(height=4)

                # Timer
                timer_id = dpg.add_text("0.000s", tag="timer_text", color=TEXT_SECONDARY, indent=30)
                if self.font_medium:
                    dpg.bind_item_font(timer_id, self.font_medium)
                dpg.add_spacer(height=8)

                # Feedback line
                feedback_id = dpg.add_text("", tag="feedback_text", indent=30)
                if self.font_heading:
                    dpg.bind_item_font(feedback_id, self.font_heading)

            dpg.add_spacer(height=16)

            # ── Pressed notes bar ────────────────────────────────
            with dpg.child_window(height=60, border=True, tag="practice_pressed_card"):
                dpg.bind_item_theme("practice_pressed_card", "theme_card")
                dpg.add_text("Currently pressed:", color=TEXT_MUTED)
                pressed_id = dpg.add_text("--", tag="pressed_notes_text", color=CYAN_HIGHLIGHT)
                if self.font_heading:
                    dpg.bind_item_font(pressed_id, self.font_heading)

    # ── Session lifecycle ────────────────────────────────────────

    def start_session(self, config: SessionConfig) -> None:
        """Initialize and start a new exercise session."""
        self.session = ExerciseSession(config)
        self._waiting_advance = False
        self._advance_at = None
        self._is_staff_mode = config.mode in STAFF_MODES

        # Toggle which display to show
        dpg.configure_item("text_target_group", show=not self._is_staff_mode)
        dpg.configure_item("staff_target_group", show=self._is_staff_mode)

        target = self.session.start()
        if target is None:
            dpg.set_value("target_label", "No targets available for this configuration.")
            return

        self._show_target(target)
        self._update_progress()
        self.midi.add_callback(self._midi_callback)

    def _show_target(self, target: Target) -> None:
        """Update the target display."""
        dpg.set_value("feedback_text", "")

        if self._is_staff_mode and self._staff_renderer and self.session:
            mode = self.session.config.mode
            clef = "treble" if mode in (ExerciseMode.STAFF_NOTE_TREBLE, ExerciseMode.STAFF_CHORD_TREBLE) else "bass"
            if isinstance(target, StaffNoteTarget):
                self._staff_renderer.draw_note(target, clef)
            elif isinstance(target, StaffChordTarget):
                self._staff_renderer.draw_chord(target, clef)
        else:
            label = ""
            if isinstance(target, NoteTarget):
                label = target.label
            elif isinstance(target, (ChordTarget, InversionTarget)):
                label = target.label
            dpg.set_value("target_label", label)
            dpg.configure_item("target_label", color=TEXT_PRIMARY)

    def _update_progress(self) -> None:
        if self.session is None:
            return
        answered = self.session.questions_answered
        total = self.session.total_questions
        if total:
            dpg.set_value("progress_text", f"Q {answered + 1} / {total}")
            pct = answered / total
            dpg.set_value("progress_bar", pct)
            dpg.configure_item("progress_bar", overlay=f"{int(pct * 100)}%")
        else:
            dpg.set_value("progress_text", f"Q {answered + 1}")
            dpg.set_value("progress_bar", 0.0)
            dpg.configure_item("progress_bar", overlay="")
        dpg.set_value("streak_text", f"Streak: {self.session.streak}")

    # ── MIDI callback (runs on mido thread) ──────────────────────

    def _midi_callback(self, msg_type: str, note: int, velocity: int) -> None:
        if self.session is None or self.session.is_finished:
            return
        if self._waiting_advance:
            return
        chord_like_modes = (
            ExerciseMode.CHORD, ExerciseMode.INVERSION,
            ExerciseMode.STAFF_CHORD_TREBLE, ExerciseMode.STAFF_CHORD_BASS,
        )
        if msg_type != "note_on":
            if self.session.config.mode in chord_like_modes:
                pass  # fall through to check
            else:
                return

        mode = self.session.config.mode

        if mode == ExerciseMode.NOTE and msg_type == "note_on":
            correct = self.session.validate_note(note)
            if correct:
                self._on_correct()
            else:
                self._on_incorrect()

        elif mode in (ExerciseMode.STAFF_NOTE_TREBLE, ExerciseMode.STAFF_NOTE_BASS) and msg_type == "note_on":
            correct = self.session.validate_staff_note(note)
            if correct:
                self._on_correct()
            else:
                self._on_incorrect()

        elif mode == ExerciseMode.CHORD:
            pressed_pcs = self.midi.state.pressed_pitch_classes
            if len(pressed_pcs) >= 3:
                correct = self.session.validate_chord(pressed_pcs)
                if correct:
                    self._on_correct()

        elif mode == ExerciseMode.INVERSION:
            pressed_pcs = self.midi.state.pressed_pitch_classes
            lowest = self.midi.state.lowest_pressed_note
            if len(pressed_pcs) >= 3:
                correct = self.session.validate_inversion(pressed_pcs, lowest)
                if correct:
                    self._on_correct()

        elif mode in (ExerciseMode.STAFF_CHORD_TREBLE, ExerciseMode.STAFF_CHORD_BASS):
            pressed_notes = self.midi.state.pressed_notes
            if len(pressed_notes) >= 3:
                correct = self.session.validate_staff_chord(pressed_notes)
                if correct:
                    self._on_correct()

    def _on_correct(self) -> None:
        self._feedback_type = "correct"
        self._feedback_timer = time.perf_counter()
        self._waiting_advance = True
        if self.session:
            self._advance_at = time.perf_counter() + self.session.config.auto_advance_delay_sec

    def _on_incorrect(self) -> None:
        self._feedback_type = "incorrect"
        self._feedback_timer = time.perf_counter()

    # ── Frame update (called from main render loop) ──────────────

    def update(self) -> None:
        """Called each frame from the main loop."""
        if self.session is None:
            return

        # Update timer
        if self.session.current_attempt and not self._waiting_advance:
            elapsed = time.perf_counter() - self.session.current_attempt.started_at
            dpg.set_value("timer_text", f"{elapsed:.3f}s")

        # Update pressed notes display
        pressed = self.midi.state.pressed_notes
        if pressed:
            names = sorted(pressed)
            display = "   ".join(f"{pc_to_note_name(midi_to_pc(n))}{n // 12 - 1}" for n in names)
            dpg.set_value("pressed_notes_text", display)
        else:
            dpg.set_value("pressed_notes_text", "--")

        # Feedback display
        if self._feedback_type == "correct":
            dpg.set_value("feedback_text", "Correct!")
            dpg.configure_item("feedback_text", color=GREEN_SUCCESS)
            dpg.configure_item("target_label", color=GREEN_SUCCESS)
        elif self._feedback_type == "incorrect":
            dpg.set_value("feedback_text", "Try again...")
            dpg.configure_item("feedback_text", color=RED_ERROR)
            dpg.configure_item("target_label", color=RED_ERROR)
            # Clear incorrect feedback after 0.3s
            if self._feedback_timer and (time.perf_counter() - self._feedback_timer > 0.3):
                self._feedback_type = None
                dpg.set_value("feedback_text", "")
                dpg.configure_item("target_label", color=TEXT_PRIMARY)

        # Auto-advance after correct
        if self._waiting_advance and self._advance_at:
            if time.perf_counter() >= self._advance_at:
                self._waiting_advance = False
                self._advance_at = None
                self._feedback_type = None
                self._advance()

    def _advance(self) -> None:
        """Move to the next target or end the session."""
        if self.session is None:
            return

        target = self.session.next_target()
        if target is None or self.session.is_finished:
            self._end_session()
            return

        self._show_target(target)
        self._update_progress()

    def _on_quit(self) -> None:
        if self.session:
            self.session.finish()
            self._end_session()

    def _end_session(self) -> None:
        self.midi.remove_callback(self._midi_callback)
        if self.session:
            self.on_session_end(self.session)
        self.session = None

    # ── Visibility ───────────────────────────────────────────────

    def show(self) -> None:
        if dpg.does_item_exist(self.TAG):
            dpg.configure_item(self.TAG, show=True)
        else:
            self.build()

    def hide(self) -> None:
        if dpg.does_item_exist(self.TAG):
            dpg.configure_item(self.TAG, show=False)
