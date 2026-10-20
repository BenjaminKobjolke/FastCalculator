"""Persistence and command behavior for currency download preferences."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast
from unittest.mock import MagicMock

from PySide6.QtCore import QByteArray, QSettings
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply

from gui.currency_prefs import CurrencyPrefs


def _prefs(
    saved: dict[str, object] | None = None,
) -> tuple[CurrencyPrefs, MagicMock, MagicMock, list[Callable[[], None]]]:
    values = saved or {}
    settings = MagicMock(spec=QSettings)
    settings.value.side_effect = lambda key, default=None, **kwargs: values.get(key, default)
    network = MagicMock(spec=QNetworkAccessManager)
    reply = MagicMock(spec=QNetworkReply)
    callbacks: list[Callable[[], None]] = []
    reply.finished.connect.side_effect = callbacks.append
    reply.error.return_value = QNetworkReply.NetworkError.NoError
    reply.readAll.return_value = QByteArray()
    network.get.return_value = reply
    prefs = CurrencyPrefs(
        lambda: None,
        settings=cast(QSettings, settings),
        network=cast(QNetworkAccessManager, network),
    )
    return prefs, settings, network, callbacks


def test_restore_defaults_to_disabled_without_fetch() -> None:
    prefs, _, network, _ = _prefs({"currency/rates": '{"date":"2026-10-20","rates":{"USD":1.2}}'})

    prefs.restore()

    assert not prefs.enabled
    assert prefs.rates == {}
    network.get.assert_not_called()


def test_restore_enabled_loads_cache_before_fetch() -> None:
    prefs, _, network, _ = _prefs(
        {
            "currency/download": True,
            "currency/rates": '{"date":"2026-10-20","rates":{"USD":1.2}}',
        }
    )

    prefs.restore()

    assert prefs.enabled and prefs.rates == {"USD": 1.2}
    network.get.assert_called_once()


def test_off_clears_rates_persists_and_ignores_late_reply() -> None:
    prefs, settings, network, callbacks = _prefs(
        {
            "currency/download": True,
            "currency/rates": '{"date":"2026-10-20","rates":{"USD":1.2}}',
        }
    )
    prefs.restore()
    assert prefs.rates == {"USD": 1.2}

    prefs.set_download("off")
    callbacks[0]()

    assert not prefs.enabled and prefs.rates == {}
    settings.setValue.assert_called_with("currency/download", False)
    network.get.assert_called_once()
