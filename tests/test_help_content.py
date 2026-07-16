"""Unit tests for the Qt-free help-markdown builder (`gui/help_content.py`)."""

from __future__ import annotations

import pytest

from gui import i18n
from gui.help_content import build_help_markdown


@pytest.fixture(autouse=True)
def _reset_language() -> None:
    i18n.set_language("en")


def test_markdown_has_title_and_all_headings() -> None:
    md = build_help_markdown()
    assert "# FastCalculator — Help" in md
    assert "## Basics" in md
    assert "## Commands" in md
    assert "## Variables" in md


def test_markdown_includes_body_text() -> None:
    assert "decimal point" in build_help_markdown()


def test_markdown_title_carries_version() -> None:
    from gui.app_version import read_version

    assert f"v{read_version()}" in build_help_markdown()


def test_markdown_follows_language() -> None:
    i18n.set_language("de")
    md = build_help_markdown()
    assert "# FastCalculator — Hilfe" in md
    assert "## Grundlagen" in md
