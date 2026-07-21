from gui.window_limits import MAX_DECIMALS, clamp_decimals


def test_clamp_decimals_within_bounds() -> None:
    assert clamp_decimals(2) == 2


def test_clamp_decimals_floor() -> None:
    assert clamp_decimals(-1) == 0


def test_clamp_decimals_ceiling() -> None:
    assert clamp_decimals(MAX_DECIMALS + 5) == MAX_DECIMALS
