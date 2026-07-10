"""Syntax highlighter for the notepad input (the Qt side of `gui/syntax.py`).

`tokenize()` decides the spans; this class owns the category->color palette, the
on/off flag, and their `QSettings` persistence, then paints. Keeping that state
here (rather than in `MainWindow`) keeps the window small and the highlighter
self-contained. Untinted ranges keep the stylesheet foreground.
"""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QTextDocument

from gui.syntax import CATEGORIES, tokenize
from gui.themes import THEMES, syntax_colors

# Falls back to the Dracula accents when nothing is persisted yet.
_DEFAULTS = syntax_colors(THEMES["dracula"])


class MathHighlighter(QSyntaxHighlighter):
    """Colors math tokens per a category->hex map. Disabled -> plain foreground."""

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        self._colors: dict[str, str] = dict(_DEFAULTS)
        self._formats: dict[str, QTextCharFormat] = {}
        self._enabled = True
        self.restore()

    # --- state (also persisted) -------------------------------------------

    def restore(self) -> None:
        """Load palette + on/off flag from `QSettings` and repaint."""
        settings = QSettings()
        self._colors = {
            category: str(settings.value(f"window/syntax_{category}", _DEFAULTS[category]))
            for category in CATEGORIES
        }
        self._enabled = bool(settings.value("window/highlighting", True, type=bool))
        self._rebuild_formats()

    def color(self, category: str) -> str:
        """Current hex for `category` (used to seed the color-picker dialog)."""
        return self._colors[category]

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_category_color(self, category: str, hex_color: str) -> None:
        self._colors[category] = hex_color
        QSettings().setValue(f"window/syntax_{category}", hex_color)
        self._rebuild_formats()

    def apply_theme_colors(self, colors: dict[str, str]) -> None:
        """Replace the whole palette (from a theme) and persist every category."""
        self._colors.update(colors)
        settings = QSettings()
        for category, hex_color in colors.items():
            settings.setValue(f"window/syntax_{category}", hex_color)
        self._rebuild_formats()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        QSettings().setValue("window/highlighting", enabled)
        self.rehighlight()

    # --- painting ----------------------------------------------------------

    def _rebuild_formats(self) -> None:
        self._formats = {}
        for category, hex_color in self._colors.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(hex_color))
            self._formats[category] = fmt
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (Qt override name)
        if not self._enabled:
            return
        for start, length, category in tokenize(text):
            fmt = self._formats.get(category)
            if fmt is not None:
                self.setFormat(start, length, fmt)
