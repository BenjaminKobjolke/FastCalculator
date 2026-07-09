"""Unit tests for the Qt-free theme/color data (`gui/themes.py`)."""

from __future__ import annotations

from gui.themes import THEMES, Theme, is_valid_hex, theme_names


def test_dracula_colors() -> None:
    assert THEMES["dracula"] == Theme("#282a36", "#f8f8f2")


def test_theme_names_lists_all() -> None:
    names = theme_names()
    assert "nord" in names
    assert "solarized-light" in names
    assert names == list(THEMES)


def test_is_valid_hex_accepts_six_and_three_digit() -> None:
    assert is_valid_hex("#282a36")
    assert is_valid_hex("#abc")
    assert is_valid_hex("  #FFF  ")


def test_is_valid_hex_rejects_bad() -> None:
    assert not is_valid_hex("282a36")  # missing #
    assert not is_valid_hex("#12")  # wrong length
    assert not is_valid_hex("red")  # named color
    assert not is_valid_hex("")
    assert not is_valid_hex("#gggggg")  # non-hex digits
