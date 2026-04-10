"""Setup / Home screen: MIDI device, exercise config, key selection."""

from __future__ import annotations
from typing import Callable, Optional

import dearpygui.dearpygui as dpg

from ..midi_input import MidiInputManager
from ..exercise import ExerciseMode, SessionConfig
from ..theory import KeySpec, ALL_MAJOR_KEYS, ALL_MINOR_KEYS
from .theme import TEXT_SECONDARY, TEXT_MUTED, ACCENT_BLUE, CYAN_HIGHLIGHT, RED_ERROR, GREEN_SUCCESS


class SetupScreen:
    """Renders the setup screen and collects a SessionConfig."""

    TAG = "setup_screen"

    def __init__(
        self,
        midi: MidiInputManager,
        on_start: Callable[[SessionConfig], None],
        font_heading: int = 0,
    ) -> None:
        self.midi = midi
        self.on_start = on_start
        self.font_heading = font_heading

        # State
        self._selected_port: Optional[str] = None
        self._mode = ExerciseMode.NOTE
        self._selected_key_checks: dict[str, bool] = {}
        self._chord_quality_checks: dict[str, bool] = {"maj": True, "min": True, "dim": True}
        self._question_count = 20
        self._octave_sensitive = False

    def _section_heading(self, label: str) -> None:
        """Add a styled section heading."""
        t = dpg.add_text(label, color=CYAN_HIGHLIGHT)
        if self.font_heading:
            dpg.bind_item_font(t, self.font_heading)

    # ── Build UI ─────────────────────────────────────────────────

    def build(self) -> None:
        """Create the setup window/group."""
        if dpg.does_item_exist(self.TAG):
            dpg.delete_item(self.TAG)

        COL_HEIGHT = 600

        with dpg.group(tag=self.TAG, parent="primary_window"):

            # ── Title row ──────────────────────────────────────
            dpg.add_spacer(height=2)
            title = dpg.add_text("MIDI Reaction Trainer", color=ACCENT_BLUE)
            if self.font_heading:
                dpg.bind_item_font(title, self.font_heading)
            dpg.add_text("Build speed and accuracy with your MIDI keyboard", color=TEXT_MUTED)
            dpg.add_spacer(height=6)

            # ── Two-column layout ──────────────────────────────
            with dpg.group(horizontal=True):

                # ━━ LEFT COLUMN: Configuration ━━━━━━━━━━━━━━━━━
                with dpg.child_window(width=620, height=COL_HEIGHT, border=True, tag="card_config"):
                    dpg.bind_item_theme("card_config", "theme_card")

                    # ▸ MIDI Device ──────────────────────────
                    self._section_heading("MIDI Device")
                    dpg.add_spacer(height=2)
                    with dpg.group(horizontal=True):
                        ports = self.midi.list_input_ports()
                        port_items = ports if ports else ["(No MIDI devices found)"]
                        dpg.add_combo(
                            items=port_items,
                            default_value=port_items[0] if port_items else "",
                            tag="midi_port_combo",
                            callback=self._on_port_selected,
                            width=380,
                        )
                        btn = dpg.add_button(label="Refresh", callback=self._refresh_ports)
                        dpg.bind_item_theme(btn, "theme_btn_secondary")
                        dpg.add_spacer(width=8)
                        dpg.add_text("", tag="midi_status_text", color=TEXT_MUTED)

                    dpg.add_separator()
                    dpg.add_spacer(height=4)

                    # ▸ Exercise Mode ────────────────────────
                    self._section_heading("Exercise Mode")
                    dpg.add_spacer(height=2)
                    dpg.add_radio_button(
                        items=["Single Note", "Chord", "Inversion Drill", "Staff Reading"],
                        default_value="Single Note",
                        tag="mode_radio",
                        callback=self._on_mode_changed,
                        horizontal=True,
                    )

                    # Staff sub-options (visible for staff reading mode)
                    with dpg.group(tag="staff_options_group", show=False):
                        dpg.add_spacer(height=2)
                        with dpg.group(horizontal=True):
                            dpg.add_text("Clef:", color=TEXT_SECONDARY)
                            dpg.add_radio_button(
                                items=["Treble", "Bass"],
                                default_value="Treble",
                                tag="staff_clef_radio",
                                callback=self._on_staff_option_changed,
                                horizontal=True,
                            )
                            dpg.add_spacer(width=16)
                            dpg.add_text("Content:", color=TEXT_SECONDARY)
                            dpg.add_radio_button(
                                items=["Notes", "Chords"],
                                default_value="Notes",
                                tag="staff_content_radio",
                                callback=self._on_staff_option_changed,
                                horizontal=True,
                            )

                    # Chord qualities (visible for chord/inversion/staff-chord modes)
                    with dpg.group(tag="chord_quality_group", show=False):
                        dpg.add_spacer(height=2)
                        dpg.add_text("Chord Qualities:", color=TEXT_SECONDARY)
                        with dpg.group(horizontal=True):
                            dpg.add_checkbox(label="Major", default_value=True, tag="qual_maj",
                                             callback=lambda s, a: self._toggle_quality("maj", a))
                            dpg.add_checkbox(label="Minor", default_value=True, tag="qual_min",
                                             callback=lambda s, a: self._toggle_quality("min", a))
                            dpg.add_checkbox(label="Diminished", default_value=True, tag="qual_dim",
                                             callback=lambda s, a: self._toggle_quality("dim", a))

                    dpg.add_separator()
                    dpg.add_spacer(height=4)

                    # ▸ Session ──────────────────────────────
                    self._section_heading("Session")
                    dpg.add_spacer(height=2)
                    with dpg.group(horizontal=True):
                        dpg.add_text("Questions:", color=TEXT_SECONDARY)
                        dpg.add_input_int(
                            default_value=20, min_value=5, max_value=200,
                            tag="question_count_input", width=100,
                            callback=lambda s, a: setattr(self, "_question_count", a),
                        )

                    dpg.add_spacer(height=16)

                    start_btn = dpg.add_button(
                        label="Start Training",
                        callback=self._on_start_clicked,
                        tag="start_button",
                        width=-1, height=42,
                    )
                    dpg.bind_item_theme(start_btn, "theme_btn_primary")
                    dpg.add_text("", tag="start_error_text", color=RED_ERROR)

                dpg.add_spacer(width=10)

                # ━━ RIGHT COLUMN: Key Selection ━━━━━━━━━━━━━━━
                with dpg.child_window(width=-1, height=COL_HEIGHT, border=True, tag="card_keys"):
                    dpg.bind_item_theme("card_keys", "theme_card")

                    self._section_heading("Key Selection")
                    dpg.add_spacer(height=4)

                    # Presets
                    with dpg.group(horizontal=True):
                        for lbl, cb in [
                            ("C major only", lambda: self._preset_keys(["C"], "major")),
                            ("All Major", lambda: self._preset_all("major")),
                            ("All Minor", lambda: self._preset_all("minor")),
                            ("Clear", self._clear_keys),
                        ]:
                            btn = dpg.add_button(label=lbl, callback=cb)
                            dpg.bind_item_theme(btn, "theme_btn_secondary")

                    dpg.add_spacer(height=8)
                    dpg.add_text("Major:", color=TEXT_SECONDARY)
                    for row_keys in [ALL_MAJOR_KEYS[:7], ALL_MAJOR_KEYS[7:]]:
                        with dpg.group(horizontal=True):
                            for key in row_keys:
                                tag = f"key_{key.root}_{key.mode}"
                                dpg.add_checkbox(
                                    label=key.root,
                                    default_value=(key.root == "C" and key.mode == "major"),
                                    tag=tag,
                                    callback=lambda s, a, k=key: self._toggle_key(k, a),
                                )
                                self._selected_key_checks[f"{key.root}_{key.mode}"] = (key.root == "C" and key.mode == "major")

                    dpg.add_spacer(height=6)
                    dpg.add_text("Minor:", color=TEXT_SECONDARY)
                    for row_keys in [ALL_MINOR_KEYS[:6], ALL_MINOR_KEYS[6:]]:
                        with dpg.group(horizontal=True):
                            for key in row_keys:
                                tag = f"key_{key.root}_{key.mode}"
                                dpg.add_checkbox(
                                    label=key.root,
                                    default_value=False,
                                    tag=tag,
                                    callback=lambda s, a, k=key: self._toggle_key(k, a),
                                )
                                self._selected_key_checks[f"{key.root}_{key.mode}"] = False

    # ── Callbacks ────────────────────────────────────────────────

    def _refresh_ports(self) -> None:
        ports = self.midi.list_input_ports()
        items = ports if ports else ["(No MIDI devices found)"]
        dpg.configure_item("midi_port_combo", items=items)
        if items:
            dpg.set_value("midi_port_combo", items[0])

    def _on_port_selected(self, sender, app_data) -> None:
        self._selected_port = app_data
        if app_data and not app_data.startswith("("):
            try:
                self.midi.open_port(app_data)
                dpg.set_value("midi_status_text", f"Connected")
                dpg.configure_item("midi_status_text", color=GREEN_SUCCESS)
            except Exception as e:
                dpg.set_value("midi_status_text", f"Error: {e}")
                dpg.configure_item("midi_status_text", color=RED_ERROR)

    def _on_mode_changed(self, sender, app_data) -> None:
        if app_data == "Staff Reading":
            self._resolve_staff_mode()
            dpg.configure_item("staff_options_group", show=True)
        else:
            mode_map = {"Single Note": ExerciseMode.NOTE, "Chord": ExerciseMode.CHORD, "Inversion Drill": ExerciseMode.INVERSION}
            self._mode = mode_map.get(app_data, ExerciseMode.NOTE)
            dpg.configure_item("staff_options_group", show=False)

        show_chord = self._mode in (
            ExerciseMode.CHORD, ExerciseMode.INVERSION,
            ExerciseMode.STAFF_CHORD_TREBLE, ExerciseMode.STAFF_CHORD_BASS,
        )
        dpg.configure_item("chord_quality_group", show=show_chord)

    def _on_staff_option_changed(self, sender=None, app_data=None) -> None:
        self._resolve_staff_mode()
        show_chord = self._mode in (ExerciseMode.STAFF_CHORD_TREBLE, ExerciseMode.STAFF_CHORD_BASS)
        dpg.configure_item("chord_quality_group", show=show_chord)

    def _resolve_staff_mode(self) -> None:
        clef = dpg.get_value("staff_clef_radio") if dpg.does_item_exist("staff_clef_radio") else "Treble"
        content = dpg.get_value("staff_content_radio") if dpg.does_item_exist("staff_content_radio") else "Notes"
        if content == "Notes":
            self._mode = ExerciseMode.STAFF_NOTE_TREBLE if clef == "Treble" else ExerciseMode.STAFF_NOTE_BASS
        else:
            self._mode = ExerciseMode.STAFF_CHORD_TREBLE if clef == "Treble" else ExerciseMode.STAFF_CHORD_BASS

    def _toggle_quality(self, quality: str, value: bool) -> None:
        self._chord_quality_checks[quality] = value

    def _toggle_key(self, key: KeySpec, value: bool) -> None:
        self._selected_key_checks[f"{key.root}_{key.mode}"] = value

    def _preset_keys(self, roots: list[str], mode: str) -> None:
        self._clear_keys()
        for root in roots:
            tag = f"key_{root}_{mode}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, True)
                self._selected_key_checks[f"{root}_{mode}"] = True

    def _preset_all(self, mode: str) -> None:
        keys = ALL_MAJOR_KEYS if mode == "major" else ALL_MINOR_KEYS
        for key in keys:
            tag = f"key_{key.root}_{key.mode}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, True)
                self._selected_key_checks[f"{key.root}_{key.mode}"] = True

    def _clear_keys(self) -> None:
        for k in self._selected_key_checks:
            self._selected_key_checks[k] = False
            tag = f"key_{k.replace('_', '_', 1)}"
            # reconstruct tag
            parts = k.split("_", 1)
            tag = f"key_{parts[0]}_{parts[1]}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, False)

    def _get_selected_keys(self) -> list[KeySpec]:
        keys = []
        for k, selected in self._selected_key_checks.items():
            if selected:
                parts = k.split("_", 1)
                keys.append(KeySpec(root=parts[0], mode=parts[1]))
        return keys

    def _on_start_clicked(self) -> None:
        # Validate
        if not self.midi.is_open:
            # Try to connect to selected port first
            port = dpg.get_value("midi_port_combo")
            if port and not port.startswith("("):
                try:
                    self.midi.open_port(port)
                except Exception:
                    dpg.set_value("start_error_text", "Please connect a MIDI device first.")
                    return
            else:
                dpg.set_value("start_error_text", "Please connect a MIDI device first.")
                return

        selected_keys = self._get_selected_keys()
        if not selected_keys:
            dpg.set_value("start_error_text", "Please select at least one key.")
            return

        qualities = {q for q, v in self._chord_quality_checks.items() if v}
        if self._mode in (ExerciseMode.CHORD, ExerciseMode.INVERSION) and not qualities:
            dpg.set_value("start_error_text", "Please select at least one chord quality.")
            return

        question_count = dpg.get_value("question_count_input")

        config = SessionConfig(
            mode=self._mode,
            selected_keys=selected_keys,
            octave_sensitive=self._octave_sensitive,
            chord_qualities=qualities,
            question_count=question_count,
        )

        self.on_start(config)

    # ── Visibility ───────────────────────────────────────────────

    def show(self) -> None:
        if dpg.does_item_exist(self.TAG):
            dpg.configure_item(self.TAG, show=True)
        else:
            self.build()

    def hide(self) -> None:
        if dpg.does_item_exist(self.TAG):
            dpg.configure_item(self.TAG, show=False)
