"""Turn a human-typed line into a clean Python-math string ready for ast.parse.

Pipeline (strict order):
  0. peel a leading "Label:" prefix so "Price: 5 + 5" still computes
  1. split off a leading "name =" assignment (single '=', not '==')
  2. comma-decimal normalize: a comma between two digits becomes '.'
     (both ',' and '.' mean decimal point — the whole point of this app)
  2b. 'x' between two numbers becomes '*' ("10 x 10"); a lone 'x' stays a variable
  3. ';' -> ',' so multi-arg functions like min(1;2) reach ast as min(1,2)
     (needed because ',' is now a decimal point, so args can't use it)
  4. word operators -> symbols (English + German), longest phrase first
  5. '^' -> '**' because Python ast reads '^' as bitwise XOR

Steps 2-5 are pure string rewrites and live in `normalize()`. `strip_unknown_words`
runs after `normalize()` (word-operators already gone) to drop unit words like the
"apples" in "5 + 5 apples".
"""

from __future__ import annotations

import re

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
# alone, not read as label "12" + expr "30") and no colon of its own. The
# `lambda` guard stops "lambda: 1" being read as label "lambda" + expr "1" — it
# stays a lambda so the walker rejects it (the walker guards everything else too).
_LABEL_RE = re.compile(r"^\s*(?!lambda\b)[^:]*[A-Za-z][^:]*:\s*(.+)$")
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


def strip_label(line: str) -> str:
    """Drop a leading 'Label:' prefix; return the rest ("Price: 5+5" -> "5+5").

    Unchanged when there is no such label, so plain expressions and time-like
    "12:30" (no letter before the colon) pass through untouched.
    """
    match = _LABEL_RE.match(line)
    return match.group(1) if match else line


def strip_unknown_words(expr: str, known: set[str]) -> str:
    """Drop unit words like "apples" in "5 + 5 apples", keeping the math.

    A bare identifier is removed only when it is (a) not a known name (scope
    variable / constant / function), (b) not a function call (not followed by
    '('), and (c) sitting right after a value — a digit, '.', or ')'. That last
    rule is what tells a trailing unit ("5 apples") from an operand in the
    expression ("foo + 1", which stays so the walker still flags it).
    """
    # ponytail: single unit word per value; "5 square meters" drops only "meters".

    def repl(match: re.Match[str]) -> str:
        name = match.group(0)
        if name in known or expr[match.end() :].startswith("("):
            return name
        before = expr[: match.start()].rstrip()
        if before and before[-1] in "0123456789.)":
            return ""
        return name

    return _IDENT_RE.sub(repl, expr)


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
    expr = _DOLLAR_RE.sub(lambda m: scope_key(m.group(1)), expr)
    expr = _COMMA_DECIMAL_RE.sub(".", expr)
    expr = _PERCENT_RE.sub(r"_pct(\1)", expr)
    expr = _X_MULTIPLY_RE.sub("*", expr)
    expr = expr.replace(";", ",")
    expr = _WORD_PATTERN.sub(lambda m: _WORD_LOOKUP[m.group(0).lower()], expr)
    expr = expr.replace("^", "**")
    return expr
