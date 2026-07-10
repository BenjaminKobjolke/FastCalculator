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
    """A pane color pair plus a syntax palette, all `#rgb`/`#rrggbb` hex.

    `number`/`operator`/`function`/`variable`/`inline` tint the notepad tokens
    (see `gui/syntax.CATEGORIES`) and default to the Dracula accents. `inline` is
    the `$`-variable color; each preset uses its palette's orange/yellow accent.
    """

    background: str
    foreground: str
    number: str = "#bd93f9"
    operator: str = "#ff79c6"
    function: str = "#8be9fd"
    variable: str = "#50fa7b"
    inline: str = "#ffb86c"


THEMES: dict[str, Theme] = {
    "dracula": Theme("#282a36", "#f8f8f2", "#bd93f9", "#ff79c6", "#8be9fd", "#50fa7b", "#ffb86c"),
    "nord": Theme("#2e3440", "#d8dee9", "#b48ead", "#81a1c1", "#88c0d0", "#a3be8c", "#ebcb8b"),
    "monokai": Theme("#272822", "#f8f8f2", "#ae81ff", "#f92672", "#66d9ef", "#a6e22e", "#fd971f"),
    "solarized-dark": Theme(
        "#002b36", "#839496", "#6c71c4", "#d33682", "#268bd2", "#2aa198", "#b58900"
    ),
    "solarized-light": Theme(
        "#fdf6e3", "#657b83", "#6c71c4", "#d33682", "#268bd2", "#2aa198", "#b58900"
    ),
}


def syntax_colors(theme: Theme) -> dict[str, str]:
    """A `category -> hex` map for the highlighter (keys match `syntax.CATEGORIES`)."""
    return {
        "number": theme.number,
        "operator": theme.operator,
        "function": theme.function,
        "variable": theme.variable,
        "inline": theme.inline,
    }


def is_valid_hex(color: str) -> bool:
    """True if `color` is a `#rgb` or `#rrggbb` hex string (whitespace ignored)."""
    return bool(_HEX.match(color.strip()))


def theme_names() -> list[str]:
    """Preset theme names, in registration order."""
    return list(THEMES)
