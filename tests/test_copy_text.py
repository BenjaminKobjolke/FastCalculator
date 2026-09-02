"""Unit tests for the clipboard text builders (`gui/commands.py`)."""

from __future__ import annotations

from engine import EvalResult
from gui.commands import build_copy_text, last_result_text
from gui.document_evaluator import Style


def test_build_copy_text_pairs_non_empty_success_lines() -> None:
    lines = ["5 mal 5", "", "price = 20", "not math !!"]
    results = [
        EvalResult.ok(25),
        EvalResult.ok(0),  # empty line: skipped because line.strip() == ""
        EvalResult.ok(20, assigned_name="price"),
        EvalResult.fail("syntax"),
    ]
    assert build_copy_text(lines, results) == "5 mal 5 = 25\nprice = 20"


def test_build_copy_text_all_empty() -> None:
    assert build_copy_text(["", "  "], [EvalResult.fail("x"), EvalResult.fail("x")]) == ""


def test_last_result_text_returns_last_success() -> None:
    lines = ["a", "b", "c"]
    results = [EvalResult.ok(1), EvalResult.ok(20), EvalResult.fail("x")]
    assert last_result_text(lines, results) == "20"


def test_last_result_text_empty_when_none_succeed() -> None:
    assert last_result_text(["a"], [EvalResult.fail("x")]) == ""
    assert last_result_text([], []) == ""


def test_last_result_text_rounds_to_input_decimals() -> None:
    # Matches the display: "11.99+19%" shows 14.27, not the raw 14.2681.
    assert last_result_text(["11.99+19%"], [EvalResult.ok(14.2681)]) == "14.27"


def test_build_copy_text_applies_inherited_style() -> None:
    # A "$sum" line inherits the group's ",00" so the clipboard matches the pane.
    lines = ["Angebot: 2000,00", "Discount: $sum - 35%"]
    results = [EvalResult.ok(2000), EvalResult.ok(1300)]
    styles: list[Style | None] = [None, Style(",", 2, grouped=False)]
    assert build_copy_text(lines, results, styles) == (
        "Angebot: 2000,00 = 2000,00\nDiscount: $sum - 35% = 1300,00"
    )


def test_last_result_text_applies_inherited_style() -> None:
    lines = ["Angebot: 2000,00", "Discount: $sum - 35%"]
    results = [EvalResult.ok(2000), EvalResult.ok(1300)]
    styles: list[Style | None] = [None, Style(",", 2, grouped=False)]
    assert last_result_text(lines, results, styles) == "1300,00"


def test_last_result_text_honors_max_decimals() -> None:
    assert last_result_text(["10/3"], [EvalResult.ok(10 / 3)], max_decimals=2) == "3.33"


def test_build_copy_text_renders_bool_text() -> None:
    assert build_copy_text(["5 == 5"], [EvalResult.from_bool(True, "true")]) == "5 == 5 = true"


def test_last_result_text_renders_bool_text() -> None:
    assert last_result_text(["5 ist gleich 5"], [EvalResult.from_bool(True, "wahr")]) == "wahr"


def test_build_copy_text_honors_max_decimals() -> None:
    lines = ["10/3"]
    results = [EvalResult.ok(10 / 3)]
    assert build_copy_text(lines, results, max_decimals=2) == "10/3 = 3.33"
