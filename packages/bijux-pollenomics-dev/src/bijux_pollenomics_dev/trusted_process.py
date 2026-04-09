"""Run repository-owned commands through a small validated subprocess wrapper."""

from __future__ import annotations

from collections.abc import Sequence
import os
from pathlib import Path
import subprocess  # nosec B404

CommandArg = str | os.PathLike[str]


def _normalize_command(command: Sequence[CommandArg]) -> list[str]:
    if not command:
        raise ValueError("trusted command is empty")
    executable = Path(os.fspath(command[0])).expanduser()
    if not executable.is_absolute():
        raise ValueError(
            f"trusted command requires an absolute executable path: {command[0]!r}"
        )
    return [os.fspath(executable), *(os.fspath(part) for part in command[1:])]


def run_text(
    command: Sequence[CommandArg],
    *,
    cwd: Path | None = None,
    check: bool,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a trusted command and return its completed process record."""
    return subprocess.run(  # nosec B603
        _normalize_command(command),
        cwd=cwd,
        check=check,
        capture_output=capture_output,
        text=True,
    )
