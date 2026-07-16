"""Qt-free builder for the release-notes window's markdown body.

Reads `release_notes/<version>/<lang>.json` folders (the same files the release
tooling uploads), newest version first, falling back to English per version.
Kept free of Qt so it is unit-testable; the window layer only renders it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from gui.i18n import current_language, t
from gui.i18n_keys import TK

RELEASE_NOTES_DIR = Path(__file__).resolve().parent.parent / "release_notes"
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _load_notes(folder: Path, lang: str) -> dict[str, object] | None:
    for candidate in (folder / f"{lang}.json", folder / "en.json"):
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            return data
    return None


def build_release_notes_markdown(
    lang: str | None = None, notes_dir: Path = RELEASE_NOTES_DIR
) -> str:
    """Release notes as markdown in `lang` (default: active UI language)."""
    lang = lang or current_language()
    folders = [p for p in notes_dir.iterdir() if p.is_dir() and _VERSION_RE.match(p.name)]
    folders.sort(key=lambda p: tuple(int(n) for n in p.name.split(".")), reverse=True)

    parts = [f"# {t(TK.RELEASE_NOTES_TITLE)}"]
    for folder in folders:
        data = _load_notes(folder, lang)
        if data is None:
            continue
        date = data.get("date", "")
        heading = f"## {folder.name} — {date}" if date else f"## {folder.name}"
        notes = data.get("notes")
        items = notes if isinstance(notes, list) else []
        bullets = "\n".join(f"- {note}" for note in items if isinstance(note, str))
        parts.append(f"{heading}\n\n{bullets}" if bullets else heading)
    return "\n\n".join(parts)
