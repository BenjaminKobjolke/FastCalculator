"""Currency aliases and caller-owned rate quantities for the engine."""

from __future__ import annotations

import math
from collections.abc import Mapping

from .units import MONEY, Quantity, Unit

CURRENCY_UNAVAILABLE = "currency unavailable"

# Surface words map to stable ISO codes. Symbols are suffix-only in expressions.
CURRENCY_CODES: dict[str, str] = {
    "usd": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "$": "USD",
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",
    "€": "EUR",
    "gbp": "GBP",
    "pound": "GBP",
    "pounds": "GBP",
    "£": "GBP",
    "jpy": "JPY",
    "yen": "JPY",
    "¥": "JPY",
    "bgn": "BGN",
    "chf": "CHF",
    "cad": "CAD",
    "aud": "AUD",
    "sek": "SEK",
    "nok": "NOK",
    "dkk": "DKK",
    "pln": "PLN",
    "czk": "CZK",
    "huf": "HUF",
    "ron": "RON",
    "isk": "ISK",
    "hrk": "HRK",
    "try": "TRY",
    "inr": "INR",
    "brl": "BRL",
    "cny": "CNY",
    "hkd": "HKD",
    "idr": "IDR",
    "ils": "ILS",
    "krw": "KRW",
    "mxn": "MXN",
    "myr": "MYR",
    "nzd": "NZD",
    "php": "PHP",
    "sgd": "SGD",
    "thb": "THB",
    "zar": "ZAR",
}

CURRENCY_SYMBOLS: dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "BGN": "BGN",
    "CHF": "CHF",
    "CAD": "CA$",
    "AUD": "A$",
    "SEK": "SEK",
    "NOK": "NOK",
    "DKK": "DKK",
    "PLN": "PLN",
    "CZK": "CZK",
    "HUF": "HUF",
    "RON": "RON",
    "ISK": "ISK",
    "HRK": "HRK",
    "TRY": "TRY",
    "INR": "₹",
    "BRL": "R$",
    "CNY": "CN¥",
    "HKD": "HK$",
    "IDR": "IDR",
    "ILS": "₪",
    "KRW": "₩",
    "MXN": "MX$",
    "MYR": "MYR",
    "NZD": "NZ$",
    "PHP": "₱",
    "SGD": "S$",
    "THB": "฿",
    "ZAR": "R",
}

_CURRENCY_ALIAS_TO_NAME: dict[str, str] = {
    word: f"_cur_{code.lower()}" for word, code in CURRENCY_CODES.items()
}


def currency_name(word: str) -> str | None:
    """Return the evaluator name for a currency alias, or None."""
    name = _CURRENCY_ALIAS_TO_NAME.get(word.lower())
    return "eur" if name == "_cur_eur" else name


def currency_scope(rates: Mapping[str, float]) -> dict[str, Quantity]:
    """Build unit quantities from ECB-style rates (foreign units per EUR)."""
    scope: dict[str, Quantity] = {}
    for code, rate in rates.items():
        normalized = code.upper()
        if normalized not in CURRENCY_SYMBOLS:
            raise ValueError(f"unsupported currency code: {code}")
        if normalized == "EUR":
            continue
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError(f"invalid currency rate: {code}")
        name = f"_cur_{normalized.lower()}"
        unit = Unit(CURRENCY_SYMBOLS[normalized], 1 / rate, MONEY, "money")
        scope[name] = Quantity(unit.factor, MONEY, unit)
    return scope
