from engine.preprocess import (
    has_inline_var,
    normalize,
    split_assignment,
    strip_label,
    strip_unknown_words,
    uses_german_comparison,
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


def test_has_inline_var_detects_defined_names() -> None:
    assert has_inline_var("$sum - 5%") is True
    assert has_inline_var("2000 + $sum") is True
    assert has_inline_var("$foo") is False  # not a defined inline var
    assert has_inline_var("5 + 5") is False


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
    assert strip_unknown_words("5 + 5 apples", set()).expr == "5 + 5 "
    assert strip_unknown_words("5 kg + 5 kg", set()).expr == "5  + 5 "
    assert strip_unknown_words("pi * 2 meters", {"pi"}).expr == "pi * 2 "


def test_strip_unknown_words_reports_what_it_dropped() -> None:
    assert strip_unknown_words("5 + 5 apples", set()).dropped == ("apples",)
    assert strip_unknown_words("5 kg + 5 kg", set()).dropped == ("kg", "kg")
    assert strip_unknown_words("2 + 2", set()).dropped == ()


def test_strip_unknown_words_keeps_operands_and_calls() -> None:
    # operand-position word stays -> the walker still reports "unknown name"
    assert strip_unknown_words("foo + 1", set()).expr == "foo + 1"
    # followed by '(' -> a call, kept so unknown functions still error
    assert strip_unknown_words("foo(2)", set()).expr == "foo(2)"
    assert strip_unknown_words("sqrt(2)", {"sqrt"}).expr == "sqrt(2)"
    assert strip_unknown_words("foo + 1", set()).dropped == ()


def test_time_literal_mm_ss() -> None:
    assert normalize("4:30") == "_time(270)"
    assert normalize("50:00") == "_time(3000)"
    assert normalize("12:30") == "_time(750)"


def test_time_literal_h_mm_ss() -> None:
    assert normalize("1:23:45") == "_time(5025)"


def test_unit_word_becomes_parenthesized_quantity() -> None:
    assert normalize("10 km") == "(10 * km)"
    assert normalize("42,195 km") == "(42.195 * km)"
    assert normalize("5 miles") == "(5 * mi)"
    assert normalize("30 km/h") == "(30 * kmh)"
    assert normalize("400 m") == "(400 * m)"


def test_durations_and_adjacency() -> None:
    assert normalize("30 min") == "(30 * min)"
    assert normalize("1 h 30 min") == "(1 * h) + (30 * min)"


def test_unknown_unit_stays_bare_for_stripping() -> None:
    # kg is not a known unit -> left bare so strip_unknown_words drops it later
    assert normalize("5 kg") == "5 kg"


def test_pace_suffix_is_division_by_unit() -> None:
    assert normalize("50:00 / 10 km") == "_time(3000) / (10 * km)"
    assert normalize("4:30 min/km") == "_time(270) / km"
    assert normalize("5:00 /km") == "_time(300) / km"


def test_speed_slash_is_ordinary_division() -> None:
    assert normalize("10 km / 50:00") == "(10 * km) / _time(3000)"


def test_conversion_wraps_in_to_call() -> None:
    assert normalize("10 km in mi") == "_to((10 * km), mi)"
    assert normalize("10 km to mi") == "_to((10 * km), mi)"
    assert normalize("12 km/h in mph") == "_to((12 * kmh), mph)"
    assert normalize("5:00 /km in min/mi") == "_to(_time(300) / km, _pace_mi)"


def test_comparison_word_operators() -> None:
    assert normalize("5 equals 5") == "5 == 5"
    assert normalize("5 ist gleich 5") == "5 == 5"
    assert normalize("5 IST GLEICH 5") == "5 == 5"


def test_split_assignment_keeps_comparison_rhs() -> None:
    assert split_assignment("a == b") == (None, "a == b")
    # "x = a == b" splits as an assignment; the evaluator rejects it later.
    assert split_assignment("x = a == b") == ("x", "a == b")


def test_uses_german_comparison() -> None:
    assert uses_german_comparison("helena ist gleich benni") is True
    assert uses_german_comparison("5 Ist Gleich 3") is True
    assert uses_german_comparison("a == b") is False
    assert uses_german_comparison("5 equals 5") is False


def test_conversion_keyword_does_not_match_inside_min() -> None:
    # the 'in' inside 'min' must never be read as the conversion keyword
    assert normalize("min(1;2)") == "min(1,2)"


def test_german_grouped_amount_with_percent() -> None:
    assert normalize("34.234,89 + 19%") == "34234.89 + _pct(19)"


def test_english_grouped_amount() -> None:
    assert normalize("34,234.89 * 2") == "34234.89 * 2"


def test_single_group_stays_ambiguous() -> None:
    # "1.000" could be one thousand or 1.0; the decimal reading is kept.
    assert normalize("1.000") == "1.000"
    assert normalize("1,000") == "1.000"


def test_grouping_runs_before_semicolon_rewrite() -> None:
    # If grouping ran after ';' -> ',', this would collapse into one number.
    assert normalize("min(1;234;567)") == "min(1,234,567)"
