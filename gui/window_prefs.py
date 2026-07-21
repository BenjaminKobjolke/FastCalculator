"""Margin and result-rounding command handlers for the notepad window.

Split out of `MainWindow` (like `window_appearance.Appearance`) so the window
class stays small. Composition: holds the window for dialogs, both pane
documents for the margin, and callbacks to refresh the layout / results.
Persistence lives here; `MainWindow._run_command` just delegates.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QInputDialog, QWidget

from app_logger import AppLogger
from gui.window_limits import (
    DEFAULT_MARGIN,
    MAX_DECIMALS,
    MAX_MARGIN,
    clamp_decimals,
    clamp_margin,
)

_log = AppLogger.get(__name__)


class EditorPrefs:
    """Owns the editor margin (`/window-margin`) and the `/round` decimal cap."""

    def __init__(
        self,
        window: QWidget,
        documents: tuple[QTextDocument, QTextDocument],
        on_margin_change: Callable[[], None],
        on_round_change: Callable[[], None],
    ) -> None:
        self._window = window
        self._documents = documents
        self._on_margin_change = on_margin_change
        self._on_round_change = on_round_change
        self.round_decimals: int | None = None

    # --- editor margin -----------------------------------------------------

    def restore_margin(self) -> None:
        saved = QSettings().value("window/margin")
        self._apply_margin(clamp_margin(int(saved)) if saved is not None else DEFAULT_MARGIN)

    def _apply_margin(self, px: int) -> None:
        for document in self._documents:
            document.setDocumentMargin(px)
        self._on_margin_change()

    def set_margin(self, arg: str) -> None:
        if not arg:
            current = round(self._documents[0].documentMargin())
            value, ok = QInputDialog.getInt(
                self._window, "Editor margin", "Margin (px):", current, 0, MAX_MARGIN
            )
            if not ok:
                return
            arg = str(value)
        if not arg.isdigit():
            _log.info("ignored /window-margin with non-numeric arg %r", arg)
            return
        px = clamp_margin(int(arg))
        self._apply_margin(px)
        QSettings().setValue("window/margin", px)

    # --- result rounding (/round) ------------------------------------------

    def restore_round(self) -> None:
        saved = QSettings().value("window/round_decimals")
        self.round_decimals = clamp_decimals(int(saved)) if saved is not None else None

    def set_round(self, arg: str) -> None:
        if arg.lower() == "off":
            self.round_decimals = None
            QSettings().remove("window/round_decimals")
            self._on_round_change()
            return
        if not arg:
            current = self.round_decimals if self.round_decimals is not None else 2
            value, ok = QInputDialog.getInt(
                self._window, "Round results", "Max decimals:", current, 0, MAX_DECIMALS
            )
            if not ok:
                return
            arg = str(value)
        if not arg.isdigit():
            _log.info("ignored /round with non-numeric arg %r", arg)
            return
        self.round_decimals = clamp_decimals(int(arg))
        QSettings().setValue("window/round_decimals", self.round_decimals)
        self._on_round_change()
