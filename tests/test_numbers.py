"""Unit tests for thousands-separator handling (`engine/numbers.py`)."""

from __future__ import annotations

import pytest

from engine.numbers import grouping_separator, strip_grouping


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Unambiguous: a group plus a decimal part using the other separator.
        ("34.234,89", "34234.89"),
        ("34,234.89", "34234.89"),
        ("1.234.567,89", "1234567.89"),
        ("1,234,567.89", "1234567.89"),
        # Unambiguous: two or more groups, no decimal part.
        ("1.234.567", "1234567"),
        ("1,234,567", "1234567"),
        # Ambiguous single group -> left for the plain decimal rules.
        ("1.000", "1.000"),
        ("1,000", "1,000"),
        ("3,5", "3,5"),
        ("3.5", "3.5"),
        # Not a group at all: the run after the separator is not exactly 3 digits.
        ("1.2345", "1.2345"),
        ("1.23", "1.23"),
    ],
)
def test_strip_grouping_table(raw: str, expected: str) -> None:
    assert strip_grouping(raw) == expected


def test_grouping_inside_an_expression() -> None:
    assert strip_grouping("34.234,89 + 19% - 1.000") == "34234.89 + 19% - 1.000"


def test_negative_amount_keeps_its_sign() -> None:
    assert strip_grouping("-1.234,50") == "-1234.50"


def test_semicolon_arguments_are_not_grouping() -> None:
    # The ';' -> ',' rewrite happens later in normalize(), so this must run first.
    assert strip_grouping("min(1;234;567)") == "min(1;234;567)"


def test_time_literal_untouched() -> None:
    assert strip_grouping("12:30 + 1:45") == "12:30 + 1:45"


def test_modulo_untouched() -> None:
    assert strip_grouping("10 % 3") == "10 % 3"


@pytest.mark.parametrize(
    ("line", "separator"),
    [
        ("34.234,89", "."),
        ("34,234.89", ","),
        ("1.234.567", "."),
        ("1,234,567", ","),
        ("1.000", None),
        ("3,5", None),
        ("100 + 19%", None),
    ],
)
def test_grouping_separator(line: str, separator: str | None) -> None:
    assert grouping_separator(line) == separator
