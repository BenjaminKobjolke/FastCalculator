"""Font-size bounds for the editor panes (Qt-free so it stays unit-testable)."""

from __future__ import annotations

MIN_POINT_SIZE = 6
MAX_POINT_SIZE = 48

RESULT_CHARS = 18  # ~what the old fixed 180px held at 12pt Consolas


def clamp_font_size(size: int) -> int:
    """Keep the editor font within readable, sane bounds."""
    return max(MIN_POINT_SIZE, min(MAX_POINT_SIZE, size))


def results_width(char_width_px: int, margin_px: int) -> int:
    """Pixel width for the results pane: N monospace chars + both margins."""
    return char_width_px * RESULT_CHARS + 2 * margin_px
