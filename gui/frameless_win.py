"""Borderless-but-snappable window support.

Hiding the title bar with Qt's ``FramelessWindowHint`` also strips the native
``WS_CAPTION`` / ``WS_THICKFRAME`` styles, and those are exactly what Windows
uses to drive Aero Snap and the Win+Arrow shortcuts. So a plain frameless Qt
window can no longer be snapped or moved by the OS.

``FramelessWindow`` keeps the window a normal native window (styles intact, so
the OS keeps managing it) and hides the caption/border by zeroing the
non-client area in the ``WM_NCCALCSIZE`` message — the standard trick used by
``qframelesswindow``. On non-Windows platforms it falls back to
``FramelessWindowHint`` (Aero Snap is a Windows-only concern there).
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtWidgets import QMainWindow

_IS_WIN = sys.platform == "win32"
_WM_NCCALCSIZE = 0x0083

if _IS_WIN:
    import ctypes
    from ctypes import wintypes

    _SWP_NOSIZE = 0x0001
    _SWP_NOMOVE = 0x0002
    _SWP_NOZORDER = 0x0004
    _SWP_FRAMECHANGED = 0x0020


def swallow_nccalcsize(frameless: bool, message: int, wparam: int) -> bool:
    """Whether a native message should be swallowed to hide the window frame.

    ``True`` only for a ``WM_NCCALCSIZE`` with ``wParam != 0`` while frameless:
    returning 0 for that message leaves the client area covering the whole
    window (no caption/border) while keeping the snap styles.
    """
    return frameless and message == _WM_NCCALCSIZE and bool(wparam)


class FramelessWindow(QMainWindow):
    """QMainWindow whose title bar can be hidden without losing native window
    management (Aero Snap / Win+Arrow) on Windows."""

    def __init__(self) -> None:
        super().__init__()
        self._frameless = False

    def set_frameless(self, enabled: bool, *, reshow: bool = True) -> None:
        """Show (``enabled=False``) or hide (``True``) the title bar.

        ``reshow`` re-shows the window after the change (a frame change hides it
        on Windows); pass ``False`` during construction, before the first show.
        """
        self._frameless = enabled
        if _IS_WIN:
            # Keep native styles; just force a frame recompute so WM_NCCALCSIZE
            # runs again and our new decision takes effect.
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                _SWP_NOSIZE | _SWP_NOMOVE | _SWP_NOZORDER | _SWP_FRAMECHANGED,
            )
        else:
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, enabled)
        if reshow:
            self.show()

    def nativeEvent(
        self, eventType: QByteArray | bytes | bytearray | memoryview, message: int
    ) -> object:
        if _IS_WIN and self._frameless and eventType == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if swallow_nccalcsize(self._frameless, msg.message, msg.wParam):
                # Leave the proposed client rect equal to the whole window rect:
                # no caption, no border, but the window keeps its snap styles.
                return True, 0
        return super().nativeEvent(eventType, message)
