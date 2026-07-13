"""Qt-free i18n loader: a thin wrapper over the python-localization library.

Keeps a single module-level current language so the rest of the app calls a bare
`t("help.title")`. Stays import-safe without a display, so the lookup logic is
unit-testable. The window layer only renders what this returns.

# ponytail: LOCALES_DIR resolves from the source tree layout; a PyInstaller
# onefile build needs the locales/ folder added to the spec datas — wire that
# when we actually cut a frozen build.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from python_localization import Localization

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
_FALLBACK = "en"

# Languages we actually ship a `{lang}.json` for; anything else clamps to English
# so Localization's constructor (which validates the file exists) never raises.
_AVAILABLE = {p.stem for p in LOCALES_DIR.glob("*.json")}

_current = _FALLBACK


@cache
def _loc(lang: str) -> Localization:
    return Localization(
        driver="json",
        lang_dir=str(LOCALES_DIR),
        default_lang=lang,
        fallback_lang=_FALLBACK,
    )


def set_language(lang: str) -> None:
    """Set the active language, clamped to a shipped locale (else English)."""
    global _current
    _current = lang if lang in _AVAILABLE else _FALLBACK


def t(key: str) -> str:
    """Translate `key` (dot notation) in the active language.

    Returns the key itself when it is missing or points at a section rather than
    a leaf string, so a bad key shows up in the UI instead of vanishing.
    """
    value = _loc(_current).t(key)
    return value if isinstance(value, str) and value else key
