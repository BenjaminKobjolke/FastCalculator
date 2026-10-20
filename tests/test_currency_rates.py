"""ECB rates parsing, cache encoding, and localized currency hints."""

from __future__ import annotations

import json

import pytest

from gui import i18n
from gui.currency_rates import (
    CurrencyRates,
    currency_hint,
    decode_cache,
    encode_cache,
    parse_ecb_xml,
)


def test_parse_ecb_xml_extracts_date_and_positive_rates() -> None:
    rates = parse_ecb_xml(
        b'<Envelope><Cube><Cube time="2026-10-20">'
        b'<Cube currency="USD" rate="1.16"/><Cube currency="GBP" rate="0.87"/>'
        b"</Cube></Cube></Envelope>"
    )

    assert rates == CurrencyRates("2026-10-20", {"USD": 1.16, "GBP": 0.87})


@pytest.mark.parametrize(
    "xml",
    [
        b"not xml",
        b"<Envelope><Cube><Cube time='bad'>"
        b"<Cube currency='USD' rate='1'/></Cube></Cube></Envelope>",
        b"<Envelope><Cube><Cube time='2026-10-20'>"
        b"<Cube currency='bad' rate='1'/></Cube></Cube></Envelope>",
        b"<Envelope><Cube><Cube time='2026-10-20'>"
        b"<Cube currency='USD' rate='0'/></Cube></Cube></Envelope>",
        b"<Envelope><Cube><Cube time='2026-10-20'>"
        b"<Cube currency='USD' rate='nan'/></Cube></Cube></Envelope>",
    ],
)
def test_parse_ecb_xml_rejects_malformed_or_invalid_rates(xml: bytes) -> None:
    with pytest.raises(ValueError):
        parse_ecb_xml(xml)


def test_cache_round_trip_and_reject_invalid_json() -> None:
    rates = CurrencyRates("2026-10-20", {"USD": 1.16})

    encoded = encode_cache(rates)
    assert json.loads(encoded) == {"date": "2026-10-20", "rates": {"USD": 1.16}}
    assert decode_cache(encoded) == rates

    with pytest.raises(ValueError):
        decode_cache('{"date":"bad","rates":{"USD":0}}')


def test_currency_hints_follow_active_language() -> None:
    assert currency_hint(False) == "currency off: /currency-rates on"
    assert currency_hint(True) == "no rate yet"
    i18n.set_language("de")
    assert currency_hint(False) == "Währung aus: /currency-rates on"
    assert currency_hint(True) == "noch kein Kurs"
    i18n.set_language("en")
