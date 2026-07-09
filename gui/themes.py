"""Color themes and hex validation (Qt-free so it stays unit-testable).

Data-only, like `engine/words.py`: extend by adding a `THEMES` entry. The GUI
(`gui/main_window.py`) turns a `Theme` into a stylesheet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


@dataclass(frozen=True)
class Theme:
    """A pane color pair: background + foreground, both `#rgb`/`#rrggbb` hex."""

    background: str
    foreground: str


THEMES: dict[str, Theme] = {
    "dracula": Theme("#282a36", "#f8f8f2"),
    "nord": Theme("#2e3440", "#d8dee9"),
    "monokai": Theme("#272822", "#f8f8f2"),
    "solarized-dark": Theme("#002b36", "#839496"),
    "solarized-light": Theme("#fdf6e3", "#657b83"),
}


def is_valid_hex(color: str) -> bool:
    """True if `color` is a `#rgb` or `#rrggbb` hex string (whitespace ignored)."""
    return bool(_HEX.match(color.strip()))


def theme_names() -> list[str]:
    """Preset theme names, in registration order."""
    return list(THEMES)
