"""The registered demo scripts, keyed by their ``--automation-demo`` id.

Bare Command steps must be unambiguous command prefixes ("/copy" would open the
autocomplete menu instead of running — see tests/test_demo_scripts.py).
"""

from __future__ import annotations

from automated_screenshot_connector import Command, DemoScript, Pause, Screenshot, TypeText

DEMOS: dict[int, DemoScript] = {
    1: DemoScript(
        id=1,
        name="basic-math",
        steps=(
            Pause(0.5),
            TypeText("1+1\n"),
            Pause(0.8),
            TypeText("5*88\n"),
            Pause(0.8),
            TypeText("100/4\n"),
            Pause(1.2),
            Screenshot("basic-results"),
            Command("/clear"),
            Pause(0.5),
            TypeText("{price} = 20\n"),
            Pause(0.6),
            TypeText("{price} * 3\n"),
            Pause(1.2),
            Screenshot("variables"),
            Pause(1.0),
        ),
    ),
}
