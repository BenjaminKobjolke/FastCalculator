"""Qt-free builder for the help window's markdown body.

Assembles the translated title + sections into one markdown string. Kept free of
Qt so the layout logic is unit-testable; `gui/help_window.py` only renders it.
"""

from __future__ import annotations

from gui.i18n import t
from gui.i18n_keys import TK

_SECTIONS = (
    (TK.HELP_BASICS_HEADING, TK.HELP_BASICS_BODY),
    (TK.HELP_COMMANDS_HEADING, TK.HELP_COMMANDS_BODY),
    (TK.HELP_VARIABLES_HEADING, TK.HELP_VARIABLES_BODY),
)


def build_help_markdown() -> str:
    """Full help document as markdown, in the active language."""
    parts = [f"# {t(TK.HELP_TITLE)}"]
    for heading_key, body_key in _SECTIONS:
        parts.append(f"## {t(heading_key)}\n\n{t(body_key)}")
    return "\n\n".join(parts)
