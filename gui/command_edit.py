"""Notepad input with inline ghost-text slash-command autosuggest.

Type `/c` and a grayed completion (`/clear`) is painted after the cursor.
Tab/Enter accepts, Up/Down cycles matches, Esc dismisses. Pressing Enter on a
full command line runs it (via the `command_entered` signal) instead of adding a
newline.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent, QPainter, QPaintEvent, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QWidget

from gui.commands import (
    command_at,
    common_prefix,
    parse_command,
    parse_command_line,
    suggest,
)


class _MenuOverlay(QWidget):
    """Full-width list of command matches, floated above the results pane.

    A child of the shared container (not the notepad viewport), so it isn't
    clipped by the notepad's narrower width — long command names show in full.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._rows: list[str] = []
        self._selected = 0

    def show_rows(self, rows: list[str], selected: int, font: QFont, top: int, width: int) -> None:
        self._rows = rows
        self._selected = selected
        self.setFont(font)
        line_h = self.fontMetrics().height()
        self.setGeometry(0, top, width, line_h * len(rows))
        self.raise_()
        self.show()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.fillRect(self.rect(), self.palette().base().color())
        metrics = self.fontMetrics()
        line_h = metrics.height()
        text_color = self.palette().text().color()
        ghost_color = self.palette().placeholderText().color()
        for i, cmd in enumerate(self._rows):
            baseline = i * line_h + metrics.ascent()
            painter.setPen(text_color if i == self._selected else ghost_color)
            painter.drawText(8, baseline, cmd)
        painter.end()


class CommandEdit(QPlainTextEdit):
    """QPlainTextEdit that recognises `/`-prefixed editor commands."""

    command_entered = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._ghost_matches: list[str] = []
        self._ghost_index = 0
        self._menu_open = False
        self._menu_overlay: _MenuOverlay | None = None
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
            # Live-narrowing to a single (or no) match collapses the menu back
            # to a plain ghost.
            if len(matches) <= 1:
                self._menu_open = False
            self.viewport().update()
        self._update_menu()

    def _ghost_suffix(self) -> str:
        """The grayed remainder shown after the cursor: the common prefix of all
        matches minus what's typed. Empty when the prefix can't extend."""
        if not self._ghost_matches:
            return ""
        prefix = self._current_prefix() or ""
        return common_prefix(self._ghost_matches)[len(prefix) :]

    def _clear_ghost(self) -> None:
        self._menu_open = False
        if self._ghost_matches:
            self._ghost_matches = []
            self._ghost_index = 0
        self.viewport().update()
        self._update_menu()

    def _update_menu(self) -> None:
        """Show/position/hide the overlay to match the current menu state."""
        parent = self.parentWidget()
        show = self._menu_open and len(self._ghost_matches) > 1 and parent is not None
        if not show:
            if self._menu_overlay is not None:
                self._menu_overlay.hide()
            return
        assert parent is not None
        if self._menu_overlay is None:
            self._menu_overlay = _MenuOverlay(parent)
        self._menu_overlay.setPalette(self.palette())
        top = self.viewport().mapTo(parent, self.cursorRect().bottomLeft()).y()
        self._menu_overlay.show_rows(
            self._ghost_matches, self._ghost_index, self.font(), top, parent.width()
        )

    def _accept_match(self, cmd: str) -> None:
        """Fill the full command `cmd`, replacing the typed prefix."""
        prefix = self._current_prefix() or ""
        if len(cmd) > len(prefix):
            self.textCursor().insertText(cmd[len(prefix) :])  # fires refresh
        self._clear_ghost()

    # --- painting ----------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        # The match list is drawn by the overlay widget, not here; only the
        # inline common-prefix ghost is painted on the viewport.
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

        if self._menu_open and key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            step = -1 if key == Qt.Key.Key_Up else 1
            self._ghost_index = (self._ghost_index + step) % len(self._ghost_matches)
            self._update_menu()
            return

        # Down opens the menu when several commands still match.
        if has_ghost and key == Qt.Key.Key_Down and len(self._ghost_matches) > 1:
            self._menu_open = True
            self._update_menu()
            return

        if has_ghost and key == Qt.Key.Key_Escape:
            if self._menu_open:
                self._menu_open = False
                self._update_menu()
                return
            self._clear_ghost()
            return

        if has_ghost and key == Qt.Key.Key_Tab:
            self._handle_tab()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._menu_open:
                self._accept_match(self._ghost_matches[self._ghost_index])
            elif len(self._ghost_matches) == 1:
                self._accept_match(self._ghost_matches[0])
            elif has_ghost:
                # Ambiguous prefix: show the menu instead of a bare newline.
                self._menu_open = True
                self._update_menu()
                return
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

    def _handle_tab(self) -> None:
        """Shell-style Tab: fill the common prefix; open the menu when several
        commands still match; complete fully when only one does."""
        if self._menu_open:
            self._accept_match(self._ghost_matches[self._ghost_index])
            return
        if len(self._ghost_matches) == 1:
            self._accept_match(self._ghost_matches[0])
            return
        suffix = self._ghost_suffix()
        if suffix:
            self.textCursor().insertText(suffix)  # fill the common prefix
        self._menu_open = True
        self._update_menu()

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
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        self._clear_ghost()
        self.command_entered.emit(f"{name} {arg}".strip())
