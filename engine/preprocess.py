"""Turn a human-typed line into a clean Python-math string ready for ast.parse.

Pipeline (strict order):
  1. split off a leading "name =" assignment (single '=', not '==')
  2. comma-decimal normalize: a comma between two digits becomes '.'
     (both ',' and '.' mean decimal point — the whole point of this app)
  3. ';' -> ',' so multi-arg functions like min(1;2) reach ast as min(1,2)
     (needed because ',' is now a decimal point, so args can't use it)
  4. word operators -> symbols (English + German), longest phrase first
  5. '^' -> '**' because Python ast reads '^' as bitwise XOR

Steps 2-5 are pure string rewrites and live in `normalize()`.
"""

from __future__ import annotations

import re

from .words import WORD_OPERATORS

# Case-insensitive lookup: lowercase phrase -> symbol.
_WORD_LOOKUP: dict[str, str] = {k.lower(): v for k, v in WORD_OPERATORS.items()}

# One regex, alternatives sorted longest-first so "divided by" beats "over"
# and "geteilt durch" beats "durch". \b anchors avoid matching inside words.
_WORD_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(k) for k in sorted(_WORD_LOOKUP, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

_ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+)$")
_COMMA_DECIMAL_RE = re.compile(r"(?<=\d),(?=\d)")


def split_assignment(line: str) -> tuple[str | None, str]:
    """Return (variable_name, expression). name is None when not an assignment.

    A single '=' with a bare identifier on the left is an assignment. '==' is
    left untouched (it is not a valid expression here, but that is the walker's
    concern, not ours).
    """
    match = _ASSIGNMENT_RE.match(line)
    if match and not match.group(2).startswith("="):
        return match.group(1), match.group(2)
    return None, line


def normalize(expr: str) -> str:
    """Rewrite a raw expression into Python-math syntax (steps 2-5)."""
    expr = _COMMA_DECIMAL_RE.sub(".", expr)
    expr = expr.replace(";", ",")
    expr = _WORD_PATTERN.sub(lambda m: _WORD_LOOKUP[m.group(0).lower()], expr)
    expr = expr.replace("^", "**")
    return expr
