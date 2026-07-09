"""Numi-style notepad window: type on the left, live results on the right."""

from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import (
    QCloseEvent,
    QFont,
    QGuiApplication,
    QKeySequence,
    QShortcut,
    QTextOption,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QPlainTextEdit,
    QWidget,
)

from app_logger import AppLogger
from gui.command_edit import CommandEdit
from gui.commands import build_copy_text, last_result_text
from gui.document_evaluator import evaluate_document, format_result
from gui.font_scale import clamp_font_size
from gui.themes import THEMES, is_valid_hex, theme_names

_log = AppLogger.get(__name__)

MIN_OPACITY = 10  # never 0: a fully invisible frameless window is unrecoverable
MAX_OPACITY = 100

DEFAULT_MARGIN = 8
MAX_MARGIN = 200


def clamp_opacity(percent: int) -> int:
    """Keep window opacity within a visible, recoverable range (percent)."""
    return max(MIN_OPACITY, min(MAX_OPACITY, percent))


def clamp_margin(px: int) -> int:
    """Keep the editor margin within sane pixel bounds."""
    return max(0, min(MAX_MARGIN, px))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Calculator")
        self.resize(640, 420)
        self._restore_window_chrome()

        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        saved_size = QSettings().value("editor/font_point_size")
        font.setPointSize(clamp_font_size(int(saved_size)) if saved_size is not None else 12)
        self._font = font

        self._input = CommandEdit()
        self._input.setFont(font)
        self._input.setFrameStyle(0)
        self._input.command_entered.connect(self._run_command)

        self._results = QPlainTextEdit()
        self._results.setFont(font)
        self._results.setReadOnly(True)
        self._results.setFrameStyle(0)
        self._results.setFixedWidth(180)
        self._results.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._results.document().setDefaultTextOption(QTextOption(Qt.AlignmentFlag.AlignRight))

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._input, 1)
        layout.addWidget(self._results, 0)
        self.setCentralWidget(container)

        self._bg: str | None = None
        self._fg: str | None = None
        self._restore_colors()
        self._restore_margin()

        self._input.textChanged.connect(self._recalculate)
        self._install_font_shortcuts()
        self._sync_scrollbars()
        self._restore_geometry()

    def _install_font_shortcuts(self) -> None:
        # Ctrl++ / Ctrl+= (same physical key with/without shift) and Alt+Up grow;
        # Ctrl+- and Alt+Down shrink.
        for seq in ("Ctrl++", "Ctrl+=", "Alt+Up"):
            QShortcut(QKeySequence(seq), self).activated.connect(lambda: self._adjust_font(1))
        for seq in ("Ctrl+-", "Alt+Down"):
            QShortcut(QKeySequence(seq), self).activated.connect(lambda: self._adjust_font(-1))

    def _adjust_font(self, delta: int) -> None:
        size = clamp_font_size(self._font.pointSize() + delta)
        if size == self._font.pointSize():
            return
        self._font.setPointSize(size)
        self._input.setFont(self._font)
        self._results.setFont(self._font)
        QSettings().setValue("editor/font_point_size", size)

    def _recalculate(self) -> None:
        lines = self._input.toPlainText().split("\n")
        results = evaluate_document("\n".join(lines))
        self._results.setPlainText(
            "\n".join(format_result(r, line) for line, r in zip(lines, results, strict=False))
        )

    def _run_command(self, name: str) -> None:
        _log.info("ran %s", name)
        if name == "/clear":
            self._input.clear()
            return
        if name == "/exit":
            self.close()
            return
        if name.startswith("/window-opacity"):
            self._set_opacity(name.partition(" ")[2].strip())
            return
        if name == "/window-title":
            self._toggle_title()
            return
        if name.startswith("/window-background-color"):
            self._set_color("window/bg_color", name.partition(" ")[2].strip())
            return
        if name.startswith("/window-font-color"):
            self._set_color("window/font_color", name.partition(" ")[2].strip())
            return
        if name.startswith("/window-theme"):
            self._set_theme(name.partition(" ")[2].strip())
            return
        if name.startswith("/window-margin"):
            self._set_margin(name.partition(" ")[2].strip())
            return
        # The command line was already removed by the widget, so the document
        # holds only real lines to copy.
        lines = self._input.toPlainText().split("\n")
        results = evaluate_document("\n".join(lines))
        if name == "/paste-last-result":
            self._input.textCursor().insertText(last_result_text(results))
            return
        if name == "/copy":
            text = build_copy_text(lines, results)
        else:  # /copy-last
            text = last_result_text(results)
        QGuiApplication.clipboard().setText(text)

    # --- window chrome (opacity, title bar) --------------------------------

    def _restore_window_chrome(self) -> None:
        """Apply persisted opacity and title-bar state on startup. Title bar
        defaults to hidden (frameless)."""
        frameless = bool(QSettings().value("window/frameless", True, type=bool))
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, frameless)
        saved = QSettings().value("window/opacity")
        if saved is not None:
            self.setWindowOpacity(clamp_opacity(int(saved)) / 100)

    def _set_opacity(self, arg: str) -> None:
        if not arg:
            current = round(self.windowOpacity() * 100)
            value, ok = QInputDialog.getInt(
                self, "Window opacity", "Opacity %:", current, MIN_OPACITY, MAX_OPACITY
            )
            if not ok:
                return
            arg = str(value)
        if not arg.isdigit():
            _log.info("ignored /window-opacity with non-numeric arg %r", arg)
            return
        percent = clamp_opacity(int(arg))
        self.setWindowOpacity(percent / 100)
        QSettings().setValue("window/opacity", percent)

    # --- colors and themes -------------------------------------------------

    def _restore_colors(self) -> None:
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
        self.setStyleSheet(f"QPlainTextEdit {{ {' '.join(parts)} }}" if parts else "")

    def _set_color(self, key: str, arg: str) -> None:
        if not arg:
            current = (self._bg if key == "window/bg_color" else self._fg) or ""
            arg, ok = QInputDialog.getText(
                self, "Color", "Hex color (e.g. #282a36):", text=current
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

    def _set_theme(self, arg: str) -> None:
        if not arg:
            arg, ok = QInputDialog.getItem(
                self, "Theme", "Choose a theme:", theme_names(), 0, False
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

    # --- editor margin -----------------------------------------------------

    def _restore_margin(self) -> None:
        saved = QSettings().value("window/margin")
        self._apply_margin(clamp_margin(int(saved)) if saved is not None else DEFAULT_MARGIN)

    def _apply_margin(self, px: int) -> None:
        self._input.document().setDocumentMargin(px)
        self._results.document().setDocumentMargin(px)

    def _set_margin(self, arg: str) -> None:
        if not arg:
            current = round(self._input.document().documentMargin())
            value, ok = QInputDialog.getInt(
                self, "Editor margin", "Margin (px):", current, 0, MAX_MARGIN
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

    def _toggle_title(self) -> None:
        frameless = not bool(self.windowFlags() & Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, frameless)
        self.show()  # Qt hides the window when its flags change; re-show it.
        QSettings().setValue("window/frameless", frameless)

    def _sync_scrollbars(self) -> None:
        # keep both panes aligned row-for-row while scrolling
        src = self._input.verticalScrollBar()
        dst = self._results.verticalScrollBar()
        src.valueChanged.connect(dst.setValue)

    def _restore_geometry(self) -> None:
        saved = QSettings().value("window/geometry")
        if saved is not None:
            self.restoreGeometry(saved)
        self._ensure_on_screen()

    def _ensure_on_screen(self) -> None:
        # A saved position can land off every screen (monitor unplugged, resized).
        # If the window center isn't on any available screen, center on primary.
        center = self.frameGeometry().center()
        if any(s.availableGeometry().contains(center) for s in QGuiApplication.screens()):
            return
        primary = QGuiApplication.primaryScreen()
        if primary is not None:
            frame = self.frameGeometry()
            frame.moveCenter(primary.availableGeometry().center())
            self.move(frame.topLeft())

    def closeEvent(self, event: QCloseEvent) -> None:
        QSettings().setValue("window/geometry", self.saveGeometry())
        super().closeEvent(event)
