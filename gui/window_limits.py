"""Window/editor bounds (Qt-free so they stay unit-testable)."""

from __future__ import annotations

MIN_OPACITY = 10  # never 0: a fully invisible frameless window is unrecoverable
MAX_OPACITY = 100

DEFAULT_MARGIN = 8
MAX_MARGIN = 200

MAX_DECIMALS = 10


def clamp_opacity(percent: int) -> int:
    """Keep window opacity within a visible, recoverable range (percent)."""
    return max(MIN_OPACITY, min(MAX_OPACITY, percent))


def clamp_margin(px: int) -> int:
    """Keep the editor margin within sane pixel bounds."""
    return max(0, min(MAX_MARGIN, px))


def clamp_decimals(n: int) -> int:
    """Keep the /round decimal cap within 0..MAX_DECIMALS."""
    return max(0, min(MAX_DECIMALS, n))
