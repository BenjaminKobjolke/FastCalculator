"""Validated, Qt-free ECB rate parsing and QSettings cache serialization."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import date
from typing import Mapping
from xml.etree import ElementTree

from gui.i18n import t
from gui.i18n_keys import TK

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
_CURRENCY_CODE = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True)
class CurrencyRates:
    """One ECB publication date and its units of foreign currency per euro."""

    date: str
    rates: Mapping[str, float]


def parse_ecb_xml(payload: bytes) -> CurrencyRates:
    """Parse a daily ECB XML response, rejecting incomplete or unsafe data."""
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise ValueError("invalid ECB XML") from exc

    dated_cube = next(
        (node for node in root.iter() if _tag_name(node) == "Cube" and "time" in node.attrib),
        None,
    )
    if dated_cube is None:
        raise ValueError("ECB XML has no dated rates")
    rate_date = dated_cube.attrib["time"]
    try:
        date.fromisoformat(rate_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid ECB rate date") from exc

    rates: dict[str, float] = {}
    for node in dated_cube:
        if _tag_name(node) != "Cube":
            continue
        code = node.attrib.get("currency", "")
        raw_rate = node.attrib.get("rate", "")
        try:
            rate = float(raw_rate)
        except ValueError as exc:
            raise ValueError("invalid ECB rate") from exc
        if not _CURRENCY_CODE.fullmatch(code) or not _is_finite(rate) or rate <= 0:
            raise ValueError("invalid ECB currency rate")
        if code in rates:
            raise ValueError("duplicate ECB currency rate")
        rates[code] = rate
    if not rates:
        raise ValueError("ECB XML has no currency rates")
    return CurrencyRates(rate_date, rates)


def encode_cache(value: CurrencyRates) -> str:
    """Encode a validated rates snapshot as compact JSON for QSettings."""
    _validate(value.date, value.rates)
    return json.dumps({"date": value.date, "rates": dict(value.rates)}, separators=(",", ":"))


def decode_cache(raw: str) -> CurrencyRates:
    """Decode and validate a QSettings cache value."""
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("invalid currency cache") from exc
    if not isinstance(value, dict) or set(value) != {"date", "rates"}:
        raise ValueError("invalid currency cache")
    rate_date, rates = value["date"], value["rates"]
    if not isinstance(rate_date, str) or not isinstance(rates, dict):
        raise ValueError("invalid currency cache")
    if any(not isinstance(code, str) or isinstance(rate, bool) for code, rate in rates.items()):
        raise ValueError("invalid currency cache")
    try:
        numeric_rates = {code: float(rate) for code, rate in rates.items()}
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError("invalid currency cache") from exc
    _validate(rate_date, numeric_rates)
    return CurrencyRates(rate_date, numeric_rates)


def currency_hint(enabled: bool) -> str:
    """Return the localized row hint for unavailable currency rates."""
    return t(TK.CURRENCY_NO_RATE_HINT if enabled else TK.CURRENCY_DISABLED_HINT)


def _validate(rate_date: str, rates: Mapping[str, float]) -> None:
    try:
        date.fromisoformat(rate_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid currency rate date") from exc
    if not rates:
        raise ValueError("currency cache has no rates")
    for code, rate in rates.items():
        if (
            not _CURRENCY_CODE.fullmatch(code)
            or isinstance(rate, bool)
            or not isinstance(rate, (int, float))
            or not _is_finite(rate)
            or rate <= 0
        ):
            raise ValueError("invalid currency cache rate")


def _is_finite(rate: int | float) -> bool:
    try:
        return math.isfinite(rate)
    except OverflowError:
        return False


def _tag_name(node: ElementTree.Element) -> str:
    return node.tag.rsplit("}", 1)[-1]
