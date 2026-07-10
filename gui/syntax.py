"""Qt-free tokenizer for notepad syntax coloring.

Splits a raw input line into colored spans, reusing the engine's own data maps
(`WORD_OPERATORS`, `FUNCTIONS`, `CONSTANTS`) as the single source of truth so the
highlighter never drifts from what the evaluator actually understands. Kept free
of PySide6 so it is unit-testable without a display, like `document_evaluator`.

The Qt layer (`gui/highlighter.py`) turns each span into a text color.
"""

from __future__ import annotations

import re

from engine.functions import CONSTANTS, FUNCTIONS
from engine.words import WORD_OPERATORS

# The user-facing color categories (also the QSettings/command suffixes).
# `inline` tints `$`-variables ("$sum"), distinct from user `variable` names.
CATEGORIES: tuple[str, ...] = ("number", "operator", "function", "variable", "inline")

_NAMES = {name.lower() for name in FUNCTIONS} | {name.lower() for name in CONSTANTS}

# Longest-first so a phrase ("divided by") wins over its parts ("over"/"by"),
# matching the preprocessing regex in `engine/preprocess.py`.
_WORD_ALT = "|".join(
    re.escape(w) for w in sorted((k.lower() for k in WORD_OPERATORS), key=len, reverse=True)
)

# One ordered scan. Word operators are tried before identifiers so "mal" is an
# operator, while `\b` anchors keep "malaria" a plain identifier. A number's
# trailing "%" (postfix percent, "19%") is part of the number; a lone "%"
# (modulo) falls through to the symbol operators.
_TOKEN_RE = re.compile(
    r"(?P<operator>\b(?:" + _WORD_ALT + r")\b)"
    r"|(?P<number>\d+(?:[.,]\d+)?%?)"
    r"|(?P<inline>\$[A-Za-z_]\w*)"
    r"|(?P<ident>[A-Za-z_]\w*)"
    r"|(?P<symop>[-+*/^%=])",
    re.IGNORECASE,
)


def tokenize(line: str) -> list[tuple[int, int, str]]:
    """Return `(start, length, category)` spans for `line`.

    Whitespace, parens, `;` and other punctuation produce no span (they keep the
    default foreground). A `/command` line yields nothing, so command text is
    never mis-colored as math.
    """
    if line.lstrip().startswith("/"):
        return []
    spans: list[tuple[int, int, str]] = []
    for m in _TOKEN_RE.finditer(line):
        kind = m.lastgroup
        if kind == "symop":
            category = "operator"
        elif kind == "ident":
            category = "function" if m.group().lower() in _NAMES else "variable"
        else:  # "operator" (word), "number", or "inline" ($-variable)
            assert kind is not None
            category = kind
        spans.append((m.start(), len(m.group()), category))
    return spans
