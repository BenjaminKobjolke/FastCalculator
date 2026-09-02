"""Thousands-separator handling for raw input numbers.

Lives outside `preprocess.py` only because that module is at its 300-line cap;
it is the same kind of pure, stdlib-only text rewrite and runs as one step of
`preprocess.normalize()`.

Only *unambiguous* grouping is rewritten. `1.000` could be one thousand or the
decimal 1.0, so it is left to the plain decimal rules; a number is only read as
grouped when it carries two or more groups ("1.234.567") or a group plus a
decimal part using the other separator ("34.234,89").
"""

from __future__ import annotations

import re

# `.` groups with an optional `,` decimal (German), and its mirror image.
# The lookarounds carry the weight:
#   (?<![\d.,]) stops a match starting mid-number, which is what keeps the two
#     patterns from fighting over "34.234,89" / "34,234.89";
#   (?![\d.,]) rejects "1.2345" — a group is exactly three digits and nothing
#     but the decimal part may follow it.
_DE_RE = re.compile(r"(?<![\d.,])(\d{1,3})((?:\.\d{3})+)(,\d+)?(?![\d.,])")
_EN_RE = re.compile(r"(?<![\d.,])(\d{1,3})((?:,\d{3})+)(\.\d+)?(?![\d.,])")
_PATTERNS = (_DE_RE, _EN_RE)

_MIN_UNAMBIGUOUS_GROUPS = 2


def strip_grouping(expr: str) -> str:
    """Rewrite unambiguously grouped numbers to plain Python literals.

    "34.234,89 + 19%" -> "34234.89 + 19%". Ambiguous single-group numbers and
    everything else are returned untouched.
    """
    for pattern in _PATTERNS:
        expr = pattern.sub(_replace, expr)
    return expr


def grouping_separator(expr: str) -> str | None:
    """The thousands separator `expr` uses, or None when it has no grouping.

    Callers that only need a yes/no answer test against None; the GUI needs the
    character itself, because the decimal separator of a grouped number is
    always the other one ("1.234.567" is German, so its decimals use ",").
    """
    for pattern in _PATTERNS:
        for match in pattern.finditer(expr):
            if _is_grouped(match):
                return match.group(2)[0]
    return None


def _is_grouped(match: re.Match[str]) -> bool:
    """The ambiguity rule, shared by both public functions."""
    _, groups, fraction = match.groups()
    group_count = len(groups) // 4  # every group is one separator plus three digits
    return bool(fraction) or group_count >= _MIN_UNAMBIGUOUS_GROUPS


def _replace(match: re.Match[str]) -> str:
    if not _is_grouped(match):
        return match.group(0)
    lead, groups, fraction = match.groups()
    digits = lead + re.sub(r"[.,]", "", groups)
    return f"{digits}.{fraction[1:]}" if fraction else digits
