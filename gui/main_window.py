"""Numi-style notepad window: type on the left, live results on the right."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import (
    QCloseEvent,
    QFont,
    QFontMetrics,
    QGuiApplication,
    QTextOption,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QPlainTextEdit,
    QWidget,
)

from app_logger import AppLogger
from gui.command_edit import CommandEdit
from gui.commands import build_copy_text, last_result_text
from gui.document_evaluator import evaluate_document, format_result, inherited_styles
from gui.font_scale import clamp_font_size, results_width
from gui.font_shortcuts import install_font_shortcuts
from gui.frameless_win import FramelessWindow
from gui.help_window import MarkdownWindow, create_help_window, create_release_notes_window
from gui.highlighter import MathHighlighter
from gui.syntax import CATEGORIES
from gui.window_appearance import Appearance
from gui.window_limits import MAX_OPACITY, MIN_OPACITY, clamp_opacity
from gui.window_prefs import EditorPrefs

_log = AppLogger.get(__name__)


class MainWindow(FramelessWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FastCalculator")
        self.resize(640, 420)
        self._restore_window_chrome()

        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        saved_size = QSettings().value("editor/font_point_size")
        font.setPointSize(clamp_font_size(int(saved_size)) if saved_size is not None else 12)
        self._font = font

        self._help: MarkdownWindow | None = None
        self._notes: MarkdownWindow | None = None

        self._input = CommandEdit()
        self._input.setFont(font)
        self._input.setFrameStyle(0)
        # No wrapping: a wrapped input row has no matching row in the results pane.
        self._input.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._input.command_entered.connect(self._run_command)

        saved_text = str(QSettings().value("document/text", "", type=str))
        if saved_text:
            self._input.setPlainText(saved_text)
            pos = int(str(QSettings().value("document/cursor", 0)))
            cursor = self._input.textCursor()
            cursor.setPosition(min(pos, len(saved_text)))
            self._input.setTextCursor(cursor)

        self._results = QPlainTextEdit()
        self._results.setFont(font)
        self._results.setReadOnly(True)
        self._results.setFrameStyle(0)
        self._results.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._results.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._results.document().setDefaultTextOption(QTextOption(Qt.AlignmentFlag.AlignRight))
        self._result_chars = 0

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._input, 1)
        layout.addWidget(self._results, 0)
        self.setCentralWidget(container)

        self._highlighter = MathHighlighter(self._input.document())
        self._appearance = Appearance(self, self._highlighter)
        self._appearance.restore_colors()
        self._prefs = EditorPrefs(
            self,
            (self._input.document(), self._results.document()),
            self._update_results_width,
            self._recalculate,
        )
        self._prefs.restore_margin()
        self._prefs.restore_round()
        self._update_results_width()

        self._input.textChanged.connect(self._recalculate)

        # ponytail: debounced autosave — one single-shot timer, .start() on each
        # keystroke restarts it, so we only write ~800ms after typing stops.
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(800)
        self._save_timer.timeout.connect(self._save_document)
        self._input.textChanged.connect(self._save_timer.start)

        self._recalculate()  # populate results for restored text
        install_font_shortcuts(self, self._adjust_font)
        self._sync_scrollbars()
        self._restore_geometry()

    def _adjust_font(self, delta: int) -> None:
        size = clamp_font_size(self._font.pointSize() + delta)
        if size == self._font.pointSize():
            return
        self._font.setPointSize(size)
        self._input.setFont(self._font)
        self._results.setFont(self._font)
        self._update_results_width()
        QSettings().setValue("editor/font_point_size", size)

    def _update_results_width(self) -> None:
        # Pane width must track font + margin + content, or results get clipped.
        char_w = QFontMetrics(self._font).horizontalAdvance("0")
        margin = round(self._results.document().documentMargin())
        self._results.setFixedWidth(results_width(char_w, margin, self._result_chars))

    def _recalculate(self) -> None:
        lines = self._input.toPlainText().split("\n")
        results = evaluate_document("\n".join(lines))
        styles = inherited_styles(lines)
        result_lines = [
            format_result(r, line, style, self._prefs.round_decimals)
            for line, r, style in zip(lines, results, styles, strict=False)
        ]
        self._results.setPlainText("\n".join(result_lines))
        widest = max((len(s) for s in result_lines), default=0)
        if widest != self._result_chars:
            self._result_chars = widest
            self._update_results_width()

    def _run_command(self, name: str) -> None:
        _log.info("ran %s", name)
        if name == "/clear":
            self._input.clear()
            return
        if name == "/exit":
            self.close()
            return
        if name == "/help":
            self._help = self._show_markdown(self._help, create_help_window)
            return
        if name == "/release-notes":
            self._notes = self._show_markdown(self._notes, create_release_notes_window)
            return
        if name.startswith("/window-opacity"):
            self._set_opacity(name.partition(" ")[2].strip())
            return
        if name == "/window-title":
            self._toggle_title()
            return
        if name.startswith("/window-background-color"):
            self._appearance.set_color("window/bg_color", name.partition(" ")[2].strip())
            return
        if name.startswith("/window-font-color"):
            self._appearance.set_color("window/font_color", name.partition(" ")[2].strip())
            return
        if name.startswith("/window-theme"):
            self._appearance.set_theme(name.partition(" ")[2].strip())
            return
        if name.startswith("/window-margin"):
            self._prefs.set_margin(name.partition(" ")[2].strip())
            return
        if name.startswith("/round"):
            self._prefs.set_round(name.partition(" ")[2].strip())
            return
        if name.startswith("/window-highlighting"):
            self._appearance.set_highlighting(name.partition(" ")[2].strip())
            return
        for category in CATEGORIES:
            if name.startswith(f"/window-{category}-color"):
                self._appearance.set_syntax_color(category, name.partition(" ")[2].strip())
                return
        # The command line was already removed by the widget, so the document
        # holds only real lines to copy.
        lines = self._input.toPlainText().split("\n")
        results = evaluate_document("\n".join(lines))
        styles = inherited_styles(lines)
        if name == "/paste-last-result":
            self._input.textCursor().insertText(
                last_result_text(lines, results, styles, self._prefs.round_decimals)
            )
            return
        if name == "/copy":
            text = build_copy_text(lines, results, styles, self._prefs.round_decimals)
        else:  # /copy-last
            text = last_result_text(lines, results, styles, self._prefs.round_decimals)
        QGuiApplication.clipboard().setText(text)

    # --- window chrome (opacity, title bar) --------------------------------

    def _restore_window_chrome(self) -> None:
        """Apply persisted opacity and title-bar state on startup. Title bar
        defaults to hidden (frameless)."""
        frameless = bool(QSettings().value("window/frameless", True, type=bool))
        self.set_frameless(frameless, reshow=False)
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

    def _show_markdown(
        self, window: MarkdownWindow | None, factory: Callable[[], MarkdownWindow]
    ) -> MarkdownWindow:
        # Non-modal, single instance: reopening raises the existing window.
        if window is None:
            window = factory()
        window.show()
        window.raise_()
        window.activateWindow()
        return window

    def _toggle_title(self) -> None:
        frameless = not self._frameless
        self.set_frameless(frameless)  # re-shows the window after the change
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

    def _save_document(self) -> None:
        QSettings().setValue("document/text", self._input.toPlainText())
        QSettings().setValue("document/cursor", self._input.textCursor().position())

    def closeEvent(self, event: QCloseEvent) -> None:
        QSettings().setValue("window/geometry", self.saveGeometry())
        self._save_document()
        # Parentless top-level windows must close too, so the app can quit.
        for extra in (self._help, self._notes):
            if extra is not None:
                extra.close()
        super().closeEvent(event)
