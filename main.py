"""Application entry point: launch the Numi-style calculator window.

Supports the automation-demo contract via the automated-screenshot-connector
library: ``--automation-demo <id>`` plays a scripted, recordable demo and
exits.
"""

from __future__ import annotations

import sys
from pathlib import Path

from automated_screenshot_connector import parse_demo_args

from app_logger import AppLogger

_ICON = Path(__file__).resolve().parent / "assets" / "icon.png"


def main() -> int:
    from PySide6.QtCore import QLocale, Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from gui import i18n
    from gui.main_window import MainWindow

    logger = AppLogger.get(__name__)
    options, leftover = parse_demo_args(sys.argv[1:])
    if leftover:
        logger.error("unrecognized arguments: %s", " ".join(leftover))
        return 2

    if options.demo is not None:
        from demo.scripts import DEMOS

        if options.demo not in DEMOS:
            logger.error("unknown demo id %s (available: %s)", options.demo, sorted(DEMOS))
            return 2

    logger.info("starting calculator")
    app = QApplication(sys.argv)
    app.setOrganizationName("BenjaminKobjolke")
    if _ICON.exists():
        app.setWindowIcon(QIcon(str(_ICON)))
    if options.demo is not None:
        from automated_screenshot_connector.qt import prepare_demo_settings

        # Wiped temp-INI namespace: deterministic demo state, user's real
        # settings untouched. Our --automation-demo-set dialect: QSettings keys.
        prepare_demo_settings("FastCalculator-Demo", options.demo_settings)
    else:
        app.setApplicationName("FastCalculator")
    # Demo runs pin the UI language per recording; otherwise follow the OS
    i18n.set_language(options.demo_language or QLocale.system().name().split("_")[0])
    window = MainWindow()

    if options.demo is not None:
        from automated_screenshot_connector import DemoClient, localize_script
        from automated_screenshot_connector.qt import DemoPlayer

        if options.demo_width is not None and options.demo_height is not None:
            window.resize(options.demo_width, options.demo_height)
        # No scrollbars in recordings: demo content is sized to fit the window, and
        # a scrollbar would show as a stray vertical line in the capture.
        for pane in (window._input, window._results):
            pane.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            pane.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        script = localize_script(DEMOS[options.demo], dict(options.demo_texts))
        client = DemoClient(options.demo_port)
        window.show()
        # winId() is the native HWND, valid once the window is shown
        player = DemoPlayer(window._input, client, script, hwnd=int(window.winId()))
        player.start()
    else:
        window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
