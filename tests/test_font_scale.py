from gui.font_scale import MAX_POINT_SIZE, MIN_POINT_SIZE, clamp_font_size


def test_clamp_within_bounds_unchanged() -> None:
    assert clamp_font_size(12) == 12


def test_clamp_floor() -> None:
    assert clamp_font_size(MIN_POINT_SIZE - 5) == MIN_POINT_SIZE


def test_clamp_ceiling() -> None:
    assert clamp_font_size(MAX_POINT_SIZE + 5) == MAX_POINT_SIZE
