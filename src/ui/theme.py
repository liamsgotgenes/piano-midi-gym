"""Centralized theme and color definitions for the UI."""

from __future__ import annotations

import dearpygui.dearpygui as dpg

# ── Color palette ────────────────────────────────────────────────────

BG_DARK       = (22, 22, 30)
BG_CARD       = (30, 32, 42)
BG_CARD_HOVER = (38, 40, 52)
BORDER_SUBTLE = (50, 54, 68)
BORDER_ACCENT = (88, 101, 242)

TEXT_PRIMARY   = (230, 232, 240)
TEXT_SECONDARY = (150, 155, 175)
TEXT_MUTED     = (100, 105, 125)

ACCENT_BLUE    = (88, 101, 242)
ACCENT_BLUE_HI = (110, 125, 255)
ACCENT_BLUE_LO = (68, 78, 200)

GREEN_SUCCESS    = (80, 220, 120)
GREEN_SUCCESS_BG = (30, 60, 40)
RED_ERROR        = (240, 80, 80)
RED_ERROR_BG     = (60, 30, 30)
YELLOW_WARN      = (255, 200, 60)
ORANGE_SLOW      = (240, 160, 60)

CYAN_HIGHLIGHT = (80, 200, 220)
PURPLE_ACCENT  = (160, 120, 240)

# ── Reusable tag-based themes ────────────────────────────────────────

_built = False


def build_themes() -> None:
    """Create all reusable Dear PyGui themes. Call once after dpg.create_context()."""
    global _built
    if _built:
        return
    _built = True

    # ── Global theme ────────────────────────────────────────────
    with dpg.theme(tag="theme_global"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 8)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 16)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)

            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BG_DARK)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, BG_CARD)
            dpg.add_theme_color(dpg.mvThemeCol_Border, BORDER_SUBTLE)
            dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT_PRIMARY)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, TEXT_MUTED)

            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (40, 43, 56))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (50, 54, 70))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (55, 60, 78))

            dpg.add_theme_color(dpg.mvThemeCol_Button, ACCENT_BLUE)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, ACCENT_BLUE_HI)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, ACCENT_BLUE_LO)

            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, ACCENT_BLUE)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, ACCENT_BLUE)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, ACCENT_BLUE_HI)

            dpg.add_theme_color(dpg.mvThemeCol_Header, (45, 48, 62))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (55, 58, 72))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (65, 68, 82))

            dpg.add_theme_color(dpg.mvThemeCol_Separator, BORDER_SUBTLE)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (26, 28, 38))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (55, 58, 72))

            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (35, 38, 50))

    # ── Primary action button ───────────────────────────────────
    with dpg.theme(tag="theme_btn_primary"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, ACCENT_BLUE)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, ACCENT_BLUE_HI)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, ACCENT_BLUE_LO)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 20, 10)

    # ── Secondary / outline button ──────────────────────────────
    with dpg.theme(tag="theme_btn_secondary"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (45, 48, 62))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 64, 80))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (50, 54, 68))
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 14, 6)

    # ── Danger / quit button ────────────────────────────────────
    with dpg.theme(tag="theme_btn_danger"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (140, 40, 40))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (180, 55, 55))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (120, 30, 30))
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)

    # ── Card container ──────────────────────────────────────────
    with dpg.theme(tag="theme_card"):
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, BG_CARD)
            dpg.add_theme_color(dpg.mvThemeCol_Border, BORDER_SUBTLE)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 16, 12)

    # ── Accent card (highlighted section) ───────────────────────
    with dpg.theme(tag="theme_card_accent"):
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (30, 35, 55))
            dpg.add_theme_color(dpg.mvThemeCol_Border, ACCENT_BLUE)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 16, 12)

    # ── Success card ────────────────────────────────────────────
    with dpg.theme(tag="theme_card_success"):
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, GREEN_SUCCESS_BG)
            dpg.add_theme_color(dpg.mvThemeCol_Border, GREEN_SUCCESS)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 16, 12)

    # ── Progress bar ────────────────────────────────────────────
    with dpg.theme(tag="theme_progress"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, ACCENT_BLUE)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (40, 43, 56))
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
