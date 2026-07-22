"""Unit/dimension-tracking value type for the calculator engine.

Pure stdlib, no GUI. A `Quantity` carries a magnitude in *canonical base units*
(meter, second) plus a dimension `(length_exp, time_exp)`. Plain numbers are
dimensionless quantities that compare numerically equal to a `float`, so the
engine and its callers keep working as if values were still floats.

Units are the single source of truth in `UNITS`; the evaluator resolves a unit
word (e.g. `km`) to a magnitude-1 `Quantity` of that unit, exactly like a
constant. Nothing here touches the AST — units never become strings, so the
whitelist walker (the security boundary) is unchanged.
"""

from __future__ import annotations

import ast
import math
import operator
from collections.abc import Callable
from dataclasses import dataclass

from .errors import IncompatibleUnitsError, UnsafeExpressionError

# Dimension = integer exponents over the base dimensions (length, time).
Dim = tuple[int, int]
DIMLESS: Dim = (0, 0)
LENGTH: Dim = (1, 0)
TIME: Dim = (0, 1)
SPEED: Dim = (1, -1)  # length / time
PACE: Dim = (-1, 1)  # time / length


@dataclass(frozen=True)
class Unit:
    """A named display unit. `canonical = display_magnitude * factor`.

    `kind` is the display category the GUI branches on ("distance", "time",
    "speed", "pace"); `dim` is the physical dimension used for the algebra.
    """

    name: str
    factor: float
    dim: Dim
    kind: str


# Input unit words (resolved like CONSTANTS) and conversion targets. Every key
# becomes a reserved name that shadows a would-be variable of the same spelling.
UNITS: dict[str, Unit] = {
    # distance (canonical: meter)
    "m": Unit("m", 1.0, LENGTH, "distance"),
    "km": Unit("km", 1000.0, LENGTH, "distance"),
    "mi": Unit("mi", 1609.344, LENGTH, "distance"),
    # time (canonical: second) — also enterable as mm:ss / h:mm:ss literals
    "s": Unit("s", 1.0, TIME, "time"),
    "min": Unit("min", 60.0, TIME, "time"),  # dual role: also the min() function (Call)
    "h": Unit("h", 3600.0, TIME, "time"),
    # speed (canonical: m/s) — input words and conversion targets
    "kmh": Unit("km/h", 1000.0 / 3600.0, SPEED, "speed"),
    "mph": Unit("mph", 1609.344 / 3600.0, SPEED, "speed"),
    # pace (canonical: s/m) — conversion targets; input pace comes from time/distance
    "_pace_km": Unit("/km", 1.0 / 1000.0, PACE, "pace"),
    "_pace_mi": Unit("/mi", 1.0 / 1609.344, PACE, "pace"),
}

# Default display unit per dimension when a quantity carries none of its own.
_DEFAULT_UNIT: dict[Dim, Unit] = {
    LENGTH: UNITS["km"],
    SPEED: UNITS["kmh"],
    PACE: UNITS["_pace_km"],
}


@dataclass(frozen=True, eq=False)
class Quantity:
    """A magnitude in canonical base units, tagged with a dimension.

    `unit` is the preferred display unit (mostly for length/speed/pace); `None`
    means "use the dimension's default". `percent` marks a `%` literal (always
    dimensionless) so add/sub can apply the Numi "100 + 19%" rule.
    """

    mag: float
    dim: Dim = DIMLESS
    unit: Unit | None = None
    percent: bool = False

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Quantity):
            return self.mag == other.mag and self.dim == other.dim
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            # Backward compat: a dimensionless quantity IS its number.
            return self.dim == DIMLESS and self.mag == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.mag, self.dim))


def dimensionless(value: float) -> Quantity:
    """Wrap a plain number as a dimensionless quantity."""
    return Quantity(float(value), DIMLESS)


def unit_quantity(unit: Unit) -> Quantity:
    """The value a bare unit word resolves to: 1 unit in canonical terms."""
    return Quantity(unit.factor, unit.dim, unit)


def require_number(q: Quantity) -> float:
    """Magnitude of a dimensionless quantity, or reject (functions take numbers)."""
    if q.dim != DIMLESS:
        raise UnsafeExpressionError("functions require plain numbers")
    return q.mag


def _add_dims(a: Dim, b: Dim) -> Dim:
    return (a[0] + b[0], a[1] + b[1])


def _sub_dims(a: Dim, b: Dim) -> Dim:
    return (a[0] - b[0], a[1] - b[1])


def _pick_unit(dim: Dim, left: Quantity, right: Quantity) -> Unit | None:
    """Display unit for a product/quotient: whichever operand shares the result
    dimension keeps its unit (so `10 * km` stays km); composites carry none."""
    if left.dim == dim and left.unit is not None:
        return left.unit
    if right.dim == dim and right.unit is not None:
        return right.unit
    return None


