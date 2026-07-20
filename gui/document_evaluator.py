"""Evaluate a whole multi-line document into per-line results.

Deliberately Qt-free so the notepad logic is unit-testable without a display.
A fresh scope is built on every call and lines run top-to-bottom, so deleting or
editing an earlier line correctly updates every line that depends on it.
"""

from __future__ import annotations

import re

from engine import EvalResult, evaluate
from engine.inline import scope_key
from engine.preprocess import has_inline_var, starts_with_binary_op

# The decimal style (separator, fraction digits) a line inherits from its group.
Style = tuple[str, int | None]

# A decimal number in the raw input: capture the separator and the fraction.
_INPUT_DECIMAL_RE = re.compile(r"\d+([.,])(\d+)")

_SUM_KEY = scope_key("sum")


def evaluate_document(text: str) -> list[EvalResult]:
    """Return one EvalResult per line of `text`, sharing a fresh variable scope.

    Also feeds the `$sum` inline variable: `_SUM_KEY` is injected before each
    line as the running total of the successful results *above* it in the current
    group (a contiguous block of lines; a blank line starts a new group).
    """
    scope: dict[str, float] = {}
    results: list[EvalResult] = []
    group_sum = 0.0
    for line in text.split("\n"):
        if not line.strip():
            group_sum = 0.0
        scope[_SUM_KEY] = group_sum
        result = evaluate(line, scope)
        results.append(result)
        if result.success and result.value is not None:
            group_sum += result.value
    return results


def inherited_styles(lines: list[str]) -> list[Style | None]:
    """Per-line group decimal style to inherit, or None.

    A line inherits its group's `(separator, place count)` only when it carries
    no decimals of its own and either references an inline `$`-variable or starts
    with a binary operator (an implicit `$sum` continuation) — so `$sum - 35%`
    and `- 500` under a `,00` group render `,00` too. Mirrors the grouping in
    `evaluate_document`: a blank line starts a new group, and only lines *above*
    the current one contribute the style.
    """
    styles: list[Style | None] = []
    group_sep = "."
    group_places: int | None = None
    for line in lines:
        if not line.strip():
            group_sep, group_places = ".", None
        sep, places = _input_decimal_style(line)
        inherits = has_inline_var(line) or starts_with_binary_op(line)
        if places is None and group_places is not None and inherits:
            styles.append((group_sep, group_places))
        else:
            styles.append(None)
        if places is not None:
            group_places = max(group_places or 0, places)
            group_sep = sep
    return styles


def format_result(
    result: EvalResult, line: str | None = None, inherited: Style | None = None
) -> str:
    """Render a result as the short text shown in the results pane.

    Empty lines and errors render as blank so the pane stays quiet while typing.
    When `line` has explicit decimals ("100,00"), the output mirrors its decimal
    separator and place count so "100,00 + 19%" reads back as "119,00". When the
    line has none of its own, `inherited` (the group's style, for `$sum` lines)
    is used instead.
    """
    if not result.success or result.value is None:
        return ""
    sep, places = _input_decimal_style(line) if line else (".", None)
    if places is None and inherited is not None:
        sep, places = inherited
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
