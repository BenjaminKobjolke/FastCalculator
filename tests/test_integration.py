"""End-to-end lines through the public engine, mirroring the plan's table."""

from __future__ import annotations

import math

import pytest

from engine import Scope, evaluate


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("3,5 + 1,5", 5.0),
        ("5 mal 5", 25.0),
        ("sqrt(16)", 4.0),
        ("10 divided by 2", 5.0),
        ("2 to the power of 10", 1024.0),
        ("min(3;9;1)", 1.0),
        ("Price: 5 + 5", 10.0),
        ("Tax: 100 * 1,19", 119.0),
        ("5 + 5 apples", 10.0),
        ("5 kg + 5 kg", 10.0),
    ],
)
def test_lines_produce_expected_values(line: str, expected: float) -> None:
    r = evaluate(line, {})
    assert r.success, r.error
    assert r.value is not None
    assert math.isclose(r.value, expected)


@pytest.mark.parametrize(
    ("line", "value", "kind", "unit"),
    [
        ("10 km", 10.0, "distance", "km"),
        ("400 m", 400.0, "distance", "m"),
        ("50:00 / 10 km", 300.0, "pace", "/km"),  # time ÷ distance = pace (s/km)
        ("4:30 min/km * 42.195 km", 270 * 42.195, "time", None),  # pace × dist = finish
        ("10 km / 50:00", 12.0, "speed", "km/h"),  # distance ÷ time = speed
        ("5 mi + 3 km", (5 * 1609.344 + 3000) / 1000, "distance", "km"),
        ("10 km in mi", 10000 / 1609.344, "distance", "mi"),
        ("5:00 /km in min/mi", 300 * 1.609344, "pace", "/mi"),
        ("12 km/h in mph", 12 / 1.609344, "speed", "mph"),
        ("1:23:45", 5025.0, "time", None),
        ("30 min", 1800.0, "time", None),
        ("1 h 30 min", 5400.0, "time", None),
        ("3:22 * 42 km", 202 * 42, "time", None),  # duration x distance-count = time
        ("3:22 * 42", 202 * 42, "time", None),
    ],
)
def test_running_lines(line: str, value: float, kind: str, unit: str | None) -> None:
    r = evaluate(line, {})
    assert r.success, r.error
    assert r.value is not None and math.isclose(r.value, value)
    assert r.kind == kind
    assert r.unit == unit


def test_unknown_units_still_dimensionless() -> None:
    # kg is not a running unit -> stripped, plain number, no kind/unit
    r = evaluate("5 kg + 5 kg", {})
    assert r.value == 10 and r.kind is None and r.unit is None


def test_incompatible_units_error() -> None:
    r = evaluate("10 km + 5 min", {})
    assert not r.success and r.error == "incompatible units"


def test_distance_variable_roundtrips() -> None:
    scope: Scope = {}
    assert evaluate("d = 10 km", scope).success
    r = evaluate("d in mi", scope)  # variable keeps its unit through scope
    assert r.kind == "distance" and r.unit == "mi"
    assert r.value is not None and math.isclose(r.value, 10000 / 1609.344)


def test_variable_workflow() -> None:
    scope: Scope = {}
    assert evaluate("x = 10", scope).success
    r = evaluate("x hoch 2", scope)
    assert r.value == 100


def test_division_by_zero_message() -> None:
    r = evaluate("10 divided by 0", {})
    assert not r.success
    assert r.error == "division by zero"


def test_german_and_english_mix() -> None:
    scope: Scope = {}
    evaluate("preis = 20", scope)
    r = evaluate("preis minus 5 mal 2", scope)  # 20 - (5*2) = 10
    assert r.value == 10
