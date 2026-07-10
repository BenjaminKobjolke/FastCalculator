"""Unit tests for the frame-hiding decision (`gui/frameless_win.py`).

Pure logic only — no QApplication or real window needed, so this runs
headless on any platform.
"""

from __future__ import annotations

from gui.frameless_win import _WM_NCCALCSIZE, swallow_nccalcsize


def test_swallow_when_frameless_and_nccalcsize() -> None:
    assert swallow_nccalcsize(True, _WM_NCCALCSIZE, wparam=1) is True


def test_keep_when_not_frameless() -> None:
    assert swallow_nccalcsize(False, _WM_NCCALCSIZE, wparam=1) is False


def test_keep_other_messages() -> None:
    assert swallow_nccalcsize(True, 0x0001, wparam=1) is False


def test_keep_when_wparam_zero() -> None:
    # wParam == 0 means Windows isn't asking us to compute the client rect.
    assert swallow_nccalcsize(True, _WM_NCCALCSIZE, wparam=0) is False
