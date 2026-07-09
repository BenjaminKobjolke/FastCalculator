"""Numi-style notepad window: type on the left, live results on the right."""

from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QCloseEvent, QFont, QGuiApplication, QTextOption
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPlainTextEdit,
    QWidget,
)

from app_logger import AppLogger
from gui.command_edit import CommandEdit
from gui.commands import build_copy_text, last_result_text
from gui.document_evaluator import evaluate_document, format_result

_log = AppLogger.get(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Calculator")
        self.resize(640, 420)

        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(12)

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

        self._input.textChanged.connect(self._recalculate)
        self._sync_scrollbars()
        self._restore_geometry()

    def _recalculate(self) -> None:
        results = evaluate_document(self._input.toPlainText())
        self._results.setPlainText("\n".join(format_result(r) for r in results))

    def _run_command(self, name: str) -> None:
        _log.info("ran %s", name)
        if name == "/clear":
            self._input.clear()
            return
        # The command line was already removed by the widget, so the document
        # holds only real lines to copy.
        lines = self._input.toPlainText().split("\n")
        results = evaluate_document("\n".join(lines))
        if name == "/copy":
            text = build_copy_text(lines, results)
        else:  # /copy-last
            text = last_result_text(results)
        QGuiApplication.clipboard().setText(text)

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
