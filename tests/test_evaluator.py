import math

import pytest

from engine import evaluate


def _val(expr: str) -> float:
    r = evaluate(expr, {})
    assert r.success, r.error
    assert r.value is not None
    return r.value


def test_basic_operators() -> None:
    assert _val("2 + 3") == 5
    assert _val("10 - 4") == 6
    assert _val("6 * 7") == 42
    assert _val("9 / 2") == 4.5
    assert _val("10 % 3") == 1
    assert _val("2 ^ 8") == 256


def test_percent() -> None:
    assert _val("100 * 19%") == 19
    assert _val("100 + 19%") == 119
    assert _val("100 - 19%") == 81
    assert _val("100 / 50%") == 200
    assert _val("19%") == pytest.approx(0.19)
    assert _val("50%") == 0.5
    assert _val("10 % 3") == 1  # bare modulo still works


def test_x_as_multiply_between_numbers() -> None:
    assert _val("10 x 10") == 100
    assert _val("10x10") == 100
    assert _val("2,5 x 4") == 10


def test_x_stays_a_variable() -> None:
    scope: dict[str, float] = {}
    assert evaluate("x = 10", scope).success
    assert evaluate("x hoch 2", scope).value == 100


def test_precedence_and_parens() -> None:
    assert _val("2 + 3 * 4") == 14
    assert _val("(2 + 3) * 4") == 20


def test_unary_minus() -> None:
    assert _val("-5 + 2") == -3
    assert _val("-(3 + 4)") == -7


def test_functions_and_constants() -> None:
    assert _val("sqrt(16)") == 4
    assert _val("abs(-7)") == 7
    assert _val("min(3;9;1)") == 1
    assert _val("max(3;9;1)") == 9
    assert _val("round(3,7)") == 4
    assert _val("floor(3,9)") == 3
    assert _val("ceil(3,1)") == 4
    assert math.isclose(_val("pi"), math.pi)
    assert math.isclose(_val("ln(e)"), 1.0)


def test_comma_as_decimal() -> None:
    assert _val("3,5 + 1,5") == 5.0


@pytest.mark.parametrize(
    "expr",
    [
        "",
        "   ",
    ],
)
def test_empty_line_fails(expr: str) -> None:
    r = evaluate(expr, {})
    assert not r.success
    assert r.error == "empty"


def test_division_by_zero() -> None:
    r = evaluate("1 / 0", {})
    assert not r.success
    assert r.error == "division by zero"


def test_garbage_is_invalid() -> None:
    r = evaluate("@#$", {})
    assert not r.success


def test_unknown_name() -> None:
    r = evaluate("foo + 1", {})
    assert not r.success
    assert r.error is not None and "unknown name" in r.error


def test_unknown_function() -> None:
    r = evaluate("bar(2)", {})
    assert not r.success
    assert r.error is not None and "unknown function" in r.error


@pytest.mark.parametrize(
    "expr",
    [
        "__import__('os')",
        "(1).__class__",
        "[x for x in range(3)]",
        "lambda: 1",
        "().__class__.__bases__",
        "e.real",
    ],
)
def test_security_rejections(expr: str) -> None:
    r = evaluate(expr, {})
    assert not r.success
