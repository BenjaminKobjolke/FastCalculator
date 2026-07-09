"""Central application logger.

Every module logs through `AppLogger` — never `print()` or `logging.getLogger`
directly — so logging can be turned off, level-filtered, or redirected from this
single place. Feature code calls `AppLogger.get(__name__)`.
"""

from __future__ import annotations

import logging
import os

_CONFIGURED = False


class AppLogger:
    """Thin wrapper over the stdlib logging module (the single off switch)."""

    @staticmethod
    def _configure() -> None:
        global _CONFIGURED
        if _CONFIGURED:
            return
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, level_name, logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        _CONFIGURED = True

    @staticmethod
    def get(name: str) -> logging.Logger:
        AppLogger._configure()
        return logging.getLogger(name)
