"""Notepad input with inline ghost-text slash-command autosuggest.

Type `/c` and a grayed completion (`/clear`) is painted after the cursor.
Tab/Enter accepts, Up/Down cycles matches, Esc dismisses. Pressing Enter on a
full command line runs it (via the `command_entered` signal) instead of adding a
newline.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QPainter, QPaintEvent, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

from gui.commands import command_at, parse_command, parse_command_line, suggest


class CommandEdit(QPlainTextEdit):
    """QPlainTextEdit that recognises `/`-prefixed editor commands."""

    command_entered = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._ghost_matches: list[str] = []
        self._ghost_index = 0
        self.textChanged.connect(self._refresh_ghost)
        self.cursorPositionChanged.connect(self._refresh_ghost)

    # --- ghost state -------------------------------------------------------

    def _current_prefix(self) -> str | None:
        """The `/`-command token at the cursor, if the cursor sits at the line
        end; else None. The token may start anywhere in the line (`105+ /pas`),
        not just at column 0. None while a selection exists or mid-line."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            return None
        block_text = cursor.block().text()
        col = cursor.positionInBlock()
        if col != len(block_text):
            return None
        return command_at(block_text, col)

    def _refresh_ghost(self) -> None:
        prefix = self._current_prefix()
        matches = suggest(prefix) if prefix is not None else []
        if matches != self._ghost_matches:
            self._ghost_matches = matches
            self._ghost_index = 0
            self.viewport().update()

    def _ghost_suffix(self) -> str:
        """The grayed remainder shown after the cursor, or ""."""
        if not self._ghost_matches:
            return ""
        prefix = self._current_prefix() or ""
        return self._ghost_matches[self._ghost_index][len(prefix):]

    def _clear_ghost(self) -> None:
        if self._ghost_matches:
            self._ghost_matches = []
            self._ghost_index = 0
            self.viewport().update()

    def _accept_ghost(self) -> None:
        suffix = self._ghost_suffix()
        if suffix:
            self.textCursor().insertText(suffix)  # fires textChanged -> refresh
        self._clear_ghost()

    # --- painting ----------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        suffix = self._ghost_suffix()
        if not suffix:
            return
        painter = QPainter(self.viewport())
        painter.setFont(self.font())
        painter.setPen(self.palette().placeholderText().color())
        # cursorRect() is already in viewport coords; drawText's point is the
        # baseline, so offset the line top by the font ascent.
        rect = self.cursorRect()
        baseline = rect.top() + self.fontMetrics().ascent()
        painter.drawText(rect.left(), baseline, suffix)
        painter.end()

    # --- keys --------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        has_ghost = bool(self._ghost_matches)

        if has_ghost and key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            step = -1 if key == Qt.Key.Key_Up else 1
            self._ghost_index = (self._ghost_index + step) % len(self._ghost_matches)
            self.viewport().update()
            return

        if has_ghost and key == Qt.Key.Key_Escape:
            self._clear_ghost()
            return

        if has_ghost and key == Qt.Key.Key_Tab:
            self._accept_ghost()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if has_ghost:
                self._accept_ghost()
            cursor = self.textCursor()
            token = command_at(cursor.block().text(), cursor.positionInBlock())
            name = parse_command(token) if token is not None else None
            if name is not None:
                self._run_current_line(name)
                return
            # Argument-carrying whole-line command (`/window-opacity 80`): the
            # trailing arg means no `/`-token sits at the cursor, so the token
            # path above misses it.
            parsed = parse_command_line(cursor.block().text())
            if parsed is not None:
                self._run_command_line(*parsed)
                return
            super().keyPressEvent(event)
            return

        super().keyPressEvent(event)

    def _run_current_line(self, name: str) -> None:
        """Delete just the `/command` token before the cursor, then emit so the
        window can act. Removing only the token (not the whole line) lets a
        command run mid-line: `105+ /paste-last-result` keeps `105+ ` and the
        window inserts the result where the token was."""
        cursor = self.textCursor()
        cursor.movePosition(
            QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, len(name)
        )
        cursor.removeSelectedText()
        self._clear_ghost()
        self.command_entered.emit(name)

    def _run_command_line(self, name: str, arg: str) -> None:
        """Delete the whole logical block, then emit `"name arg"` so the window
        can act. Used for argument-carrying commands, which own the whole line."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(
            QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor
        )
        cursor.removeSelectedText()
        self._clear_ghost()
        self.command_entered.emit(f"{name} {arg}".strip())
