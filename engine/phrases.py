"""Rewrite natural-language percent phrases before expression parsing."""

from __future__ import annotations

import re

_AS_PERCENT_OF_RE = re.compile(r"(.+?)\s+as\s+a?\s*%\s+of\s+(.+)", re.IGNORECASE)
_PERCENT_AMOUNT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%\s+(of|von|on|off)\s+(.+)", re.IGNORECASE)


def rewrite_percent_phrases(expression: str) -> str:
    """Convert supported percent phrases to ordinary arithmetic."""
    match = _AS_PERCENT_OF_RE.search(expression)
    if match:
        before, after = match.groups()
        replacement = f"(100 * ({before}) / ({after}))"
        return expression[: match.start()] + replacement + expression[match.end() :]

    match = _PERCENT_AMOUNT_RE.search(expression)
    if not match:
        return expression

    percent, phrase, amount = match.groups()
    operation = phrase.lower()
    if operation in {"of", "von"}:
        replacement = f"({percent}% * ({amount}))"
    elif operation == "on":
        replacement = f"(({amount}) * (1 + {percent}%))"
    else:
        replacement = f"(({amount}) * (1 - {percent}%))"
    return expression[: match.start()] + replacement + expression[match.end() :]
