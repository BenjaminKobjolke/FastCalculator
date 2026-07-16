"""Application entry point: launch the Numi-style calculator window."""

from __future__ import annotations

import sys

from app_logger import AppLogger


def main() -> int:
    from PySide6.QtCore import QLocale
    from PySide6.QtWidgets import QApplication

    from gui import i18n
    from gui.main_window import MainWindow

    AppLogger.get(__name__).info("starting calculator")
    app = QApplication(sys.argv)
    app.setOrganizationName("BenjaminKobjolke")
    app.setApplicationName("FastCalculator")
    i18n.set_language(QLocale.system().name().split("_")[0])
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
