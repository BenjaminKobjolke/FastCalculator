from gui.document_evaluator import evaluate_document, format_result


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
