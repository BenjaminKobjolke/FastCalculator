"""Help window: renders the localized help markdown in a QTextBrowser.

A plain top-level QWidget — NOT a QDialog. On Windows a dialog uses a dialog
frame (no maximize box) and is excluded from Aero Snap / Win+Arrow; a normal
QWidget window gets the standard frame and snaps like any other window. It is
shown non-modally so the notepad stays usable while help is open.

Mirrors the main window's look and feel — same monospace font + saved size,
themed background/foreground, opacity and margin — and the same font-size
shortcuts (Ctrl++/Ctrl+-/Alt+Up/Alt+Down). The text is selectable and shows a
caret (keyboard-navigable), so it feels like the notepad. Esc closes it.

"""

from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from gui.font_scale import clamp_font_size
from gui.font_shortcuts import install_font_shortcuts
from gui.help_content import build_help_markdown
from gui.i18n import t
from gui.i18n_keys import TK


class HelpWindow(QWidget):
    """Resizable top-level help window that tracks the notepad's appearance."""

    def __init__(self) -> None:
        super().__init__()  # parentless: a fully independent, snappable window
        self.setWindowTitle(t(TK.HELP_TITLE))
        self.resize(560, 640)

        self._browser = QTextBrowser(self)
        self._browser.setOpenExternalLinks(True)
        # Caret + selection like the notepad: TextSelectableByKeyboard gives a
        # navigable blinking cursor; the mouse flags keep click-select and links.
        self._browser.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByKeyboard
        )

        self._font = self._build_font()
        self._render()
        self._apply_appearance()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._browser)

        self._install_shortcuts()

    def _build_font(self) -> QFont:
        # Same Consolas/monospace and shared size key as the notepad.
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        saved = QSettings().value("editor/font_point_size")
        font.setPointSize(clamp_font_size(int(saved)) if saved is not None else 12)
        return font

    def _render(self) -> None:
        # Qt renders markdown `code`/```blocks``` at a fixed, smaller size that
        # ignores the widget font. Pin code to the current point size via the
        # document's default stylesheet (must be set before setMarkdown) so it
        # scales with the body when the font changes.
        self._browser.setFont(self._font)
        pt = self._font.pointSize()
        self._browser.document().setDefaultStyleSheet(
            f"code, pre {{ font-family: Consolas; font-size: {pt}pt; }}"
        )
        self._browser.setMarkdown(build_help_markdown())

    def _apply_appearance(self) -> None:
        # Reuse the notepad's persisted appearance (same QSettings keys as
        # Appearance / MainWindow), so help matches the current theme.
        settings = QSettings()
        bg = settings.value("window/bg_color")
        fg = settings.value("window/font_color")
        # The browser fills the window (zero layout margins), so styling it alone
        # covers all visible area.
        parts = []
        if bg:
            parts.append(f"background-color:{bg};")
        if fg:
            parts.append(f"color:{fg};")
        self._browser.setStyleSheet(f"QTextBrowser {{ {' '.join(parts)} }}" if parts else "")

        margin = settings.value("window/margin")
        if margin is not None:
            self._browser.document().setDocumentMargin(int(margin))

        opacity = settings.value("window/opacity")
        if opacity is not None:
            self.setWindowOpacity(int(opacity) / 100)

    def _install_shortcuts(self) -> None:
        # QWidget has no built-in Esc-to-close (QDialog did), so wire it.
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self).activated.connect(self.close)
        install_font_shortcuts(self, self._adjust_font)

    def _adjust_font(self, delta: int) -> None:
        size = clamp_font_size(self._font.pointSize() + delta)
        if size == self._font.pointSize():
            return
        self._font.setPointSize(size)
        self._render()  # re-render so code spans rescale with the body
        QSettings().setValue("editor/font_point_size", size)
