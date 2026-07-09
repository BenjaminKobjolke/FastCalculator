"""Qt-free slash-command logic for the notepad.

Kept free of PySide6 so it is unit-testable without a display. The widget layer
(`gui/command_edit.py`) handles ghost text and keys; the window
(`gui/main_window.py`) performs the clipboard side effects.
"""

from __future__ import annotations

from engine import EvalResult
from gui.document_evaluator import format_result

COMMANDS: list[str] = ["/clear", "/copy", "/copy-last", "/exit", "/paste-last-result"]


def command_at(text: str, col: int) -> str | None:
    """The `/`-token ending at `col`: from the last `/` of the trailing non-space
    run up to the cursor.

    Lets a command be recognised anywhere in a line, with (`105+ /pas`) or
    without (`81+/pas`) a space before the slash. Returns None when the trailing
    run holds no `/`. Non-command slashes (division, `100/5` -> `/5`) fall
    through `suggest`/`parse_command`, which reject them.
    """
    head = text[:col]
    i = len(head)
    while i > 0 and not head[i - 1].isspace():
        i -= 1
    run = head[i:]
    slash = run.rfind("/")
    return run[slash:] if slash != -1 else None


def suggest(prefix: str) -> list[str]:
    """Full commands that start with `prefix` (case-insensitive).

    Returns `[]` when `prefix` does not begin with `/`, so plain math lines never
    trigger suggestions.
    """
    p = prefix.strip().lower()
    if not p.startswith("/"):
        return []
    return [c for c in COMMANDS if c.startswith(p)]


def parse_command(line: str) -> str | None:
    """Return the command if `line` (trimmed) is exactly one, else None."""
    stripped = line.strip().lower()
    return stripped if stripped in COMMANDS else None


def build_copy_text(lines: list[str], results: list[EvalResult]) -> str:
    """Render non-empty, successful lines as `input = result`, newline-joined."""
    pairs = []
    for line, result in zip(lines, results, strict=False):
        text = line.strip()
        if not text or not result.success or result.value is None:
            continue
        # An assignment line ("price = 20") already shows its value; don't
        # append "= 20" a second time. Only bare expressions get the " = value".
        if result.assigned_name is not None:
            pairs.append(text)
        else:
            pairs.append(f"{text} = {format_result(result, line)}")
    return "\n".join(pairs)


def last_result_text(results: list[EvalResult]) -> str:
    """Formatted value of the last successful result, or `""` if none."""
    for result in reversed(results):
        if result.success and result.value is not None:
            return format_result(result)
    return ""
