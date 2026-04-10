"""Results screen: session summary, per-item breakdown, history."""

from __future__ import annotations
from typing import Callable, Optional

import dearpygui.dearpygui as dpg

from ..exercise import ExerciseSession
from ..scoring import compute_session_stats, SessionStats
from ..history import save_session, load_session_list
from .theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT_BLUE, CYAN_HIGHLIGHT, GREEN_SUCCESS, ORANGE_SLOW, YELLOW_WARN,
)


class ResultsScreen:
    """Renders the end-of-session results screen."""

    TAG = "results_screen"

    def __init__(
        self,
        on_restart: Callable[[], None],
        font_heading: int = 0,
        font_medium: int = 0,
    ) -> None:
        self.on_restart = on_restart
        self.font_heading = font_heading
        self.font_medium = font_medium
        self._stats: Optional[SessionStats] = None

    def _section_heading(self, label: str, color=CYAN_HIGHLIGHT) -> None:
        t = dpg.add_text(label, color=color)
        if self.font_heading:
            dpg.bind_item_font(t, self.font_heading)

    # ── Build UI ─────────────────────────────────────────────────

    def build(self) -> None:
        if dpg.does_item_exist(self.TAG):
            dpg.delete_item(self.TAG)

        with dpg.group(tag=self.TAG, parent="primary_window"):

            # ── Title ────────────────────────────────────────────
            dpg.add_spacer(height=4)
            title = dpg.add_text("Session Complete", color=GREEN_SUCCESS)
            if self.font_heading:
                dpg.bind_item_font(title, self.font_heading)
            dpg.add_spacer(height=6)

            # ── Summary stats card ───────────────────────────────
            with dpg.child_window(height=110, border=True, tag="card_summary"):
                dpg.bind_item_theme("card_summary", "theme_card_accent")
                with dpg.group(horizontal=True):
                    # Left column — big accuracy
                    with dpg.group():
                        dpg.add_text("Accuracy", color=TEXT_MUTED)
                        acc_id = dpg.add_text("--", tag="res_accuracy_big", color=GREEN_SUCCESS)
                        if self.font_medium:
                            dpg.bind_item_font(acc_id, self.font_medium)
                        dpg.add_text("", tag="res_accuracy_detail", color=TEXT_SECONDARY)

                    dpg.add_spacer(width=50)

                    # Middle column — time stats
                    with dpg.group():
                        dpg.add_text("Reaction Time", color=TEXT_MUTED)
                        avg_id = dpg.add_text("--", tag="res_avg_time", color=ACCENT_BLUE)
                        if self.font_medium:
                            dpg.bind_item_font(avg_id, self.font_medium)
                        dpg.add_text("", tag="res_time_detail", color=TEXT_SECONDARY)

                    dpg.add_spacer(width=50)

                    # Right column — streak + total
                    with dpg.group():
                        dpg.add_text("Session", color=TEXT_MUTED)
                        streak_id = dpg.add_text("--", tag="res_streak", color=YELLOW_WARN)
                        if self.font_medium:
                            dpg.bind_item_font(streak_id, self.font_medium)
                        dpg.add_text("", tag="res_session_detail", color=TEXT_SECONDARY)

            dpg.add_spacer(height=6)

            # ── Two-column: per-item + slowest ───────────────────
            with dpg.group(horizontal=True):
                # Per-item breakdown
                with dpg.child_window(width=680, height=280, border=True, tag="card_per_item"):
                    dpg.bind_item_theme("card_per_item", "theme_card")
                    self._section_heading("Per-Item Breakdown")
                    dpg.add_spacer(height=4)
                    with dpg.group(tag="per_item_group"):
                        pass

                dpg.add_spacer(width=10)

                # Slowest items
                with dpg.child_window(width=-1, height=280, border=True, tag="card_slowest"):
                    dpg.bind_item_theme("card_slowest", "theme_card")
                    self._section_heading("Slowest Items", color=ORANGE_SLOW)
                    dpg.add_spacer(height=4)
                    with dpg.group(tag="slowest_items_group"):
                        pass

            dpg.add_spacer(height=6)

            # ── History card ─────────────────────────────────────
            with dpg.child_window(height=120, border=True, tag="card_history"):
                dpg.bind_item_theme("card_history", "theme_card")
                self._section_heading("Recent Sessions")
                dpg.add_spacer(height=4)
                with dpg.group(tag="history_group"):
                    pass

            dpg.add_spacer(height=6)

            # ── Action button ────────────────────────────────────
            btn = dpg.add_button(
                label="New Session", callback=self._on_restart,
                width=200, height=38,
            )
            dpg.bind_item_theme(btn, "theme_btn_primary")

    # ── Populate ─────────────────────────────────────────────────

    def show_results(self, session: ExerciseSession) -> None:
        """Compute stats, save history, and display results."""
        stats = compute_session_stats(session.attempts, session.best_streak)
        self._stats = stats

        # Save to disk
        try:
            save_session(session.config, session.attempts, session.best_streak)
        except Exception:
            pass

        # ── Summary cards ────────────────────────────────────────
        dpg.set_value("res_accuracy_big", f"{stats.accuracy_pct:.0f}%")
        dpg.set_value("res_accuracy_detail", f"{stats.correct_attempts} / {stats.total_attempts} correct")

        dpg.set_value("res_avg_time", f"{self._fmt_ms(stats.avg_reaction_ms)}")
        fast = self._fmt_ms(stats.fastest_ms)
        slow = self._fmt_ms(stats.slowest_ms)
        med = self._fmt_ms(stats.median_reaction_ms)
        dpg.set_value("res_time_detail", f"Median {med}  |  {fast} - {slow}")

        dpg.set_value("res_streak", f"{stats.best_streak} streak")
        dpg.set_value("res_session_detail", f"{stats.total_attempts} questions")

        # Color accuracy based on score
        if stats.accuracy_pct >= 90:
            dpg.configure_item("res_accuracy_big", color=GREEN_SUCCESS)
        elif stats.accuracy_pct >= 70:
            dpg.configure_item("res_accuracy_big", color=YELLOW_WARN)
        else:
            dpg.configure_item("res_accuracy_big", color=ORANGE_SLOW)

        # ── Per-item table ───────────────────────────────────────
        self._clear_group("per_item_group")
        # Header
        with dpg.group(horizontal=True, parent="per_item_group"):
            dpg.add_text(f"{'Item':<18s} {'Score':>7s} {'Avg Time':>10s} {'Errors':>7s}", color=TEXT_MUTED)

        for label, item in sorted(stats.per_item.items(), key=lambda x: x[1].avg_reaction_ms or 999999):
            acc = f"{item.correct}/{item.attempts}"
            time_str = self._fmt_ms(item.avg_reaction_ms)
            row_color = TEXT_PRIMARY if item.correct == item.attempts else TEXT_SECONDARY
            with dpg.group(horizontal=True, parent="per_item_group"):
                dpg.add_text(f"{label:<18s} {acc:>7s} {time_str:>10s} {item.errors:>7d}", color=row_color)

        # ── Slowest items ────────────────────────────────────────
        self._clear_group("slowest_items_group")
        slowest = sorted(
            [i for i in stats.per_item.values() if i.avg_reaction_ms is not None],
            key=lambda x: x.avg_reaction_ms or 0,
            reverse=True,
        )[:5]
        for rank, item in enumerate(slowest, 1):
            with dpg.group(horizontal=True, parent="slowest_items_group"):
                dpg.add_text(f"{rank}.", color=TEXT_MUTED)
                dpg.add_text(f"{item.label}", color=ORANGE_SLOW)
                dpg.add_spacer(width=10)
                dpg.add_text(f"{self._fmt_ms(item.avg_reaction_ms)}", color=TEXT_SECONDARY)

        # ── History ──────────────────────────────────────────────
        self._clear_group("history_group")
        try:
            sessions = load_session_list()[:8]
            for s in sessions:
                ts = s.get("timestamp", "")[:19].replace("T", " ")
                mode = s.get("mode", "")
                acc = s.get("accuracy_pct", 0)
                avg = s.get("avg_reaction_ms")
                avg_str = f"{avg:.0f}ms" if avg else "--"
                with dpg.group(horizontal=True, parent="history_group"):
                    dpg.add_text(ts, color=TEXT_MUTED)
                    dpg.add_spacer(width=10)
                    dpg.add_text(f"{mode}", color=TEXT_SECONDARY)
                    dpg.add_spacer(width=10)
                    dpg.add_text(f"{acc:.0f}%", color=TEXT_PRIMARY)
                    dpg.add_spacer(width=10)
                    dpg.add_text(f"avg {avg_str}", color=TEXT_SECONDARY)
        except Exception:
            dpg.add_text("(Could not load history)", parent="history_group", color=TEXT_MUTED)

    @staticmethod
    def _fmt_ms(ms: Optional[float]) -> str:
        if ms is None:
            return "--"
        if ms < 1000:
            return f"{ms:.0f}ms"
        return f"{ms / 1000:.2f}s"

    @staticmethod
    def _clear_group(tag: str) -> None:
        if dpg.does_item_exist(tag):
            children = dpg.get_item_children(tag, 1)
            if children:
                for child in children:
                    dpg.delete_item(child)

    def _on_restart(self) -> None:
        self.on_restart()

    # ── Visibility ───────────────────────────────────────────────

    def show(self) -> None:
        if dpg.does_item_exist(self.TAG):
            dpg.configure_item(self.TAG, show=True)
        else:
            self.build()

    def hide(self) -> None:
        if dpg.does_item_exist(self.TAG):
            dpg.configure_item(self.TAG, show=False)
