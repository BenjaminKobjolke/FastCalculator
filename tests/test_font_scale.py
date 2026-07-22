from gui.font_scale import (
    MAX_POINT_SIZE,
    MIN_POINT_SIZE,
    MIN_RESULT_CHARS,
    clamp_font_size,
    results_width,
)


def test_clamp_within_bounds_unchanged() -> None:
    assert clamp_font_size(12) == 12


def test_clamp_floor() -> None:
    assert clamp_font_size(MIN_POINT_SIZE - 5) == MIN_POINT_SIZE


def test_clamp_ceiling() -> None:
    assert clamp_font_size(MAX_POINT_SIZE + 5) == MAX_POINT_SIZE


def test_results_width_chars_plus_margins() -> None:
    assert results_width(10, 8, 12) == 10 * 12 + 16


def test_results_width_zero_margin() -> None:
    assert results_width(10, 0, 12) == 120


def test_results_width_clamps_to_minimum() -> None:
    assert results_width(10, 8, 0) == 10 * MIN_RESULT_CHARS + 16


def test_results_width_grows_with_char_width() -> None:
    assert results_width(20, 8, 12) > results_width(10, 8, 12)
