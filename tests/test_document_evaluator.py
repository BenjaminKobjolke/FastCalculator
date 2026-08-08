from gui.document_evaluator import (
    evaluate_document,
    format_result,
    inherited_styles,
)


def test_scope_flows_between_lines() -> None:
    results = evaluate_document("x = 10\nx hoch 2\nx + 5")
    assert results[0].value == 10
    assert results[1].value == 100
    assert results[2].value == 15


def test_deleting_source_line_breaks_dependents() -> None:
    # no "x = ..." line -> "x hoch 2" can no longer resolve x
    results = evaluate_document("x hoch 2")
    assert not results[0].success


def test_blank_and_error_lines_format_empty() -> None:
    results = evaluate_document("\nfoo +\n2 + 2")
    assert format_result(results[0]) == ""  # blank line
    assert format_result(results[1]) == ""  # syntax error
    assert format_result(results[2]) == "4"


def test_sum_totals_results_above() -> None:
    results = evaluate_document("10\n20\n$sum")
    assert results[2].value == 30


def test_sum_excludes_current_and_below() -> None:
    # $sum on the first line sees nothing above it -> 0.
    results = evaluate_document("$sum\n10")
    assert results[0].value == 0


def test_sum_counts_assignment_values() -> None:
    results = evaluate_document("x = 5\n10\n$sum")
    assert results[2].value == 15


def test_sum_resets_at_blank_line() -> None:
    results = evaluate_document("10\n20\n\n5\n$sum")
    assert results[4].value == 5  # only the group after the blank line


def test_sum_is_zero_at_start_of_new_group() -> None:
    results = evaluate_document("10\n20\n\n$sum")
    assert results[3].value == 0


def test_sum_ignores_error_lines() -> None:
    results = evaluate_document("10\nfoo +\n$sum")
    assert results[2].value == 10


def test_sum_percent_example() -> None:
    # The plan's worked example: 2000 - 5% of 2000.
    results = evaluate_document("Angebot: 2000\nRabatt: $sum - 5%")
    assert results[1].value == 1900


def test_leading_operator_continues_running_total() -> None:
    # The reported case: "- 4000" under "2000 plus 2000" means 4000 - 4000.
    results = evaluate_document("2000 plus 2000\n- 4000")
    assert results[0].value == 4000
    assert results[1].value == 0


def test_leading_multiply_uses_running_total() -> None:
    # Leading "*" was a syntax error before; now it multiplies the sum.
    results = evaluate_document("10\n20\n* 2")
    assert results[2].value == 60


def test_leading_operator_resets_after_blank_line() -> None:
    # A blank line starts a new group -> sum is 0 -> "- 5" is just -5.
    results = evaluate_document("10\n\n- 5")
    assert results[2].value == -5


def test_leading_operator_on_single_line_is_unary() -> None:
    # No lines above -> sum is 0 -> "-5" stays -5.
    results = evaluate_document("-5")
    assert results[0].value == -5


def test_leading_percent_applies_to_running_total() -> None:
    results = evaluate_document("10\n+ 5%")
    assert results[1].value == 10.5


def test_leading_operator_inherits_group_decimal_style() -> None:
    out = _formatted("2000,00\n- 500")
    assert out == ["2000,00", "1500,00"]


def test_leading_operator_continuation_replaces_running_total() -> None:
    # The reported case: "*3" should continue from the shown "0", not
    # double-count the pre-subtraction total (100 * 3 = 300 is wrong).
    results = evaluate_document("100\n-100\n*3")
    assert [r.value for r in results] == [100, 0, 0]


def test_continuation_result_feeds_later_sum() -> None:
    # A leading-operator line's result (not the pre-continuation total) is
    # what a later "$sum" sees.
    results = evaluate_document("2000 plus 2000\n- 4000\n$sum")
    assert results[2].value == 0


def test_leading_word_operator_continuation_replaces_running_total() -> None:
    # Word operators ("mal") normalize to "*" before the leading-op check;
    # the continuation flag must fire for them too, not just symbol operators.
    results = evaluate_document("10\n20\nmal 2")
    assert [r.value for r in results] == [10, 20, 60]


def test_format_number_trims_integers() -> None:
    results = evaluate_document("6 / 2\n9 / 2")
    assert format_result(results[0]) == "3"
    assert format_result(results[1]) == "4.5"


def test_output_mirrors_input_decimal_style() -> None:
    line = "100.00 + 19%"
    r = evaluate_document(line)[0]
    assert format_result(r, line) == "119.00"

    line = "100,00 + 19%"
    r = evaluate_document(line)[0]
    assert format_result(r, line) == "119,00"

    # No explicit decimals in input -> keep the plain formatting.
    line = "100 + 19%"
    r = evaluate_document(line)[0]
    assert format_result(r, line) == "119"


