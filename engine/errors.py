"""Engine-internal exceptions.

These NEVER leak to the GUI: `evaluate()` catches them and converts to an
`EvalResult.fail(...)`. Keeping them here documents the failure modes in one place.
"""

from __future__ import annotations


class EngineError(Exception):
    """Base for all engine-internal errors."""


class EmptyLineError(EngineError):
    """Line was blank after trimming."""


class UnsafeExpressionError(EngineError):
    """Expression contained a node type outside the whitelist."""


class UnknownNameError(EngineError):
    """A variable or constant name could not be resolved."""


class UnknownFunctionError(EngineError):
    """A function call referenced a name outside the whitelist."""
