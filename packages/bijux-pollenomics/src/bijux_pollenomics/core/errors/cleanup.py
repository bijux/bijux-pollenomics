"""Best-effort cleanup diagnostics cannot replace the failure being unwound."""

from __future__ import annotations

from collections.abc import Callable


def add_cleanup_note(primary: BaseException, note: Callable[[], str]) -> None:
    """Evaluate and append a diagnostic without interrupting remaining cleanup."""
    try:
        primary.add_note(note())
    except BaseException:
        # Diagnostics have less authority than the failure already being unwound.
        return
