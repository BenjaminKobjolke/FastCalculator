"""Evaluate a whole multi-line document into per-line results.

Deliberately Qt-free so the notepad logic is unit-testable without a display.
A fresh scope is built on every call and lines run top-to-bottom, so deleting or
editing an earlier line correctly updates every line that depends on it.
"""

from __future__ import annotations

import ast
import re

from engine import EvalResult, evaluate
from engine.errors import IncompatibleUnitsError
from engine.inline import scope_key
from engine.preprocess import has_inline_var, starts_with_binary_op
from engine.units import Quantity, apply_binop, dimensionless

# The decimal style (separator, fraction digits) a line inherits from its group.
Style = tuple[str, int | None]

# A decimal number in the raw input: capture the separator and the fraction.
_INPUT_DECIMAL_RE = re.compile(r"\d+([.,])(\d+)")

_SUM_KEY = scope_key("sum")


def evaluate_document(text: str) -> list[EvalResult]:
    """Return one EvalResult per line of `text`, sharing a fresh variable scope.

    Also feeds the `$sum` inline variable: `_SUM_KEY` is injected before each
    line as the running total of the successful results *above* it in the current
    group (a contiguous block of lines; a blank line starts a new group). The
    total is a `Quantity`, so units flow through `$sum` and leading-operator
    continuations ("5 km" + "3 km" -> "8 km"; a pace line then "* 42 km" -> a
    finish time). A dimension-incompatible result restarts the total from itself,
    so mixing units never errors and plain-number groups behave exactly as before.
    """
    scope: dict[str, Quantity] = {}
    results: list[EvalResult] = []
    group_total: Quantity = dimensionless(0.0)
    for line in text.split("\n"):
        if not line.strip():
            group_total = dimensionless(0.0)
        scope[_SUM_KEY] = group_total
        result = evaluate(line, scope)
        results.append(result)
        if result.success and result.quantity is not None:
            try:
                group_total = apply_binop(ast.Add, group_total, result.quantity)
            except IncompatibleUnitsError:
                group_total = result.quantity
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
    result: EvalResult,
    line: str | None = None,
    inherited: Style | None = None,
    max_decimals: int | None = None,
) -> str:
    """Render a result as the short text shown in the results pane.

    Empty lines and errors render as blank so the pane stays quiet while typing.
    When `line` has explicit decimals ("100,00"), the output mirrors its decimal
    separator and place count so "100,00 + 19%" reads back as "119,00". When the
    line has none of its own, `inherited` (the group's style, for `$sum` lines)
    is used instead. `max_decimals` (the persisted `/round` setting) caps the
    fraction digits of plain numbers — it rounds, never pads.
    """
    if not result.success or result.value is None:
        return ""
    # Unit-bearing results render from their kind; time/pace as clock text, the
    # rest as a number with a unit suffix (keeping the input's decimal separator).
    if result.kind == "time":
        return _format_hms(result.value)
    if result.kind == "pace":
        return f"{_format_mmss(result.value)} {result.unit}"
    if result.kind in ("distance", "speed"):
        return f"{_format_quantity(result.value, line, inherited)} {result.unit}"
    sep, places = _input_decimal_style(line) if line else (".", None)
    if places is None and inherited is not None:
        sep, places = inherited
    if places is not None and max_decimals is not None:
        places = min(places, max_decimals)
    if places is None:
        if max_decimals is None:
            return _format_number(result.value)
        return _format_capped(result.value, max_decimals)
    text = f"{result.value:.{places}f}"
    return text.replace(".", sep)


def _format_hms(seconds: float) -> str:
    """Whole seconds as `h:mm:ss` (or `m:ss` when under an hour)."""
    total = round(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def _format_mmss(seconds: float) -> str:
    """Pace as `m:ss` (seconds per km/mi)."""
    total = round(seconds)
    minutes, secs = divmod(total, 60)
    return f"{minutes}:{secs:02d}"


def _format_quantity(value: float, line: str | None, inherited: Style | None) -> str:
    """Numeric part of a distance/speed result: 4 significant figures, with the
    input line's decimal separator (or the inherited group style)."""
    sep, _ = _input_decimal_style(line) if line else (".", None)
    if sep == "." and inherited is not None:
        sep = inherited[0]
    return f"{value:.4g}".replace(".", sep)


def _input_decimal_style(line: str) -> tuple[str, int | None]:
    """(separator, max fraction digits) from the input, or (".", None) if none."""
    matches = _INPUT_DECIMAL_RE.findall(line)
    if not matches:
        return ".", None
    return matches[0][0], max(len(frac) for _, frac in matches)


def _format_capped(value: float, max_decimals: int) -> str:
    """Round to at most `max_decimals` fraction digits, trimming trailing zeros
    (cap, don't pad: 3.14159 -> "3.14", 5.0 -> "5", 2.5 -> "2.5")."""
    text = f"{value:.{max_decimals}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def _format_number(value: float) -> str:
    # Show integers without a trailing ".0"; trim float noise to 10 sig digits.
    if value == int(value) and abs(value) < 1e16:
        return str(int(value))
    return f"{value:.10g}"
