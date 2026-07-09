from engine.preprocess import normalize, split_assignment


def test_comma_between_digits_becomes_dot() -> None:
    assert normalize("3,5 + 1,5") == "3.5 + 1.5"


def test_standalone_comma_in_function_uses_semicolon() -> None:
    # user separates args with ';'; engine turns it into the ',' ast expects
    assert normalize("min(1;2)") == "min(1,2)"


def test_word_operators_english() -> None:
    assert normalize("5 times 5") == "5 * 5"
    assert normalize("10 divided by 3") == "10 / 3"


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
