"""Whitelisted functions and constants available inside expressions.

Only names in these maps can be called / referenced. Everything else is rejected
by the AST walker, which is the security boundary against arbitrary code.
"""

from __future__ import annotations

import math
from collections.abc import Callable

# math.log defaults to natural log; expose base-10 as `log`, natural as `ln`.
FUNCTIONS: dict[str, Callable[..., float]] = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log10,
    "ln": math.log,
    "round": round,
    "abs": abs,
    "min": min,
    "max": max,
    "floor": math.floor,
    "ceil": math.ceil,
}

CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
}
