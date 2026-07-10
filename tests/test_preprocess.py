from engine.preprocess import (
    normalize,
    split_assignment,
    strip_label,
    strip_unknown_words,
)


def test_comma_between_digits_becomes_dot() -> None:
    assert normalize("3,5 + 1,5") == "3.5 + 1.5"


def test_standalone_comma_in_function_uses_semicolon() -> None:
    # user separates args with ';'; engine turns it into the ',' ast expects
    assert normalize("min(1;2)") == "min(1,2)"


def test_word_operators_english() -> None:
    assert normalize("5 times 5") == "5 * 5"
    assert normalize("10 divided by 3") == "10 / 3"


def test_dollar_sum_rewritten_to_internal_name() -> None:
    assert normalize("$sum") == "_inline_sum"
    assert normalize("$sum - 5%") == "_inline_sum - _pct(5)"


def test_unknown_dollar_var_is_left_untouched() -> None:
    # Only defined inline vars are rewritten; a stray "$foo" stays for ast.parse
    # to reject as an invalid expression.
    assert normalize("$foo") == "$foo"


def test_word_operators_german() -> None:
    assert normalize("5 mal 5") == "5 * 5"
    assert normalize("10 geteilt durch 2") == "10 / 2"


def test_longest_match_wins_over_shorter() -> None:
    # "divided by" must beat "over"/"by"; "geteilt durch" must beat "durch"
    assert normalize("10 divided by 2") == "10 / 2"
    assert normalize("10 geteilt durch 2") == "10 / 2"


def test_case_insensitive() -> None:
    assert normalize("5 MAL 5") == "5 * 5"
    assert normalize("5 Times 5") == "5 * 5"


def test_power_word_and_caret_become_double_star() -> None:
    assert normalize("2 hoch 3") == "2 ** 3"
    assert normalize("2^3") == "2**3"
    assert normalize("2 to the power of 3") == "2 ** 3"


def test_split_assignment() -> None:
    assert split_assignment("x = 5") == ("x", "5")
    assert split_assignment("longer_name = 2 + 3") == ("longer_name", "2 + 3")


def test_split_assignment_ignores_equality() -> None:
    name, expr = split_assignment("x == 5")
    assert name is None
    assert expr == "x == 5"


def test_split_assignment_plain_expression() -> None:
    assert split_assignment("2 + 3") == (None, "2 + 3")


def test_strip_label_peels_colon_prefix() -> None:
    assert strip_label("Price: 5 + 5") == "5 + 5"
    assert strip_label("Tax: 100 * 1,19") == "100 * 1,19"


def test_strip_label_leaves_plain_and_numeric() -> None:
    assert strip_label("5 + 5") == "5 + 5"
    assert strip_label("12:30") == "12:30"  # no letter -> not a label
    assert strip_label("Notes:") == "Notes:"  # nothing after the colon


def test_strip_unknown_words_drops_units_attached_to_values() -> None:
    assert strip_unknown_words("5 + 5 apples", set()) == "5 + 5 "
    assert strip_unknown_words("5 kg + 5 kg", set()) == "5  + 5 "
    assert strip_unknown_words("pi * 2 meters", {"pi"}) == "pi * 2 "


def test_strip_unknown_words_keeps_operands_and_calls() -> None:
    # operand-position word stays -> the walker still reports "unknown name"
    assert strip_unknown_words("foo + 1", set()) == "foo + 1"
    # followed by '(' -> a call, kept so unknown functions still error
    assert strip_unknown_words("foo(2)", set()) == "foo(2)"
    assert strip_unknown_words("sqrt(2)", {"sqrt"}) == "sqrt(2)"
