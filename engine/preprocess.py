"""Turn a human-typed line into a clean Python-math string ready for ast.parse.

Pipeline (strict order):
  0. peel a leading "Label:" prefix so "Price: 5 + 5" still computes
  1. split off a leading "name =" assignment (single '=', not '==')
  2. comma-decimal normalize: a comma between two digits becomes '.'
     (both ',' and '.' mean decimal point — the whole point of this app)
  3. conversion: "<expr> in|to <unit>" -> "_to(<expr>, <Name>)" (captured first,
     before the unit/pace steps can mangle the target)
  4. time literals: "mm:ss" / "h:mm:ss" -> "_time(<seconds>)"
  5. postfix percent: "19%" -> "_pct(19)"
  6. 'x' between two numbers becomes '*' ("10 x 10"); a lone 'x' stays a variable
  7. ';' -> ',' so multi-arg functions like min(1;2) reach ast as min(1,2)
  8. pace suffix: "min/km" / "/km" -> "/ km" (division by a unit distance)
  9. adjacency: "1 h 30 min" -> "1 h + 30 min" (before units are parenthesized)
  10. unit words: "10 km" -> "(10 * km)" (known units only; parenthesized so
      "50:00 / 10 km" stays time / (10*km))
  11. word operators -> symbols (English + German), longest phrase first
  12. '^' -> '**' because Python ast reads '^' as bitwise XOR

These string rewrites live in `normalize()`. `strip_unknown_words` runs after
`normalize()` (word-operators already gone) to drop *unknown* unit words like the
"apples" in "5 + 5 apples" — known running units (km, mi, ...) are quantities by
then, so they survive. It reports what it dropped, so a line can still be
*labelled* with a word that carries no math ("60 Watt" -> 60, labelled "Watt").
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .inline import INLINE_VARS, scope_key
from .words import WORD_OPERATORS

# Case-insensitive lookup: lowercase phrase -> symbol.
_WORD_LOOKUP: dict[str, str] = {k.lower(): v for k, v in WORD_OPERATORS.items()}

# One regex, alternatives sorted longest-first so "divided by" beats "over"
# and "geteilt durch" beats "durch". \b anchors avoid matching inside words.
_WORD_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(k) for k in sorted(_WORD_LOOKUP, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

# A leading "Label:" prefix. The label must contain a letter (so "12:30" is left
# alone, not read as label "12" + expr "30") and no colon of its own. The colon
# must not be digit-preceded, so a time literal like "50:00" (and the "50:00" in
# "10 km / 50:00", where the letters of "km" would otherwise satisfy the letter
# rule) is left for the time step, not misread as a label. The `lambda` guard
# stops "lambda: 1" being read as label "lambda" + expr "1" — it stays a lambda
# so the walker rejects it (the walker guards everything else too).
_LABEL_RE = re.compile(r"^\s*(?!lambda\b)[^:]*[A-Za-z][^:]*(?<!\d):\s*(.+)$")
_IDENT_RE = re.compile(r"[A-Za-z_]\w*")
_ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+)$")
_COMMA_DECIMAL_RE = re.compile(r"(?<=\d),(?=\d)")
# "10 x 10" / "10x10" -> multiply. Only between numbers so a standalone `x`
# stays a variable ("x = 10", "x hoch 2").
# ponytail: number-flanked only; `10 x pi` / `10 x (2+3)` still won't multiply.
_X_MULTIPLY_RE = re.compile(r"(?<=[\d.])\s*[xX]\s*(?=[\d.])")
# Postfix percent: "19%" -> _pct(19). Only when '%' has no right operand, so
# modulo ("10 % 3") is left alone. The evaluator makes '+'/'-' apply the
# percent to the left side (Numi-style: 100+19% = 119); '*'/'/' just use 0.19.
_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%(?!\s*[\w.(])")
# Inline `$`-variables ("$sum") -> their internal scope name ("_inline_sum").
# Only defined names are rewritten; a stray "$foo" is left for ast.parse to
# reject as an invalid expression.
_DOLLAR_RE = re.compile(r"\$(" + "|".join(re.escape(n) for n in INLINE_VARS) + r")\b")
# The German comparison phrase, checked on the *raw* line so the evaluator can
# localize a true/false result before word rewriting erases the language.
_GERMAN_COMPARE_RE = re.compile(r"\bist\s+gleich\b", re.IGNORECASE)
# A line beginning with a binary operator continues from the running total
# ("$sum"): "- 4000" means "$sum - 4000". `**` first so it wins over `*`. The
# evaluator matches this against the *normalized* expr, so word operators and
# `^` are already the symbols `+ - * / % **` by then.
_LEADING_OP_RE = re.compile(r"^\s*(\*\*|[-+*/%])")

# --- Running units (distance / time / pace / speed) ------------------------
# Time literal: mm:ss or h:mm:ss (colon count disambiguates), 1-2 digit fields.
# Colons are untouched by the comma-decimal and ';' steps, so no clash. Seconds
# are computed at rewrite time and emitted as an int -> `_time(<seconds>)`.
_TIME_RE = re.compile(r"(?<!\d)(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?(?!\d)")

# Surface unit word -> canonical unit Name (a reserved identifier the evaluator
# resolves via engine.units.UNITS). Only these are turned into quantities; every
# other trailing word (kg, apples) is left for `strip_unknown_words` to drop.
_UNIT_ALIASES: dict[str, str] = {
    "km/h": "kmh",
    "kmh": "kmh",
    "kph": "kmh",
    "mph": "mph",
    "km": "km",
    "kms": "km",
    "kilometer": "km",
    "kilometers": "km",
    "kilometre": "km",
    "kilometres": "km",
    "mi": "mi",
    "mile": "mi",
    "miles": "mi",
    "m": "m",
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
    "min": "min",
    "h": "h",
    "s": "s",
}
_UNIT_ALT = "|".join(re.escape(u) for u in sorted(_UNIT_ALIASES, key=len, reverse=True))
# A number glued/spaced to a known unit -> "(<mag> * <Name>)". Parenthesized so
# "50:00 / 10 km" stays time / (10*km), not (time/10)*km. `(?![A-Za-z/])` stops
# `m` matching inside `min` and keeps the km of `km/h` from matching alone.
_UNIT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(" + _UNIT_ALT + r")(?![A-Za-z/])", re.IGNORECASE)

# Pace suffix: `/km`, `min/km`, `/mi`, `min/mi` glued -> division by a unit
# distance (`_time(270) / km`). Only a slash glued to km/mi; a spaced `/` stays
# ordinary division. The optional `min` is redundant noise the literal already
# carries, so it is consumed.
_PACE_UNIT_RE = re.compile(r"(?:\bmin\s*)?/(km|mi)\b", re.IGNORECASE)

# Adjacent quantities imply addition ("1 h 30 min" == 1 h + 30 min). Runs before
# unit parenthesization, so it sees the raw "<number> <unit>" form.
_ADJACENT_RE = re.compile(r"(\d(?:[\d.]*)?\s*(?:km|mi|m|min|h|s)\b)\s+(?=\d)", re.IGNORECASE)

# Conversion target surface form -> reserved unit Name (slash-free, so the pace
# step never mangles it). Distance/speed/pace only; time renders as h:mm:ss so
# converting time units is a no-op we skip.
_CONV_TARGETS: dict[str, str] = {
    "km": "km",
    "kilometer": "km",
    "kilometers": "km",
    "kms": "km",
    "mi": "mi",
    "mile": "mi",
    "miles": "mi",
    "m": "m",
    "meter": "m",
    "meters": "m",
    "km/h": "kmh",
    "kmh": "kmh",
    "kph": "kmh",
    "mph": "mph",
    "/km": "_pace_km",
    "min/km": "_pace_km",
    "/mi": "_pace_mi",
    "min/mi": "_pace_mi",
}
_CONV_ALT = "|".join(re.escape(t) for t in sorted(_CONV_TARGETS, key=len, reverse=True))
# "<expr> in|to <unit>" -> "_to(<expr>, <Name>)". The keyword is bracketed by
# whitespace on both sides, so the `in` inside `min`/`sin` never matches; runs
# before the unit/pace steps so the target is captured before they touch it.
_CONV_RE = re.compile(r"^(.*\S)\s+(?:in|to)\s+(" + _CONV_ALT + r")\s*$", re.IGNORECASE)
_MULTISPACE_RE = re.compile(r"\s{2,}")


def _time_repl(match: re.Match[str]) -> str:
    a, b, c = match.group(1), match.group(2), match.group(3)
    seconds = int(a) * 60 + int(b) if c is None else int(a) * 3600 + int(b) * 60 + int(c)
    return f"_time({seconds})"


def _unit_repl(match: re.Match[str]) -> str:
    return f"({match.group(1)} * {_UNIT_ALIASES[match.group(2).lower()]})"


def _pace_repl(match: re.Match[str]) -> str:
    return f" / {match.group(1).lower()}"


def _conv_repl(match: re.Match[str]) -> str:
    return f"_to({match.group(1)}, {_CONV_TARGETS[match.group(2).lower()]})"


def has_inline_var(line: str) -> bool:
    """True if the line references a defined inline `$`-variable ("$sum").

    Reuses `_DOLLAR_RE` (the same names as `normalize`), so a stray `$foo` that
    isn't a declared inline var reads as False.
    """
    return _DOLLAR_RE.search(line) is not None


def uses_german_comparison(line: str) -> bool:
    """True if the raw line compares via the German phrase ("ist gleich"),
    so its true/false result renders as "wahr"/"falsch"."""
    return _GERMAN_COMPARE_RE.search(line) is not None


def starts_with_binary_op(line: str) -> bool:
    """True if the line's expression begins with a binary operator ("- 4000").

    Peels a `Label:` prefix and a `name =` assignment first, so `Total: - 5` and
    `x = * 2` are recognized. Uses the same `_LEADING_OP_RE` the evaluator uses,
    so the display side (decimal-style inheritance) can't drift from the math.
    """
    _, expr = split_assignment(strip_label(line))
    return _LEADING_OP_RE.match(expr) is not None


def strip_label(line: str) -> str:
    """Drop a leading 'Label:' prefix; return the rest ("Price: 5+5" -> "5+5").

    Unchanged when there is no such label, so plain expressions and time-like
    "12:30" (no letter before the colon) pass through untouched.
    """
    match = _LABEL_RE.match(line)
    return match.group(1) if match else line


@dataclass(frozen=True)
class StrippedExpr:
    """Result of `strip_unknown_words`: the cleaned expression plus the words
    it removed, in the order they appeared.

    The dropped words carry no math — they are the raw material for the
    display-only unit label ("60 Watt" -> 60, labelled "Watt").
    """

    expr: str
    dropped: tuple[str, ...]


def strip_unknown_words(expr: str, known: set[str]) -> StrippedExpr:
    """Drop unit words like "apples" in "5 + 5 apples", keeping the math.

    A bare identifier is removed only when it is (a) not a known name (scope
    variable / constant / function), (b) not a function call (not followed by
    '('), and (c) sitting right after a value — a digit, '.', or ')'. That last
    rule is what tells a trailing unit ("5 apples") from an operand in the
    expression ("foo + 1", which stays so the walker still flags it).
    """
    # ponytail: single unit word per value; "5 square meters" drops only "meters".
    dropped: list[str] = []

    def repl(match: re.Match[str]) -> str:
        name = match.group(0)
        if name in known or expr[match.end() :].startswith("("):
            return name
        before = expr[: match.start()].rstrip()
        if before and before[-1] in "0123456789.)":
            dropped.append(name)
            return ""
        return name

    return StrippedExpr(_IDENT_RE.sub(repl, expr), tuple(dropped))


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
    """Rewrite a raw expression into Python-math syntax.

    Order matters: conversion is captured before the unit/pace steps can mangle
    its target; time literals become `_time(...)` before percent/units; pace
    suffixes resolve before units so a bare `km` survives; adjacency runs before
    units are parenthesized; word operators run before `^`->`**`.
    """
    expr = _DOLLAR_RE.sub(lambda m: scope_key(m.group(1)), expr)
    expr = _COMMA_DECIMAL_RE.sub(".", expr)
    expr = _CONV_RE.sub(_conv_repl, expr)
    expr = _TIME_RE.sub(_time_repl, expr)
    expr = _PERCENT_RE.sub(r"_pct(\1)", expr)
    expr = _X_MULTIPLY_RE.sub("*", expr)
    expr = expr.replace(";", ",")
    expr = _PACE_UNIT_RE.sub(_pace_repl, expr)
    expr = _ADJACENT_RE.sub(r"\1 + ", expr)
    expr = _UNIT_RE.sub(_unit_repl, expr)
    expr = _WORD_PATTERN.sub(lambda m: _WORD_LOOKUP[m.group(0).lower()], expr)
    expr = expr.replace("^", "**")
    return _MULTISPACE_RE.sub(" ", expr).strip()
