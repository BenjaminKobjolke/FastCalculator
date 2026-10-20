"""Tests for radix literal rewriting and output formatting."""

from __future__ import annotations

import pytest

from engine import evaluate
from engine.radix import format_radix, rewrite_radix_literals, split_radix_output


@pytest.mark.parametrize(
    ("literal", "value"),
    [("0xFF", 255), ("0b1010", 10), ("0o17", 15), ("0Xff", 255)],
)
def test_radix_literals_rewrite_to_decimal(literal: str, value: int) -> None:
    assert rewrite_radix_literals(literal) == str(value)


def test_radix_rewrite_does_not_change_multiplication() -> None:
    assert rewrite_radix_literals("10x10") == "10x10"
    assert rewrite_radix_literals("0x10") == "16"


@pytest.mark.parametrize(
    ("value", "base", "expected"),
    [
        (255, "hex", "0xFF"),
        (10, "bin", "0b1010"),
        (15, "oct", "0o17"),
        (-255, "hex", "-0xFF"),
    ],
)
def test_format_radix(value: int, base: str, expected: str) -> None:
    assert format_radix(value, base) == expected


@pytest.mark.parametrize(
    ("text", "expression", "base"),
    [
        ("255 in hex", "255", "hex"),
        ("10 to bin", "10", "bin"),
        ("15 IN OCT", "15", "oct"),
    ],
)
def test_split_radix_output(text: str, expression: str, base: str) -> None:
    assert split_radix_output(text) == (expression, base)


def test_evaluator_returns_radix_text_and_quantity() -> None:
    result = evaluate("255 in hex", {})
    assert result.success and result.kind == "radix"
    assert result.text == "0xFF" and result.value == 255
    assert result.quantity is not None and result.quantity.mag == 255


def test_evaluator_formats_negative_radix_output() -> None:
    result = evaluate("-255 in hex", {})
    assert result.success and result.text == "-0xFF"


@pytest.mark.parametrize("expression", ["1.5 in hex", "5 km in hex"])
def test_evaluator_rejects_non_integer_or_unit_radix_output(expression: str) -> None:
    result = evaluate(expression, {})
    assert not result.success


def test_assignment_preserves_value_and_assignment_name() -> None:
    scope = {}
    result = evaluate("answer = 0xFF", scope)
    assert result.success and result.assigned_name == "answer"
    assert result.value == 255
    assert scope["answer"].mag == 255
