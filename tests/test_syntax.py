"""Unit tests for the Qt-free syntax tokenizer (`gui/syntax.py`)."""

from __future__ import annotations

from gui.syntax import tokenize


def _cats(line: str) -> list[tuple[str, str]]:
    """(text, category) pairs for readable assertions."""
    return [(line[start : start + length], cat) for start, length, cat in tokenize(line)]


def test_number_operator_number() -> None:
    assert _cats("5 mal 5") == [("5", "number"), ("mal", "operator"), ("5", "number")]


def test_decimals_and_percent() -> None:
    assert _cats("100,00 + 19%") == [
        ("100,00", "number"),
        ("+", "operator"),
        ("19%", "number"),
    ]


def test_assignment() -> None:
    assert _cats("price = 20") == [
        ("price", "variable"),
        ("=", "operator"),
        ("20", "number"),
    ]


def test_function_and_constant() -> None:
    assert _cats("sqrt(16) + pi") == [
        ("sqrt", "function"),
        ("16", "number"),
        ("+", "operator"),
        ("pi", "function"),
    ]


def test_variable_with_word_operator() -> None:
    assert _cats("x hoch 2") == [
        ("x", "variable"),
        ("hoch", "operator"),
        ("2", "number"),
    ]


def test_multiword_operator_is_one_token() -> None:
    # Longest-first: "divided by" wins over "over"/"by".
    assert _cats("10 divided by 2") == [
        ("10", "number"),
        ("divided by", "operator"),
        ("2", "number"),
    ]


def test_command_line_has_no_tokens() -> None:
    assert tokenize("/clear") == []


def test_word_operator_is_case_insensitive() -> None:
    assert _cats("5 MAL 5") == [("5", "number"), ("MAL", "operator"), ("5", "number")]


def test_identifier_containing_operator_word_stays_variable() -> None:
    # "plusval" must not match the "plus" word operator (\b anchors).
    assert _cats("plusval") == [("plusval", "variable")]


def test_dollar_variable_is_one_inline_token() -> None:
    # "$sum" is a single `inline` span, not "$" + a plain `variable` "sum".
    assert _cats("$sum") == [("$sum", "inline")]


def test_dollar_variable_in_expression() -> None:
    assert _cats("$sum - 5%") == [
        ("$sum", "inline"),
        ("-", "operator"),
        ("5%", "number"),
    ]


def test_comparison_symbols_are_operators() -> None:
    assert _cats("5 < 3") == [("5", "number"), ("<", "operator"), ("3", "number")]
    assert _cats("5 != 3") == [
        ("5", "number"),
        ("!", "operator"),
        ("=", "operator"),
        ("3", "number"),
    ]


def test_comparison_words_are_operators() -> None:
    assert _cats("5 equals 5") == [("5", "number"), ("equals", "operator"), ("5", "number")]
    assert _cats("5 ist gleich 5") == [
        ("5", "number"),
        ("ist gleich", "operator"),
        ("5", "number"),
    ]


def test_grouped_number_is_one_token() -> None:
    assert _cats("34.234,89 + 19%") == [
        ("34.234,89", "number"),
        ("+", "operator"),
        ("19%", "number"),
    ]
