"""Font-size bounds for the editor panes (Qt-free so it stays unit-testable)."""

from __future__ import annotations

MIN_POINT_SIZE = 6
MAX_POINT_SIZE = 48

MIN_RESULT_CHARS = 4  # pane must not collapse to nothing on an empty document


def clamp_font_size(size: int) -> int:
    """Keep the editor font within readable, sane bounds."""
    return max(MIN_POINT_SIZE, min(MAX_POINT_SIZE, size))


def results_width(char_width_px: int, margin_px: int, char_count: int) -> int:
    """Pixel width for the results pane: widest result + both margins."""
    return char_width_px * max(char_count, MIN_RESULT_CHARS) + 2 * margin_px
