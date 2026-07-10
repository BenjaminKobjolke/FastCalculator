"""Color / theme / syntax-color command handlers for the notepad window.

Split out of `MainWindow` so the window class stays small and this visual
concern is cohesive. Composition, not a mixin: it holds the window it styles and
the highlighter it recolors, so it only needs `QWidget.setStyleSheet` from the
window (no multiple-inheritance typing). Persistence lives here and in the
highlighter; `MainWindow._run_command` just delegates.
"""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QInputDialog, QWidget

from app_logger import AppLogger
from gui.highlighter import MathHighlighter
from gui.themes import THEMES, is_valid_hex, syntax_colors, theme_names

_log = AppLogger.get(__name__)


class Appearance:
    """Owns pane background/foreground and drives the syntax highlighter."""

    def __init__(self, window: QWidget, highlighter: MathHighlighter) -> None:
        self._window = window
        self._highlighter = highlighter
        self._bg: str | None = None
        self._fg: str | None = None

    # --- background / foreground -------------------------------------------

    def restore_colors(self) -> None:
        self._bg = QSettings().value("window/bg_color")
        self._fg = QSettings().value("window/font_color")
        self._apply_colors()

    def _apply_colors(self) -> None:
        # One rule on the window cascades to both QPlainTextEdit panes; the
        # layout has no gaps, so this covers all visible area.
        # ponytail: ghost-completion text keeps the default placeholderText
        # color (stylesheets don't retint it). Also set the PlaceholderText
        # palette role if it reads poorly on a dark theme.
        parts = []
        if self._bg:
            parts.append(f"background-color:{self._bg};")
        if self._fg:
            parts.append(f"color:{self._fg};")
        self._window.setStyleSheet(f"QPlainTextEdit {{ {' '.join(parts)} }}" if parts else "")

    def set_color(self, key: str, arg: str) -> None:
        if not arg:
            current = (self._bg if key == "window/bg_color" else self._fg) or ""
            arg, ok = QInputDialog.getText(
                self._window, "Color", "Hex color (e.g. #282a36):", text=current
            )
            if not ok:
                return
        arg = arg.strip()
        if not is_valid_hex(arg):
            _log.info("ignored %s with invalid hex %r", key, arg)
            return
        if key == "window/bg_color":
            self._bg = arg
        else:
            self._fg = arg
        self._apply_colors()
        QSettings().setValue(key, arg)

    def set_theme(self, arg: str) -> None:
        if not arg:
            arg, ok = QInputDialog.getItem(
                self._window, "Theme", "Choose a theme:", theme_names(), 0, False
            )
            if not ok:
                return
        theme = THEMES.get(arg.strip())
        if theme is None:
            _log.info("ignored /window-theme with unknown name %r", arg)
            return
        self._bg, self._fg = theme.background, theme.foreground
        self._apply_colors()
        QSettings().setValue("window/bg_color", self._bg)
        QSettings().setValue("window/font_color", self._fg)
        self._highlighter.apply_theme_colors(syntax_colors(theme))

    # --- syntax colors -----------------------------------------------------

    def set_syntax_color(self, category: str, arg: str) -> None:
        if not arg:
            arg, ok = QInputDialog.getText(
                self._window,
                "Syntax color",
                f"Hex color for {category}:",
                text=self._highlighter.color(category),
            )
            if not ok:
                return
        arg = arg.strip()
        if not is_valid_hex(arg):
            _log.info("ignored /window-%s-color with invalid hex %r", category, arg)
            return
        self._highlighter.set_category_color(category, arg)

    def set_highlighting(self, arg: str) -> None:
        arg = arg.strip().lower()
        if arg == "on":
            enabled = True
        elif arg == "off":
            enabled = False
        else:  # empty or unrecognized: toggle, like /window-title
            enabled = not self._highlighter.enabled
        self._highlighter.set_enabled(enabled)