def _require_dimless(left: Quantity, right: Quantity) -> None:
    if left.dim != DIMLESS or right.dim != DIMLESS:
        raise UnsafeExpressionError("powers and modulo require plain numbers")


def _add_sub(op: type[ast.operator], left: Quantity, right: Quantity) -> Quantity:
    if right.percent:  # Numi percent: "100 + 19%" == 100 + 19% of 100
        delta = left.mag * right.mag
        mag = left.mag + delta if op is ast.Add else left.mag - delta
        return Quantity(mag, left.dim, left.unit)
    if left.dim != right.dim:
        raise IncompatibleUnitsError("incompatible units")
    mag = left.mag + right.mag if op is ast.Add else left.mag - right.mag
    return Quantity(mag, left.dim, right.unit or left.unit)


def _time_times_distance(a: Quantity, b: Quantity) -> Quantity | None:
    """A duration times a distance = the duration repeated per unit of that
    distance ("3:22 * 42 km" == 3:22 x 42 = 2:21:24). Result is a time; the
    distance's number (in its own unit) is the multiplier count. Order-independent.
    Without this, `time * distance` would be a meaningless (length, time) value."""
    for t, d in ((a, b), (b, a)):
        if t.dim == TIME and d.dim == LENGTH:
            return Quantity(t.mag * render(d)[0], TIME)
    return None


def apply_binop(op: type[ast.operator], left: Quantity, right: Quantity) -> Quantity:
    """Dimensional algebra for one binary operation. Raises on unit mismatch or
    an unsupported operator (the walker relies on that to stay strict)."""
    if op is ast.Add or op is ast.Sub:
        return _add_sub(op, left, right)
    if op is ast.Mult:
        scaled = _time_times_distance(left, right)
        if scaled is not None:
            return scaled
        dim = _add_dims(left.dim, right.dim)
        return Quantity(left.mag * right.mag, dim, _pick_unit(dim, left, right))
    if op is ast.Div:
        if right.mag == 0:
            raise ZeroDivisionError("division by zero")
        dim = _sub_dims(left.dim, right.dim)
        return Quantity(left.mag / right.mag, dim, _pick_unit(dim, left, right))
    if op is ast.Pow:
        _require_dimless(left, right)
        return dimensionless(left.mag**right.mag)
    if op is ast.Mod:
        _require_dimless(left, right)
        return dimensionless(left.mag % right.mag)
    raise UnsafeExpressionError("unsupported operator")


_COMPARERS: dict[type[ast.cmpop], Callable[[float, float], bool]] = {
    ast.Lt: operator.lt,
    ast.Gt: operator.gt,
    ast.LtE: operator.le,
    ast.GtE: operator.ge,
}


def compare(op: type[ast.cmpop], left: Quantity, right: Quantity) -> bool:
    """One comparison over same-dimension quantities ("5 km == 5000 m").

    Magnitudes are canonical, so no conversion is needed. Equality tolerates
    float noise via `isclose` (0.1 + 0.2 == 0.3 is true). The percent flag is
    deliberately ignored — comparisons never apply the Numi "+19%" rule, which
    is why this does not reuse `apply_binop(Sub)`.
    """
    if left.dim != right.dim:
        raise IncompatibleUnitsError("incompatible units")
    if op is ast.Eq or op is ast.NotEq:
        eq = math.isclose(left.mag, right.mag, rel_tol=1e-9, abs_tol=1e-12)
        return eq if op is ast.Eq else not eq
    fn = _COMPARERS.get(op)
    if fn is None:
        raise UnsafeExpressionError("unsupported comparison")
    return fn(left.mag, right.mag)


def convert(q: Quantity, target: Quantity) -> Quantity:
    """Re-express `q` in `target`'s unit (same dimension), for `X in <unit>`."""
    if q.dim != target.dim or target.unit is None:
        raise IncompatibleUnitsError("incompatible units")
    return Quantity(q.mag, q.dim, target.unit)


def render(q: Quantity) -> tuple[float, str | None, str | None]:
    """`(display_magnitude, kind, unit_label)` for the GUI.

    Dimensionless and time results carry no unit label (time is formatted from
    seconds); everything else is divided into its display unit. `kind` is None
    for a plain number, so the GUI keeps its existing decimal-style path.
    """
    if q.dim == DIMLESS:
        return (q.mag, None, None)
    if q.dim == TIME:
        return (q.mag, "time", None)
    unit = q.unit or _DEFAULT_UNIT.get(q.dim)
    if unit is None:  # composite dimension with no default (e.g. area) — raw number
        return (q.mag, None, None)
    return (q.mag / unit.factor, unit.kind, unit.name)
