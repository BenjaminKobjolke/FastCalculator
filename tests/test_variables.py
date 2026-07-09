from engine import evaluate


def test_assignment_stores_and_reports_name() -> None:
    scope: dict[str, float] = {}
    r = evaluate("x = 10", scope)
    assert r.success
    assert r.assigned_name == "x"
    assert r.value == 10
    assert scope["x"] == 10


def test_variable_reuse_across_calls() -> None:
    scope: dict[str, float] = {}
    evaluate("x = 10", scope)
    r = evaluate("x hoch 2", scope)
    assert r.success
    assert r.value == 100


def test_assignment_with_expression_rhs() -> None:
    scope: dict[str, float] = {}
    evaluate("a = 2 + 3", scope)
    evaluate("b = a * 4", scope)
    assert scope["a"] == 5
    assert scope["b"] == 20


def test_unknown_variable_errors() -> None:
    r = evaluate("y + 1", {})
    assert not r.success
    assert r.error is not None and "unknown name" in r.error


def test_user_scope_shadows_constant() -> None:
    scope: dict[str, float] = {}
    evaluate("e = 5", scope)
    r = evaluate("e + 1", scope)
    assert r.value == 6
