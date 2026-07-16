"""Unit tests for the Qt-free release-notes markdown builder (`gui/release_notes.py`)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gui import i18n
from gui.release_notes import RELEASE_NOTES_DIR, build_release_notes_markdown


@pytest.fixture(autouse=True)
def _reset_language() -> None:
    i18n.set_language("en")


def _note(directory: Path, version: str, lang: str, notes: list[str]) -> None:
    folder = directory / version
    folder.mkdir(parents=True, exist_ok=True)
    payload = {"version": version, "date": "2026-01-01", "notes": notes}
    (folder / f"{lang}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_versions_sorted_numerically_newest_first(tmp_path: Path) -> None:
    _note(tmp_path, "1.0.2", "en", ["Fixed: a"])
    _note(tmp_path, "1.0.10", "en", ["New: b"])
    md = build_release_notes_markdown(lang="en", notes_dir=tmp_path)
    assert md.index("## 1.0.10") < md.index("## 1.0.2")


def test_german_file_is_picked(tmp_path: Path) -> None:
    _note(tmp_path, "1.0.0", "en", ["New: english"])
    _note(tmp_path, "1.0.0", "de", ["Neu: deutsch"])
    md = build_release_notes_markdown(lang="de", notes_dir=tmp_path)
    assert "Neu: deutsch" in md
    assert "New: english" not in md


def test_missing_language_falls_back_to_english(tmp_path: Path) -> None:
    _note(tmp_path, "1.0.0", "en", ["New: english only"])
    md = build_release_notes_markdown(lang="de", notes_dir=tmp_path)
    assert "New: english only" in md


def test_non_version_dirs_and_broken_json_are_skipped(tmp_path: Path) -> None:
    _note(tmp_path, "1.0.0", "en", ["New: ok"])
    (tmp_path / "not-a-version").mkdir()
    broken = tmp_path / "2.0.0"
    broken.mkdir()
    (broken / "en.json").write_text("{ nope", encoding="utf-8")
    md = build_release_notes_markdown(lang="en", notes_dir=tmp_path)
    assert "New: ok" in md
    assert "2.0.0" not in md
    assert "not-a-version" not in md


def test_date_appears_in_heading(tmp_path: Path) -> None:
    _note(tmp_path, "1.0.0", "en", ["New: x"])
    assert "## 1.0.0 — 2026-01-01" in build_release_notes_markdown(lang="en", notes_dir=tmp_path)


def test_default_language_follows_i18n(tmp_path: Path) -> None:
    _note(tmp_path, "1.0.0", "en", ["New: english"])
    _note(tmp_path, "1.0.0", "de", ["Neu: deutsch"])
    i18n.set_language("de")
    assert "Neu: deutsch" in build_release_notes_markdown(notes_dir=tmp_path)


def test_real_dir_renders_initial_release() -> None:
    assert RELEASE_NOTES_DIR.is_dir()
    md = build_release_notes_markdown(lang="en")
    assert "## 0.1.0" in md
    assert "initial release of FastCalculator" in md
