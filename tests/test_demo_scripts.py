"""Validation of the registered demo scripts against the command registry."""

import json
import string
from pathlib import Path

from automated_screenshot_connector import Command, Screenshot, TypeText

from demo.scripts import DEMOS
from gui.commands import parse_command_line, suggest

TEXTS_DIR = Path(__file__).parent.parent / "tools" / "create_media" / "texts"


def _script_placeholders() -> set[str]:
    names: set[str] = set()
    for script in DEMOS.values():
        for step in script.steps:
            text = step.text if isinstance(step, TypeText) else None
            text = step.line if isinstance(step, Command) else text
            if text:
                names.update(f for _, f, _, _ in string.Formatter().parse(text) if f)
    return names


def test_registry_ids_match_script_ids() -> None:
    for demo_id, script in DEMOS.items():
        assert script.id == demo_id


def test_every_demo_has_a_name_and_steps() -> None:
    for script in DEMOS.values():
        assert script.name
        assert script.steps


def test_command_steps_use_known_commands() -> None:
    for script in DEMOS.values():
        for step in script.steps:
            if isinstance(step, Command):
                assert parse_command_line(step.line) is not None, step.line


def test_bare_command_steps_are_unambiguous() -> None:
    # An ambiguous prefix ("/copy" vs "/copy-last") opens the autocomplete menu
    # on Return instead of running, which would stall the demo.
    for script in DEMOS.values():
        for step in script.steps:
            if isinstance(step, Command) and " " not in step.line:
                assert suggest(step.line) == [step.line], step.line


def test_screenshot_names_unique_within_demo() -> None:
    for script in DEMOS.values():
        names = [s.name for s in script.steps if isinstance(s, Screenshot)]
        assert len(names) == len(set(names))


def test_every_placeholder_has_a_text_in_every_language() -> None:
    placeholders = _script_placeholders()
    texts_files = sorted(TEXTS_DIR.glob("*.json"))
    if placeholders:
        assert texts_files, f"scripts use placeholders {placeholders} but {TEXTS_DIR} is empty"
    for file in texts_files:
        keys = set(json.loads(file.read_text(encoding="utf-8")))
        missing = placeholders - keys
        assert not missing, f"{file.name} is missing texts for: {sorted(missing)}"


def test_texts_files_share_the_same_keys() -> None:
    key_sets = {
        file.name: set(json.loads(file.read_text(encoding="utf-8")))
        for file in TEXTS_DIR.glob("*.json")
    }
    assert len(set(map(frozenset, key_sets.values()))) <= 1, key_sets
