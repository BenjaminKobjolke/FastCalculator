"""Typed result of evaluating a single calculator line.

Crossing the engine->GUI boundary as a typed object, never a bag-of-keys dict.
"""

from __future__ import annotations

from dataclasses import dataclass

from .units import Quantity, render


@dataclass(frozen=True)
class EvalResult:
    """Outcome of evaluating one line.

    `assigned_name` is set only when the line was an assignment ("x = ...");
    it lets the GUI know a variable was defined. `kind`/`unit` describe a
    unit-bearing result ("distance"/"km", "pace"/"/km", "time"/None, ...) so the
    GUI can render it; both are None for a plain number, whose `value` is the
    number itself exactly as before. `quantity` is the raw computed value, kept
    so the document layer can carry units through the `$sum` running total.
    A comparison result has `kind` "bool" and its localized word in `text`;
    `quantity` stays None so it never feeds the `$sum` total.
    """

    success: bool
    value: float | None = None
    error: str | None = None
    assigned_name: str | None = None
    kind: str | None = None
    unit: str | None = None
    quantity: Quantity | None = None
    text: str | None = None

    @classmethod
    def ok(cls, value: float, assigned_name: str | None = None) -> EvalResult:
        return cls(success=True, value=value, assigned_name=assigned_name)

    @classmethod
    def fail(cls, message: str) -> EvalResult:
        return cls(success=False, error=message)

    @classmethod
    def from_bool(cls, truth: bool, text: str) -> EvalResult:
        """A comparison outcome: numeric 1/0 plus the localized display word
        (`value` stays a float so every existing None-guard keeps working)."""
        return cls(success=True, value=1.0 if truth else 0.0, kind="bool", text=text)

    @classmethod
    def from_quantity(cls, q: Quantity, assigned_name: str | None = None) -> EvalResult:
        """Build a result from a computed quantity, splitting it into the display
        magnitude plus its `kind`/`unit` labels (and keeping the quantity itself)."""
        value, kind, unit = render(q)
        return cls(
            success=True,
            value=value,
            assigned_name=assigned_name,
            kind=kind,
            unit=unit,
            quantity=q,
        )
