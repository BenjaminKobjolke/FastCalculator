"""Inline `$`-variables: names that reference an aggregate of prior results.

Data-only, like `words.py`/`functions.py`: the single source of truth for which
`$name` tokens exist, shared by the engine (preprocessing) and the GUI
(autocomplete, coloring) so they can't drift. Extend by adding a name here.

Each `$name` is rewritten in preprocessing to the internal scope key
`scope_key(name)` (a plain identifier), whose value the document layer
(`gui/document_evaluator.py`) computes and injects into `scope` per line. The
engine itself holds no aggregate state — `$sum` only has meaning with document
context.
"""

from __future__ import annotations

# The inline variable names, without the leading '$'. Extend here: "avg", ...
INLINE_VARS: tuple[str, ...] = ("sum",)

_PREFIX = "_inline_"


def scope_key(name: str) -> str:
    """Internal scope key a `$name` token resolves to (`"sum"` -> `"_inline_sum"`)."""
    return _PREFIX + name
