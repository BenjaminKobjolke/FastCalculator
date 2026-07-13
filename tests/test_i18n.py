"""Unit tests for the Qt-free i18n loader wrapper (`gui/i18n.py`)."""

from __future__ import annotations

import pytest

from gui import i18n


@pytest.fixture(autouse=True)
def _reset_language() -> None:
    # Every test starts from English so ordering never leaks state.
    i18n.set_language("en")


def test_t_returns_english_string() -> None:
    assert i18n.t("help.title") == "Calculator — Help"


def test_set_language_switches_to_german() -> None:
    i18n.set_language("de")
    assert i18n.t("help.title") == "Rechner — Hilfe"


def test_unknown_key_returns_the_key() -> None:
    # A missing key is visible, not a silent empty string.
    assert i18n.t("help.nope") == "help.nope"


def test_section_key_returns_the_key() -> None:
    # "help" points at a dict, not a leaf string -> echo the key.
    assert i18n.t("help") == "help"


def test_unknown_language_clamps_to_english() -> None:
    i18n.set_language("xx")
    assert i18n.t("help.title") == "Calculator — Help"


def test_german_falls_back_to_english_for_missing_key() -> None:
    # Both files carry the same keys, but the fallback path must not raise.
    i18n.set_language("de")
    assert i18n.t("help.commands.heading") == "Befehle"
