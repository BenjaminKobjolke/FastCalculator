"""Surface words for units and their conversion targets.

The maps are shared data for preprocessing; unit values and dimensions live in
``units.py``.
"""

from __future__ import annotations

UNIT_ALIASES: dict[str, str] = {
    "km/h": "kmh",
    "kmh": "kmh",
    "kph": "kmh",
    "mph": "mph",
    "km": "km",
    "kms": "km",
    "kilometer": "km",
    "kilometers": "km",
    "kilometre": "km",
    "kilometres": "km",
    "mi": "mi",
    "mile": "mi",
    "miles": "mi",
    "m": "m",
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "oz": "oz",
    "ounce": "oz",
    "ounces": "oz",
    "min": "min",
    "h": "h",
    "s": "s",
}

_TIME_UNITS = {"min", "h", "s"}
CONV_TARGETS: dict[str, str] = {
    word: unit for word, unit in UNIT_ALIASES.items() if unit not in _TIME_UNITS
}
CONV_TARGETS.update(
    {
        "/km": "_pace_km",
        "min/km": "_pace_km",
        "/mi": "_pace_mi",
        "min/mi": "_pace_mi",
    }
)
