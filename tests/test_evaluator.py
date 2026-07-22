import math

import pytest

from engine import Scope, evaluate


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
    scope: Scope = {}
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


def test_colon_label_prefix() -> None:
    assert _val("Price: 5 + 5") == 10
    assert _val("Tax: 100 * 1,19") == 119


def test_trailing_unit_text() -> None:
    assert _val("5 + 5 apples") == 10
    assert _val("5 kg + 5 kg") == 10


def test_unit_text_keeps_scope_variables() -> None:
    scope: Scope = {}
    assert evaluate("x = 5", scope).success
    assert evaluate("x + 3 dollars", scope).value == 8


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
        "(1 == 1) + 1",  # Compare nested in arithmetic
        "1 < 2 < 3",  # chained comparison
        "pi is e",  # identity op
        "-(1 == 1)",  # Compare under unary op
        "sqrt(1 == 1)",  # Compare as call argument
    ],
)
def test_security_rejections(expr: str) -> None:
    r = evaluate(expr, {})
    assert not r.success


def _bool_text(expr: str, scope: Scope | None = None) -> str:
    r = evaluate(expr, scope if scope is not None else {})
    assert r.success, r.error
    assert r.kind == "bool"
    assert r.text is not None
    return r.text


def test_comparison_operators() -> None:
    assert _bool_text("5 == 5") == "true"
    assert _bool_text("5 == 3") == "false"
    assert _bool_text("5 != 3") == "true"
    assert _bool_text("3 < 5") == "true"
    assert _bool_text("3 > 5") == "false"
    assert _bool_text("5 <= 5") == "true"
    assert _bool_text("4 >= 5") == "false"


def test_comparison_of_variables() -> None:
    scope: Scope = {}
    assert evaluate("helena = 3000", scope).success
    assert evaluate("benni = 3000", scope).success
    assert _bool_text("helena == benni", scope) == "true"


def test_single_equals_still_assigns() -> None:
    scope: Scope = {}
    assert evaluate("helena = 5", scope).success
    assert evaluate("benni = 7", scope).success
    r = evaluate("helena = benni", scope)
    assert r.success and r.assigned_name == "helena" and r.value == 7


def test_comparison_word_operators() -> None:
    assert _bool_text("5 equals 5") == "true"
    assert _bool_text("5 ist gleich 5") == "wahr"
    assert _bool_text("5 ist gleich 3") == "falsch"


def test_comparison_is_unit_aware() -> None:
    assert _bool_text("5 km == 5000 m") == "true"
    assert _bool_text("50:00 == 50 min") == "true"
    assert _bool_text("19% == 0,19") == "true"


def test_comparison_float_tolerance() -> None:
    assert _bool_text("0,1 + 0,2 == 0,3") == "true"


def test_comparison_incompatible_units_fails() -> None:
    r = evaluate("5 km == 5", {})
    assert not r.success
    assert r.error is not None and "incompatible units" in r.error


def test_comparison_unknown_name_fails() -> None:
    r = evaluate("helena == 5", {})
    assert not r.success
    assert r.error is not None and "unknown name" in r.error


def test_cannot_assign_a_comparison() -> None:
    r = evaluate("x = 5 == 5", {})
    assert not r.success
    assert r.error is not None and "cannot assign a comparison" in r.error


def test_chained_comparison_rejected() -> None:
    r = evaluate("1 < 2 < 3", {})
    assert not r.success
    assert r.error is not None and "chained" in r.error
