"""Currency unit and document behavior without GUI or network access."""

import pytest

from engine import evaluate
from engine.currency import CURRENCY_UNAVAILABLE, currency_scope
from engine.units import MONEY, UNITS, Quantity, render
from gui.document_evaluator import evaluate_document, pane_texts


def test_currency_scope_converts_rate_to_euro_based_quantity() -> None:
    scope = currency_scope({"USD": 1.25, "GBP": 0.8})
    usd = scope["_cur_usd"]
    gbp = scope["_cur_gbp"]

    assert usd.dim == MONEY and usd.mag == pytest.approx(0.8)
    assert gbp.dim == MONEY and gbp.mag == pytest.approx(1.25)
    rendered = render(usd)
    assert rendered[0] == pytest.approx(1)
    assert rendered[1:] == ("money", "$")


def test_static_euro_and_currency_conversion() -> None:
    result = evaluate("100 usd in eur", currency_scope({"USD": 1.25}))

    assert result.success
    assert result.quantity == Quantity(80, MONEY, UNITS["eur"])
    assert result.unit == "€"


def test_unavailable_currency_has_specific_failure() -> None:
    result = evaluate("50 usd", {})

    assert not result.success
    assert result.error == CURRENCY_UNAVAILABLE


def test_unknown_name_keeps_ordinary_error() -> None:
    result = evaluate("imaginary + 50", {})

    assert not result.success
    assert result.error == "unknown name: imaginary"


def test_document_currency_conversions_totals_and_disabled_rates() -> None:
    rates = {"USD": 1.25}
    results = evaluate_document("100 usd in eur\n20 eur\n$sum", rates)

    assert [result.value for result in results] == pytest.approx([80, 20, 100])
    assert results[2].unit == "€"

    disabled = evaluate_document("100 usd", {})[0]
    assert not disabled.success and disabled.error == CURRENCY_UNAVAILABLE


def test_pane_texts_maps_unavailable_currency_to_supplied_hint() -> None:
    lines = ["50 usd", "unknown + 50"]
    results = evaluate_document("\n".join(lines), {})

    assert pane_texts(lines, results, currency_hint="currency off: /currency-rates on") == [
        "currency off: /currency-rates on",
        "",
    ]


def test_pane_texts_formats_successful_results() -> None:
    lines = ["20 eur", "50 usd"]
    results = evaluate_document("\n".join(lines), {"USD": 1.25})

    assert pane_texts(lines, results, currency_hint="no rate yet") == ["20 €", "50 $"]


def test_disabled_currency_does_not_reuse_a_supplied_cached_rate() -> None:
    # The caller passes no rates when the feature is disabled, even if it has a cache.
    result = evaluate_document("5 usd", {})[0]

    assert not result.success and result.error == CURRENCY_UNAVAILABLE


def test_currency_scope_rejects_nonpositive_rates() -> None:
    with pytest.raises(ValueError):
        currency_scope({"USD": 0})

