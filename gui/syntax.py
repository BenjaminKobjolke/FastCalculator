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
from engine.radix import RADIX_LITERAL_PATTERN
from engine.units import UNITS
from engine.words import PERCENT_WORDS, WORD_OPERATORS

# The user-facing color categories (also the QSettings/command suffixes).
# `inline` tints `$`-variables ("$sum"), distinct from user `variable` names.
CATEGORIES: tuple[str, ...] = ("number", "operator", "function", "variable", "inline")

# Function/constant/unit names color as `function` — a single source of truth so
# `km`, `sqrt`, `pi` all read as recognized words, not stray variables. Internal
# pace names (leading "_") are excluded; users never type them.
_NAMES = (
    {name.lower() for name in FUNCTIONS}
    | {name.lower() for name in CONSTANTS}
    | {name.lower() for name in UNITS if not name.startswith("_")}
)

# Longest-first so a phrase ("divided by") wins over its parts ("over"/"by"),
# matching the preprocessing regex in `engine/preprocess.py`.
_WORD_ALT = "|".join(
    re.escape(w) for w in sorted((k.lower() for k in WORD_OPERATORS), key=len, reverse=True)
)

# One ordered scan. Word operators are tried before identifiers so "mal" is an
# operator, while `\b` anchors keep "malaria" a plain identifier. A number's
# trailing "%" (postfix percent, "19%") is part of the number; a lone "%"
# (modulo) falls through to the symbol operators. Repeated separator groups keep
# a written-out amount ("34.234,89") one token instead of two.
_TOKEN_RE = re.compile(
    r"(?P<operator>\b(?:" + _WORD_ALT + r")\b)"
    r"|(?P<number>" + RADIX_LITERAL_PATTERN + r"|\d+(?:[.,]\d+)*%?)"
    r"|(?P<inline>\$[A-Za-z_]\w*)"
    r"|(?P<ident>[A-Za-z_]\w*)"
    r"|(?P<symop>[-+*/^%=<>!])",
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
    percent_end: int | None = None
    for m in _TOKEN_RE.finditer(line):
        kind = m.lastgroup
        if kind == "symop":
            category = "operator"
        elif kind == "ident":
            is_percent_word = (
                percent_end is not None
                and not line[percent_end : m.start()].strip()
                and m.group().lower() in PERCENT_WORDS
            )
            category = (
                "operator"
                if is_percent_word
                else "function"
                if m.group().lower() in _NAMES
                else "variable"
            )
        else:  # "operator" (word), "number", or "inline" ($-variable)
            assert kind is not None
            category = kind
        spans.append((m.start(), len(m.group()), category))
        percent_end = m.end() if kind == "number" and m.group().endswith("%") else None
    return spans