def test_max_decimals_caps_long_fractions() -> None:
    r = evaluate_document("10/3")[0]
    assert format_result(r, "10/3", max_decimals=2) == "3.33"


def test_max_decimals_trims_instead_of_padding() -> None:
    # cap, don't pad: whole/short results keep their natural width
    assert format_result(evaluate_document("5+5")[0], "5+5", max_decimals=2) == "10"
    assert format_result(evaluate_document("5/2")[0], "5/2", max_decimals=2) == "2.5"


def test_max_decimals_zero_rounds_to_integer() -> None:
    r = evaluate_document("10/3")[0]
    assert format_result(r, "10/3", max_decimals=0) == "3"


def test_max_decimals_caps_input_style_keeps_separator() -> None:
    line = "100,00 + 19%"
    r = evaluate_document(line)[0]
    assert format_result(r, line, max_decimals=1) == "119,0"


def test_max_decimals_never_extends_input_style() -> None:
    line = "1,5 * 3"
    r = evaluate_document(line)[0]
    assert format_result(r, line, max_decimals=3) == "4,5"


def test_running_results_format() -> None:
    assert _formatted("10 km") == ["10 km"]
    assert _formatted("50:00 / 10 km") == ["5:00 /km"]
    assert _formatted("10 km / 50:00") == ["12 km/h"]
    assert _formatted("1:23:45") == ["1:23:45"]
    assert _formatted("30 min") == ["30:00"]
    assert _formatted("4:30 min/km * 42.195 km") == ["3:09:53"]
    assert _formatted("10 km in mi") == ["6.214 mi"]


def test_units_flow_through_leading_operator() -> None:
    # the reported case: "* 42 km" under a pace line = pace * distance = time
    assert _formatted("3:22 / 1 km\n* 42 km") == ["3:22 /km", "2:21:24"]


def test_bare_time_scaled_by_distance() -> None:
    # a duration line then "* 42 km" multiplies the time by 42 -> finish time
    assert _formatted("3:22\n* 42 km") == ["3:22", "2:21:24"]


def test_homogeneous_unit_group_sums_with_unit() -> None:
    assert _formatted("5 km\n3 km\n$sum") == ["5 km", "3 km", "8 km"]


def test_leading_operator_scales_unit_total() -> None:
    assert _formatted("5 km\n3 km\n* 2") == ["5 km", "3 km", "16 km"]


def test_distance_keeps_input_decimal_separator() -> None:
    # comma-locale input -> comma-formatted number, still with the unit suffix
    assert _formatted("5,5 mi + 3 km") == ["11,85 km"]


def _formatted(text: str) -> list[str]:
    """Render a whole document the way the GUI does: each result formatted with
    its own line and the inherited group decimal style."""
    lines = text.split("\n")
    results = evaluate_document(text)
    styles = inherited_styles(lines)
    return [
        format_result(r, line, style)
        for line, r, style in zip(lines, results, styles, strict=False)
    ]


def test_inline_line_inherits_group_decimal_style() -> None:
    # The reported bug: "$sum" line drops the ",00" the group above established.
    out = _formatted("Angebot: 2000,00 Euro\nDiscount: $sum - 35%")
    assert out == ["2000,00", "1300,00"]


def test_inline_line_without_group_decimals_stays_integer() -> None:
    # No decimals anywhere in the group -> no spurious ",00".
    out = _formatted("10\n20\n$sum")
    assert out[2] == "30"


def test_blank_line_resets_inherited_style() -> None:
    # The ",00" group ends at the blank line; the next group is decimal-free.
    out = _formatted("100,00\n\n5\n$sum")
    assert out[3] == "5"


def test_inline_line_with_own_decimals_uses_own_places() -> None:
    # The line carries its own decimals -> they win over the group's place count.
    out = _formatted("100,00\n$sum + 1,5")
    assert out[1] == "101,5"


def test_non_inline_line_does_not_inherit_group_style() -> None:
    # Only "$"-var lines inherit; a plain expression keeps its own formatting.
    out = _formatted("100,00\n5 * 3")
    assert out[1] == "15"


def test_bool_result_formats_as_text() -> None:
    results = evaluate_document("5 == 5\n5 ist gleich 3")
    # Bool text is verbatim: decimal styling and /round caps never touch it.
    assert format_result(results[0], "5 == 5", max_decimals=2) == "true"
    assert format_result(results[1], "5 ist gleich 3") == "falsch"


def test_bool_line_is_transparent_to_sum() -> None:
    results = evaluate_document("5\n3\n5 == 5\n$sum")
    assert results[3].value == 8


def test_bool_line_does_not_restart_unit_group() -> None:
    assert _formatted("5 km\n3 km\n2 == 2\n$sum") == ["5 km", "3 km", "true", "8 km"]
