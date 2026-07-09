"""Typed result of evaluating a single calculator line.

Crossing the engine->GUI boundary as a typed object, never a bag-of-keys dict.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalResult:
    """Outcome of evaluating one line.

    `assigned_name` is set only when the line was an assignment ("x = ...");
    it lets the GUI know a variable was defined.
    """

    success: bool
    value: float | None = None
    error: str | None = None
    assigned_name: str | None = None

    @classmethod
    def ok(cls, value: float, assigned_name: str | None = None) -> EvalResult:
        return cls(success=True, value=value, assigned_name=assigned_name)

    @classmethod
    def fail(cls, message: str) -> EvalResult:
        return cls(success=False, error=message)
