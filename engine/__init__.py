"""Pure, dependency-free expression engine for the calculator.

Public API:
    evaluate(line, scope) -> EvalResult
    EvalResult
    Scope  (type alias: dict[str, Quantity])
"""

from __future__ import annotations

from .evaluator import Scope, evaluate
from .result import EvalResult

__all__ = ["evaluate", "EvalResult", "Scope"]
