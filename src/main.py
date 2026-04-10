"""MIDI Reaction Trainer — main entry point."""

from __future__ import annotations

import os

import dearpygui.dearpygui as dpg

from .midi_input import MidiInputManager
from .exercise import ExerciseSession, SessionConfig
from .ui.theme import build_themes
from .ui.setup_screen import SetupScreen
from .ui.practice_screen import PracticeScreen
from .ui.results_screen import ResultsScreen


class App:
    """Application controller — manages screen transitions and state."""

    def __init__(self) -> None:
        self.midi = MidiInputManager()
        self.setup_screen: SetupScreen | None = None
        self.practice_screen: PracticeScreen | None = None
        self.results_screen: ResultsScreen | None = None

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="MIDI Reaction Trainer", width=960, height=750)

        # Register fonts — Windows Segoe UI for clean look
        font_path = "C:/Windows/Fonts/segoeui.ttf"
        font_path_bold = "C:/Windows/Fonts/segoeuib.ttf"
        if not os.path.exists(font_path):
            font_path = "C:/Windows/Fonts/arial.ttf"
            font_path_bold = font_path

        with dpg.font_registry():
            self.font_default = dpg.add_font(font_path, 17)
            self.font_heading = dpg.add_font(font_path_bold, 22)
            self.font_large = dpg.add_font(font_path_bold, 60)
            self.font_medium = dpg.add_font(font_path, 30)
            self.font_small = dpg.add_font(font_path, 14)

        dpg.bind_font(self.font_default)

        # Build theme system
        build_themes()
        dpg.bind_theme("theme_global")

        with dpg.window(tag="primary_window"):
            pass

        dpg.set_primary_window("primary_window", True)

        # Create screens
        self.setup_screen = SetupScreen(
            self.midi, on_start=self._on_start_training,
            font_heading=self.font_heading,
        )
        self.practice_screen = PracticeScreen(
            self.midi, on_session_end=self._on_session_end,
            font_large=self.font_large, font_medium=self.font_medium,
            font_heading=self.font_heading,
        )
        self.results_screen = ResultsScreen(
            on_restart=self._on_restart,
            font_heading=self.font_heading, font_medium=self.font_medium,
        )

        # Build and show setup
        self.setup_screen.build()
        self.practice_screen.build()
        self.practice_screen.hide()
        self.results_screen.build()
        self.results_screen.hide()

        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Main render loop
        while dpg.is_dearpygui_running():
            # Tick practice screen (timer updates, auto-advance)
            if self.practice_screen:
                self.practice_screen.update()
            dpg.render_dearpygui_frame()

        # Cleanup
        self.midi.close_port()
        dpg.destroy_context()

    # ── Screen transitions ───────────────────────────────────────

    def _on_start_training(self, config: SessionConfig) -> None:
        """Transition from setup → practice."""
        if self.setup_screen:
            self.setup_screen.hide()
        if self.results_screen:
            self.results_screen.hide()

        if self.practice_screen:
            self.practice_screen.show()
            self.practice_screen.start_session(config)

    def _on_session_end(self, session: ExerciseSession) -> None:
        """Transition from practice → results."""
        if self.practice_screen:
            self.practice_screen.hide()

        if self.results_screen:
            self.results_screen.show()
            self.results_screen.show_results(session)

    def _on_restart(self) -> None:
        """Transition from results → setup."""
        if self.results_screen:
            self.results_screen.hide()
        if self.setup_screen:
            self.setup_screen.show()


def main() -> None:
    app = App()
    app.run()


if __name__ == "__main__":
    main()
