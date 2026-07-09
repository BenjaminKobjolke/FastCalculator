"""Font-size bounds for the editor panes (Qt-free so it stays unit-testable)."""

from __future__ import annotations

MIN_POINT_SIZE = 6
MAX_POINT_SIZE = 48


def clamp_font_size(size: int) -> int:
    """Keep the editor font within readable, sane bounds."""
    return max(MIN_POINT_SIZE, min(MAX_POINT_SIZE, size))
