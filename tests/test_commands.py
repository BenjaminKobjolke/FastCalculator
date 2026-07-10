"""Unit tests for the Qt-free slash-command logic (`gui/commands.py`)."""

from __future__ import annotations

from engine import EvalResult
from gui.commands import (
    build_copy_text,
    command_at,
    common_prefix,
    last_result_text,
    parse_command,
    parse_command_line,
    suggest,
)


def test_command_at_start_of_line() -> None:
    assert command_at("/cle", 4) == "/cle"


def test_command_at_mid_line() -> None:
    assert command_at("105+ /pas", 9) == "/pas"


def test_command_at_no_space_before_slash() -> None:
    assert command_at("81+/pas", 7) == "/pas"


def test_command_at_division_slash_returns_non_command() -> None:
    # "/5" is picked up but suggest()/parse_command() reject it, so no false run.
    assert command_at("100/5", 5) == "/5"
    assert parse_command(command_at("100/5", 5) or "") is None


def test_command_at_full_command_mid_line() -> None:
    text = "price = /paste-last-result"
    assert command_at(text, len(text)) == "/paste-last-result"


def test_command_at_non_slash_word_is_none() -> None:
    assert command_at("5 + 5", 5) is None


def test_command_at_trailing_space_is_none() -> None:
    assert command_at("/copy ", 6) is None


def test_command_at_empty_is_none() -> None:
    assert command_at("", 0) is None


def test_suggest_single_letter_matches_all() -> None:
    assert suggest("/c") == ["/clear", "/copy", "/copy-last"]


def test_suggest_exit() -> None:
    assert suggest("/e") == ["/exit"]


def test_suggest_paste_last_result() -> None:
    assert suggest("/p") == ["/paste-last-result"]


def test_common_prefix_window_family_extends_to_dash() -> None:
    assert common_prefix(suggest("/win")) == "/window-"


def test_common_prefix_copy_family_cannot_extend() -> None:
    # LCP already equals what's typed -> Tab opens the list instead of filling.
    assert common_prefix(suggest("/c")) == "/c"


def test_common_prefix_single_match_is_full_command() -> None:
    assert common_prefix(suggest("/e")) == "/exit"


def test_common_prefix_empty() -> None:
    assert common_prefix([]) == ""


def test_common_prefix_copy_narrowed() -> None:
    assert common_prefix(suggest("/copy")) == "/copy"


def test_parse_command_exact_paste_last_result() -> None:
    assert parse_command("/paste-last-result") == "/paste-last-result"


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


def test_parse_command_line_with_arg() -> None:
    assert parse_command_line("/window-opacity 80") == ("/window-opacity", "80")


def test_parse_command_line_no_arg() -> None:
    assert parse_command_line("/window-title") == ("/window-title", "")


def test_parse_command_line_non_command() -> None:
    assert parse_command_line("5 + 5") is None
    assert parse_command_line("100/5") is None


def test_parse_command_line_unknown_slash() -> None:
    assert parse_command_line("/nope 1") is None


def test_parse_command_line_is_case_insensitive() -> None:
    assert parse_command_line("/WINDOW-OPACITY 80") == ("/window-opacity", "80")


def test_suggest_window_family() -> None:
    assert suggest("/window") == [
        "/window-opacity",
        "/window-title",
        "/window-background-color",
        "/window-font-color",
        "/window-theme",
        "/window-margin",
        "/window-highlighting",
        "/window-number-color",
        "/window-operator-color",
        "/window-function-color",
        "/window-variable-color",
        "/window-inline-color",
    ]


def test_suggest_syntax_color_family() -> None:
    # /window-op* is shared with /window-opacity, so disambiguation needs a 4th char.
    assert suggest("/window-n") == ["/window-number-color"]
    assert suggest("/window-ope") == ["/window-operator-color"]
    assert suggest("/window-fu") == ["/window-function-color"]
    assert suggest("/window-v") == ["/window-variable-color"]
    assert suggest("/window-h") == ["/window-highlighting"]
    assert suggest("/window-i") == ["/window-inline-color"]


def test_suggest_inline_variable() -> None:
    assert suggest("$") == ["$sum"]
    assert suggest("$su") == ["$sum"]
    assert suggest("$SUM") == ["$sum"]  # case-insensitive


def test_suggest_unknown_inline_variable_is_empty() -> None:
    assert suggest("$foo") == []


def test_command_at_dollar_token_mid_expression() -> None:
    assert command_at("Rabatt: $su", len("Rabatt: $su")) == "$su"
    assert command_at("2000 + $sum", len("2000 + $sum")) == "$sum"


def test_command_at_dollar_no_space_before() -> None:
    assert command_at("2000+$su", len("2000+$su")) == "$su"


def test_parse_command_line_inline_color() -> None:
    assert parse_command_line("/window-inline-color #ffb86c") == (
        "/window-inline-color",
        "#ffb86c",
    )


def test_parse_command_line_syntax_color() -> None:
    assert parse_command_line("/window-number-color #ffb86c") == (
        "/window-number-color",
        "#ffb86c",
    )


def test_parse_command_line_highlighting_toggle() -> None:
    assert parse_command_line("/window-highlighting off") == ("/window-highlighting", "off")


def test_parse_command_line_margin() -> None:
    assert parse_command_line("/window-margin 12") == ("/window-margin", "12")


def test_suggest_margin() -> None:
    assert suggest("/window-m") == ["/window-margin"]


def test_parse_command_line_color_with_hex() -> None:
    assert parse_command_line("/window-background-color #282a36") == (
        "/window-background-color",
        "#282a36",
    )


def test_suggest_background_color() -> None:
    assert suggest("/window-b") == ["/window-background-color"]


def test_suggest_font_color() -> None:
    # /window-f is shared with /window-function-color, so it needs a 4th char.
    assert suggest("/window-fo") == ["/window-font-color"]


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
    lines = ["a", "b", "c"]
    results = [EvalResult.ok(1), EvalResult.ok(20), EvalResult.fail("x")]
    assert last_result_text(lines, results) == "20"


def test_last_result_text_empty_when_none_succeed() -> None:
    assert last_result_text(["a"], [EvalResult.fail("x")]) == ""
    assert last_result_text([], []) == ""


def test_last_result_text_rounds_to_input_decimals() -> None:
    # Matches the display: "11.99+19%" shows 14.27, not the raw 14.2681.
    assert last_result_text(["11.99+19%"], [EvalResult.ok(14.2681)]) == "14.27"
