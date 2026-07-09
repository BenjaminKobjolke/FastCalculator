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


def test_format_number_trims_integers() -> None:
    results = evaluate_document("6 / 2\n9 / 2")
    assert format_result(results[0]) == "3"
    assert format_result(results[1]) == "4.5"
