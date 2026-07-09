"""Unit tests for the Qt-free slash-command logic (`gui/commands.py`)."""

from __future__ import annotations

from engine import EvalResult
from gui.commands import (
    COMMANDS,
    build_copy_text,
    last_result_text,
    parse_command,
    suggest,
)


def test_suggest_single_letter_matches_all() -> None:
    assert suggest("/c") == ["/clear", "/copy", "/copy-last"]


def test_suggest_exit() -> None:
    assert suggest("/e") == ["/exit"]


def test_parse_command_exact_exit() -> None:
    assert parse_command("/exit") == "/exit"


def test_suggest_narrows_to_copy_family() -> None:
    assert suggest("/copy") == ["/copy", "/copy-last"]


def test_suggest_unknown_prefix_is_empty() -> None:
    assert suggest("/x") == []


def test_suggest_without_leading_slash_is_empty() -> None:
    assert suggest("5 + 5") == []
    assert suggest("") == []


def test_suggest_is_case_insensitive() -> None:
    assert suggest("/CL") == ["/clear"]


def test_suggest_full_command_still_suggests_itself() -> None:
    assert suggest("/clear") == ["/clear"]


def test_parse_command_trims_whitespace() -> None:
    assert parse_command("  /clear ") == "/clear"


def test_parse_command_rejects_partial() -> None:
    assert parse_command("/copyx") is None
    assert parse_command("/cop") is None


def test_parse_command_exact_copy() -> None:
    assert parse_command("/copy") == "/copy"


def test_parse_command_non_command_line() -> None:
    assert parse_command("5 mal 5") is None


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
    results = [EvalResult.ok(1), EvalResult.ok(20), EvalResult.fail("x")]
    assert last_result_text(results) == "20"


def test_last_result_text_empty_when_none_succeed() -> None:
    assert last_result_text([EvalResult.fail("x")]) == ""
    assert last_result_text([]) == ""
