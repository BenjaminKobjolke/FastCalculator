"""Qt-free reader for the app version.

`version.txt` in the project root is the single source of truth (the release
scripts in `tools/` bump it). In a frozen PyInstaller build the file is bundled
next to the extracted modules, so the same relative path works.
"""

from __future__ import annotations

from pathlib import Path

VERSION_FILE = Path(__file__).resolve().parent.parent / "version.txt"


def read_version(path: Path = VERSION_FILE) -> str:
    """Version string `X.Y.Z`, or `0.0.0` if the file is missing/unreadable."""
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"
    return text or "0.0.0"
