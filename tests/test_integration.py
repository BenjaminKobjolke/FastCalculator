"""End-to-end lines through the public engine, mirroring the plan's table."""

from __future__ import annotations

import math

import pytest

from engine import evaluate


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("3,5 + 1,5", 5.0),
        ("5 mal 5", 25.0),
        ("sqrt(16)", 4.0),
        ("10 divided by 2", 5.0),
        ("2 to the power of 10", 1024.0),
        ("min(3;9;1)", 1.0),
    ],
)
def test_lines_produce_expected_values(line: str, expected: float) -> None:
    r = evaluate(line, {})
    assert r.success, r.error
    assert r.value is not None
    assert math.isclose(r.value, expected)


def test_variable_workflow() -> None:
    scope: dict[str, float] = {}
    assert evaluate("x = 10", scope).success
    r = evaluate("x hoch 2", scope)
    assert r.value == 100


def test_division_by_zero_message() -> None:
    r = evaluate("10 divided by 0", {})
    assert not r.success
    assert r.error == "division by zero"


def test_german_and_english_mix() -> None:
    scope: dict[str, float] = {}
    evaluate("preis = 20", scope)
    r = evaluate("preis minus 5 mal 2", scope)  # 20 - (5*2) = 10
    assert r.value == 10
