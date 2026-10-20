"""Rewrite radix literals and format explicit radix output requests."""

from __future__ import annotations

import re

RADIX_LITERAL_PATTERN = (
    r"(?<![A-Za-z0-9_.])(?:0[xX][0-9a-fA-F]+|0[bB][01]+|0[oO][0-7]+)(?![A-Za-z0-9_.])"
)
_RADIX_LITERAL_RE = re.compile(RADIX_LITERAL_PATTERN)
_RADIX_PREFIX_WORD_RE = re.compile(r"(?<![A-Za-z0-9_.])0[xXbBoO][A-Za-z_]\w*")
_RADIX_OUTPUT_RE = re.compile(r"\s+(?:in|to)\s+(hex|bin|oct)\s*$", re.IGNORECASE)
_PREFIXES = {"hex": "0x", "bin": "0b", "oct": "0o"}
_FORMATS = {"hex": "X", "bin": "b", "oct": "o"}


def rewrite_radix_literals(expression: str) -> str:
    """Replace complete hexadecimal, binary, and octal literals with decimal."""

    for match in _RADIX_PREFIX_WORD_RE.finditer(expression):
        if _RADIX_LITERAL_RE.fullmatch(match.group()) is None:
            raise ValueError("invalid radix literal")

    return _RADIX_LITERAL_RE.sub(lambda match: str(int(match.group(), 0)), expression)


def split_radix_output(expression: str) -> tuple[str, str | None]:
    """Split a trailing ``in|to hex|bin|oct`` from its expression."""

    match = _RADIX_OUTPUT_RE.search(expression)
    if match is None:
        return expression, None
    return expression[: match.start()].rstrip(), match.group(1).lower()


def format_radix(value: int, radix: str) -> str:
    """Format an integer with its requested prefix and uppercase digits."""

    sign = "-" if value < 0 else ""
    digits = format(abs(value), _FORMATS[radix])
    return f"{sign}{_PREFIXES[radix]}{digits}"
