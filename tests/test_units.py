"""Unit tests for the Quantity value type and its dimensional algebra."""

from __future__ import annotations

import ast
import math

import pytest

from engine.errors import IncompatibleUnitsError, UnsafeExpressionError
from engine.units import (
    DIMLESS,
    LENGTH,
    PACE,
    SPEED,
    TIME,
    UNITS,
    Quantity,
    apply_binop,
    convert,
    dimensionless,
    render,
    require_number,
    unit_quantity,
)


def test_dimensionless_equals_plain_number() -> None:
    assert dimensionless(10) == 10
    assert dimensionless(2.5) == 2.5
    # A dimensioned quantity is never equal to a bare number, even same magnitude.
    assert unit_quantity(UNITS["km"]) != 1000


def test_unit_quantity_is_canonical() -> None:
    km = unit_quantity(UNITS["km"])
    assert km.mag == 1000.0 and km.dim == LENGTH
    mi = unit_quantity(UNITS["mi"])
    assert mi.dim == LENGTH and math.isclose(mi.mag, 1609.344)


def test_multiply_number_by_unit_keeps_unit() -> None:
    q = apply_binop(ast.Mult, dimensionless(10), unit_quantity(UNITS["km"]))
    assert q.dim == LENGTH and q.mag == 10000.0
    assert q.unit is UNITS["km"]


def test_add_requires_same_dimension() -> None:
    a = apply_binop(ast.Mult, dimensionless(5), unit_quantity(UNITS["mi"]))
    b = apply_binop(ast.Mult, dimensionless(3), unit_quantity(UNITS["km"]))
    s = apply_binop(ast.Add, a, b)  # 5 mi + 3 km
    assert s.dim == LENGTH
    assert math.isclose(s.mag, 5 * 1609.344 + 3000)
    assert s.unit is UNITS["km"]  # right operand's unit wins the display


def test_add_incompatible_dimensions_raises() -> None:
    length = unit_quantity(UNITS["km"])
    time = unit_quantity(UNITS["min"])
    with pytest.raises(IncompatibleUnitsError):
        apply_binop(ast.Add, length, time)


def test_time_over_distance_is_pace() -> None:
    time = Quantity(3000.0, TIME)  # 50:00
    dist = apply_binop(ast.Mult, dimensionless(10), unit_quantity(UNITS["km"]))
    pace = apply_binop(ast.Div, time, dist)
    assert pace.dim == PACE
    value, kind, unit = render(pace)
    assert kind == "pace" and unit == "/km"
    assert math.isclose(value, 300.0)  # 300 s/km == 5:00 /km


def test_distance_over_time_is_speed() -> None:
    dist = apply_binop(ast.Mult, dimensionless(10), unit_quantity(UNITS["km"]))
    time = Quantity(3000.0, TIME)
    speed = apply_binop(ast.Div, dist, time)
    assert speed.dim == SPEED
    value, kind, unit = render(speed)
    assert kind == "speed" and unit == "km/h"
    assert math.isclose(value, 12.0)


def test_pace_times_distance_is_time() -> None:
    pace = Quantity(0.27, PACE)  # 4:30 /km == 270 s/km == 0.27 s/m
    dist = apply_binop(ast.Mult, dimensionless(42.195), unit_quantity(UNITS["km"]))
    finish = apply_binop(ast.Mult, pace, dist)
    assert finish.dim == TIME
    value, kind, _ = render(finish)
    assert kind == "time"
    assert math.isclose(value, 0.27 * 42195)


def test_time_times_distance_is_scaled_time() -> None:
    t = Quantity(202.0, TIME)  # 3:22
    d = apply_binop(ast.Mult, dimensionless(42), unit_quantity(UNITS["km"]))
    result = apply_binop(ast.Mult, t, d)
    assert result.dim == TIME
    assert math.isclose(result.mag, 202 * 42)
    # order-independent
    assert apply_binop(ast.Mult, d, t).mag == result.mag
    # distance unit is just the count: mi gives the same as km here
    d_mi = apply_binop(ast.Mult, dimensionless(42), unit_quantity(UNITS["mi"]))
    assert math.isclose(apply_binop(ast.Mult, t, d_mi).mag, 202 * 42)


def test_percent_add_on_number() -> None:
    pct = Quantity(0.19, DIMLESS, percent=True)
    assert apply_binop(ast.Add, dimensionless(100), pct) == 119
    assert apply_binop(ast.Sub, dimensionless(100), pct) == 81


def test_pow_and_mod_require_plain_numbers() -> None:
    assert apply_binop(ast.Pow, dimensionless(2), dimensionless(8)) == 256
    assert apply_binop(ast.Mod, dimensionless(10), dimensionless(3)) == 1
    with pytest.raises(UnsafeExpressionError):
        apply_binop(ast.Pow, unit_quantity(UNITS["km"]), dimensionless(2))


def test_division_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        apply_binop(ast.Div, dimensionless(1), dimensionless(0))


def test_require_number_rejects_units() -> None:
    assert require_number(dimensionless(7)) == 7
    with pytest.raises(UnsafeExpressionError):
        require_number(unit_quantity(UNITS["km"]))


def test_convert_relabels_display_unit() -> None:
    ten_km = apply_binop(ast.Mult, dimensionless(10), unit_quantity(UNITS["km"]))
    as_mi = convert(ten_km, unit_quantity(UNITS["mi"]))
    value, kind, unit = render(as_mi)
    assert kind == "distance" and unit == "mi"
    assert math.isclose(value, 10000 / 1609.344)


def test_convert_rejects_cross_dimension() -> None:
    ten_km = apply_binop(ast.Mult, dimensionless(10), unit_quantity(UNITS["km"]))
    with pytest.raises(IncompatibleUnitsError):
        convert(ten_km, unit_quantity(UNITS["min"]))


def test_render_dimensionless_has_no_unit() -> None:
    assert render(dimensionless(42)) == (42.0, None, None)
