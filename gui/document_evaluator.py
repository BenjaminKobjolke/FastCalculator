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

# A group needs at least this many contributing lines before its total is worth
# showing — otherwise a lone line would just echo itself one row down.
_MIN_TOTAL_LINES = 2


def evaluate_document(text: str) -> list[EvalResult]:
    """Return one EvalResult per line of `text`, sharing a fresh variable scope.

    Also feeds the `$sum` inline variable: `_SUM_KEY` is injected before each
    line as the running total of the successful results *above* it in the current
    group (a contiguous block of lines; a blank line starts a new group). The
    total is a `Quantity`, so units flow through `$sum` and leading-operator
    continuations ("5 km" + "3 km" -> "8 km"; a pace line then "* 42 km" -> a
    finish time). A dimension-incompatible result restarts the total from itself,
    so mixing units never errors and plain-number groups behave exactly as before.

    A leading-operator line ("- 100", "* 3") already folds the running total
    into its own result (the engine rewrote it to "$sum - 100"), so its result
    *replaces* the total rather than adding to it — adding would double-count
    the sum already inside `result.quantity`. `result.continued` (set by the
    engine) is what tells the two cases apart.

    The blank line that closes a group carries that group's total as its own
    result, so a block of numbers totals itself without anyone typing `$sum`.
    """
    scope: dict[str, Quantity] = {}
    results: list[EvalResult] = []
    group_total: Quantity = dimensionless(0.0)
    contributing = 0
    labels: set[str] = set()
    for line in text.split("\n"):
        if not line.strip():
            results.append(_group_total_result(group_total, contributing, labels))
            group_total, contributing, labels = dimensionless(0.0), 0, set()
            continue
        scope[_SUM_KEY] = group_total
        result = evaluate(line, scope)
        results.append(result)
        if result.success and result.quantity is not None:
            contributing += 1
            if result.kind is None and result.unit is not None:
                labels.add(result.unit)
            if result.continued:
                group_total = result.quantity
            else:
                try:
                    group_total = apply_binop(ast.Add, group_total, result.quantity)
                except IncompatibleUnitsError:
                    group_total = result.quantity
    return results


def _group_total_result(total: Quantity, contributing: int, labels: set[str]) -> EvalResult:
    """The result shown on the blank line that closes a group.

    Blank (`fail("empty")`, the pre-existing behavior) unless the group had
    enough contributing lines for a total to say anything new — which also keeps
    a run of blank lines from repeating the same number. The display-only unit
    label rides along only when every contributing line agreed on one.
    """
    if contributing < _MIN_TOTAL_LINES:
        return EvalResult.fail("empty")
    label = next(iter(labels)) if len(labels) == 1 else None
    return EvalResult.from_quantity(total, unit_label=label)


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
        sep, places = _input_decimal_style(line)
        # The blank line closing a group shows that group's total, so it
        # inherits the style — checked before the reset, or the style is gone.
        blank = not line.strip()
        inherits = blank or has_inline_var(line) or starts_with_binary_op(line)
        if places is None and group_places is not None and inherits:
            styles.append((group_sep, group_places))
        else:
            styles.append(None)
        if blank:
            group_sep, group_places = ".", None
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
    # Comparison results carry their localized word; never decimal-styled.
    if result.kind == "bool":
        return result.text or ""
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
            number = _format_number(result.value)
        else:
            number = _format_capped(result.value, max_decimals)
    else:
        number = f"{result.value:.{places}f}".replace(".", sep)
    # A plain number with a unit carries a display-only label ("60 Watt").
    return f"{number} {result.unit}" if result.unit is not None else number


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
