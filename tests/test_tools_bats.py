"""Static compatibility checks for batch files exposed to Tickets Watcher."""

from pathlib import Path
import re

import pytest


TOOLS = Path(__file__).parents[1] / "tools"
FILE_READ_PROMPT = re.compile(r"(?i)\bset\s+/p\b(?![^\r\n&|]*=[ \t]*<)")


def _runnable_bats() -> list[Path]:
    bats = []
    for path in TOOLS.rglob("*"):
        if (
            path.suffix.lower() not in {".bat", ".cmd"}
            or any(part.startswith(".") for part in path.relative_to(TOOLS).parts)
            or "create_media/output" in path.as_posix()
        ):
            continue
        lines = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith(("REM ", "rem ", "::"))
        ]
        if not all(
            line.lower() == "@echo off" or re.match(r"(?i)^set\s+\w+=", line)
            for line in lines
        ):
            bats.append(path)
    return sorted(bats)


RUNNABLE_BATS = _runnable_bats()


@pytest.mark.parametrize("path", RUNNABLE_BATS, ids=lambda path: path.relative_to(TOOLS).as_posix())
def test_ends_with_explicit_exit_code(path: Path) -> None:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert re.search(r"(?i)(?:^|&)\s*@?exit\s+/b\s+\S+\s*$", lines[-1])


@pytest.mark.parametrize("path", RUNNABLE_BATS, ids=lambda path: path.relative_to(TOOLS).as_posix())
def test_has_no_blocking_command(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        command = line.strip()
        if not command or command.lower().startswith(("rem ", "::")):
            continue
        assert not re.search(r"(?i)\b(?:pause|choice)\b", command)
        assert not re.search(r"(?i)^\s*@?start\b(?![^\r\n]*\s/wait\b)", command)
        assert not FILE_READ_PROMPT.search(command)


@pytest.mark.parametrize("path", RUNNABLE_BATS, ids=lambda path: path.relative_to(TOOLS).as_posix())
def test_uses_crlf_line_endings(path: Path) -> None:
    content = path.read_bytes()
    assert content.count(b"\n") == content.count(b"\r\n")
