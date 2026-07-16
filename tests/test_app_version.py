"""Unit tests for the version-file reader (`gui/app_version.py`)."""

from __future__ import annotations

import re
from pathlib import Path

from gui.app_version import VERSION_FILE, read_version


def test_real_version_file_is_semver() -> None:
    assert VERSION_FILE.is_file()
    assert re.fullmatch(r"\d+\.\d+\.\d+", read_version())


def test_missing_file_returns_zero_version(tmp_path: Path) -> None:
    assert read_version(tmp_path / "nope.txt") == "0.0.0"


def test_whitespace_is_stripped(tmp_path: Path) -> None:
    f = tmp_path / "version.txt"
    f.write_text("1.2.3\n", encoding="utf-8")
    assert read_version(f) == "1.2.3"
