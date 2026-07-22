"""Data-only word-operator maps (English + German).

Pure data, no logic. Extend by adding entries. The preprocessing step in
`preprocess.py` builds a longest-match-first regex from these keys, so a
multi-word phrase like "divided by" wins over the single word "over".
"""

from __future__ import annotations

# Natural-language operator words -> math symbol.
# `^` is later rewritten to `**` (Python ast reads `^` as bitwise XOR).
WORD_OPERATORS: dict[str, str] = {
    # multiply
    "multiplied by": "*",
    "times": "*",
    "mal": "*",
    # add
    "plus": "+",
    "add": "+",
    # subtract
    "minus": "-",
    "less": "-",
    # divide
    "divided by": "/",
    "geteilt durch": "/",
    "durch": "/",
    "over": "/",
    # power
    "to the power of": "^",
    "hoch": "^",
    # compare (equality; other comparisons are symbol-only: != < > <= >=)
    "equals": "==",
    "ist gleich": "==",
    # modulo
    "modulo": "%",
    "mod": "%",
}

# Localized true/false words for comparison results. The evaluator picks the
# language from the input line ("ist gleich" -> German), see `preprocess.
# uses_german_comparison`.
BOOL_TEXT: dict[str, tuple[str, str]] = {
    "en": ("true", "false"),
    "de": ("wahr", "falsch"),
}
