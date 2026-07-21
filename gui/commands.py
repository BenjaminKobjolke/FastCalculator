"""Qt-free slash-command logic for the notepad.

Kept free of PySide6 so it is unit-testable without a display. The widget layer
(`gui/command_edit.py`) handles ghost text and keys; the window
(`gui/main_window.py`) performs the clipboard side effects.
"""

from __future__ import annotations

import os

from engine import EvalResult
from engine.inline import INLINE_VARS
from gui.document_evaluator import Style, format_result

COMMANDS: list[str] = [
    "/clear",
    "/copy",
    "/copy-last",
    "/exit",
    "/help",
    "/paste-last-result",
    "/release-notes",
    "/round",
    "/window-opacity",
    "/window-title",
    "/window-background-color",
    "/window-font-color",
    "/window-theme",
    "/window-margin",
    "/window-highlighting",
    "/window-number-color",
    "/window-operator-color",
    "/window-function-color",
    "/window-variable-color",
    "/window-inline-color",
]

# Inline `$`-variable tokens, autocompleted like commands but kept in the text.
INLINE_TOKENS: list[str] = [f"${name}" for name in INLINE_VARS]


def command_at(text: str, col: int) -> str | None:
    """The `/`- or `$`-token ending at `col`: from the last `/`/`$` of the
    trailing non-space run up to the cursor.

    Lets a command or `$sum` be recognised anywhere in a line, with (`105+ /pas`)
    or without (`81+/pas`) a space before it. Returns None when the trailing run
    holds neither `/` nor `$`. Non-command slashes (division, `100/5` -> `/5`)
    fall through `suggest`/`parse_command`, which reject them.
    """
    head = text[:col]
    i = len(head)
    while i > 0 and not head[i - 1].isspace():
        i -= 1
    run = head[i:]
    start = max(run.rfind("/"), run.rfind("$"))
    return run[start:] if start != -1 else None


def suggest(prefix: str) -> list[str]:
    """Full completions that start with `prefix` (case-insensitive).

    `/`-prefixes match commands, `$`-prefixes match inline variables; anything
    else returns `[]`, so plain math lines never trigger suggestions.
    """
    p = prefix.strip().lower()
    if p.startswith("/"):
        return [c for c in COMMANDS if c.startswith(p)]
    if p.startswith("$"):
        return [v for v in INLINE_TOKENS if v.startswith(p)]
    return []


def common_prefix(matches: list[str]) -> str:
    """Longest string that every command in `matches` starts with (``""`` if
    empty). Single match -> the whole command, so completion still fills fully."""
    if not matches:
        return ""
    return os.path.commonprefix(matches)


def parse_command(line: str) -> str | None:
    """Return the command if `line` (trimmed) is exactly one, else None."""
    stripped = line.strip().lower()
    return stripped if stripped in COMMANDS else None


def parse_command_line(line: str) -> tuple[str, str] | None:
    """`(command, arg)` if `line`'s first token is a known command, else None.

    Handles argument-carrying commands (`/window-opacity 80`) that
    `parse_command` rejects because they are not an exact whole-line match. `arg`
    is the trimmed remainder (`""` when the command takes none)."""
    stripped = line.strip()
    if not stripped.startswith("/"):
        return None
    cmd, _, rest = stripped.partition(" ")
    cmd = cmd.lower()
    if cmd not in COMMANDS:
        return None
    return cmd, rest.strip()


def _styles_for(lines: list[str], styles: list[Style | None] | None) -> list[Style | None]:
    """Align a per-line inherited-style list with `lines`, or all-None if absent."""
    return styles if styles is not None else [None] * len(lines)


def build_copy_text(
    lines: list[str],
    results: list[EvalResult],
    styles: list[Style | None] | None = None,
    max_decimals: int | None = None,
) -> str:
    """Render non-empty, successful lines as `input = result`, newline-joined."""
    pairs = []
    for line, result, style in zip(lines, results, _styles_for(lines, styles), strict=False):
        text = line.strip()
        if not text or not result.success or result.value is None:
            continue
        # An assignment line ("price = 20") already shows its value; don't
        # append "= 20" a second time. Only bare expressions get the " = value".
        if result.assigned_name is not None:
            pairs.append(text)
        else:
            pairs.append(f"{text} = {format_result(result, line, style, max_decimals)}")
    return "\n".join(pairs)


def last_result_text(
    lines: list[str],
    results: list[EvalResult],
    styles: list[Style | None] | None = None,
    max_decimals: int | None = None,
) -> str:
    """Formatted value of the last successful result, or `""` if none."""
    triples = list(zip(lines, results, _styles_for(lines, styles), strict=False))
    for line, result, style in reversed(triples):
        if result.success and result.value is not None:
            return format_result(result, line, style, max_decimals)
    return ""
