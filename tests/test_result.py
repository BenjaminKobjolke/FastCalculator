from engine.result import EvalResult


def test_ok_sets_value_and_success() -> None:
    r = EvalResult.ok(5.0)
    assert r.success is True
    assert r.value == 5.0
    assert r.error is None
    assert r.assigned_name is None


def test_ok_with_assigned_name() -> None:
    r = EvalResult.ok(10.0, assigned_name="x")
    assert r.assigned_name == "x"
    assert r.success is True


def test_fail_sets_error_and_no_value() -> None:
    r = EvalResult.fail("boom")
    assert r.success is False
    assert r.error == "boom"
    assert r.value is None


def test_from_bool_true() -> None:
    r = EvalResult.from_bool(True, "true")
    assert r.success is True
    assert r.value == 1.0
    assert r.kind == "bool"
    assert r.text == "true"
    assert r.quantity is None


def test_from_bool_false() -> None:
    r = EvalResult.from_bool(False, "falsch")
    assert r.value == 0.0
    assert r.text == "falsch"
