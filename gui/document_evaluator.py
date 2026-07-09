"""Evaluate a whole multi-line document into per-line results.

Deliberately Qt-free so the notepad logic is unit-testable without a display.
A fresh scope is built on every call and lines run top-to-bottom, so deleting or
editing an earlier line correctly updates every line that depends on it.
"""

from __future__ import annotations

import re

from engine import EvalResult, evaluate

# A decimal number in the raw input: capture the separator and the fraction.
_INPUT_DECIMAL_RE = re.compile(r"\d+([.,])(\d+)")


def evaluate_document(text: str) -> list[EvalResult]:
    """Return one EvalResult per line of `text`, sharing a fresh variable scope."""
    scope: dict[str, float] = {}
    return [evaluate(line, scope) for line in text.split("\n")]


def format_result(result: EvalResult, line: str | None = None) -> str:
    """Render a result as the short text shown in the results pane.

    Empty lines and errors render as blank so the pane stays quiet while typing.
    When `line` has explicit decimals ("100,00"), the output mirrors its decimal
    separator and place count so "100,00 + 19%" reads back as "119,00".
    """
    if not result.success or result.value is None:
        return ""
    sep, places = _input_decimal_style(line) if line else (".", None)
    if places is None:
        return _format_number(result.value)
    text = f"{result.value:.{places}f}"
    return text.replace(".", sep)


def _input_decimal_style(line: str) -> tuple[str, int | None]:
    """(separator, max fraction digits) from the input, or (".", None) if none."""
    matches = _INPUT_DECIMAL_RE.findall(line)
    if not matches:
        return ".", None
    return matches[0][0], max(len(frac) for _, frac in matches)


def _format_number(value: float) -> str:
    # Show integers without a trailing ".0"; trim float noise to 10 sig digits.
    if value == int(value) and abs(value) < 1e16:
        return str(int(value))
    return f"{value:.10g}"
