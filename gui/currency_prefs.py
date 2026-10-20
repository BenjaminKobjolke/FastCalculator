"""Persisted currency download preference and asynchronous ECB rate fetch."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import QSettings, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from app_logger import AppLogger
from gui.currency_rates import ECB_URL, CurrencyRates, decode_cache, encode_cache, parse_ecb_xml

_log = AppLogger.get(__name__)


class CurrencyPrefs:
    """Own the persisted switch, cached rates and a single in-flight fetch."""

    def __init__(
        self,
        on_change: Callable[[], None],
        *,
        settings: QSettings | None = None,
        network: QNetworkAccessManager | None = None,
    ) -> None:
        self._settings = settings if settings is not None else QSettings()
        self._network = network if network is not None else QNetworkAccessManager()
        self._on_change = on_change
        self._enabled = False
        self._rates: dict[str, float] = {}
        self._generation = 0

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def rates(self) -> Mapping[str, float]:
        return self._rates.copy()

    def restore(self) -> None:
        """Restore the off-by-default setting and fetch only when enabled."""
        self._enabled = bool(self._settings.value("currency/download", False, type=bool))
        if self._enabled:
            self._load_cache()
            self._fetch()

    def set_download(self, arg: str) -> None:
        """Set or toggle download with `/currency-rates [on|off]`."""
        value = arg.strip().lower()
        if value not in ("", "on", "off"):
            _log.info("ignored /currency-rates with invalid arg %r", arg)
            return
        enabled = not self._enabled if not value else value == "on"
        self._settings.setValue("currency/download", enabled)
        if not enabled:
            self._generation += 1
            changed = self._enabled or bool(self._rates)
            self._enabled = False
            self._rates.clear()
            if changed:
                self._on_change()
            return

        self._enabled = True
        self._load_cache()
        self._on_change()
        self._fetch()

    def _load_cache(self) -> None:
        raw = str(self._settings.value("currency/rates", "", type=str))
        try:
            cached = decode_cache(raw)
        except ValueError:
            self._rates.clear()
            return
        self._rates = dict(cached.rates)

    def _fetch(self) -> None:
        generation = self._generation
        request = QNetworkRequest(QUrl(ECB_URL))
        reply = self._network.get(request)
        reply.finished.connect(lambda: self._receive(reply, generation))

    def _receive(self, reply: QNetworkReply, generation: int) -> None:
        if not self._enabled or generation != self._generation:
            reply.deleteLater()
            return
        if reply.error() != QNetworkReply.NetworkError.NoError:
            _log.warning("ECB rate fetch failed: %s", reply.errorString())
            reply.deleteLater()
            return
        try:
            snapshot = parse_ecb_xml(bytes(reply.readAll()))
        except (ValueError, TypeError) as exc:
            _log.warning("ECB rate response was rejected: %s", exc)
            reply.deleteLater()
            return

        self._store(snapshot)
        self._rates = dict(snapshot.rates)
        reply.deleteLater()
        self._on_change()

    def _store(self, snapshot: CurrencyRates) -> None:
        self._settings.setValue("currency/rates", encode_cache(snapshot))
        self._settings.setValue("currency/date", snapshot.date)
