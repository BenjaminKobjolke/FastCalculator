"""Shared font-size shortcut wiring for top-level widgets."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QWidget


def install_font_shortcuts(widget: QWidget, adjust: Callable[[int], None]) -> None:
    """Install the common grow/shrink font shortcuts on `widget`."""
    for seq in ("Ctrl++", "Ctrl+=", "Alt+Up"):
        QShortcut(QKeySequence(seq), widget).activated.connect(lambda: adjust(1))
    for seq in ("Ctrl+-", "Alt+Down"):
        QShortcut(QKeySequence(seq), widget).activated.connect(lambda: adjust(-1))
