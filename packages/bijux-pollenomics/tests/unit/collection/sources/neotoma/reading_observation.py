"""Observe actual descriptor opens alongside remaining direct pathname readers."""

from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import receipts

Opening = Callable[..., Any]
_SOURCE_OPEN: ContextVar[bool] = ContextVar("neotoma_source_open", default=False)


def capture_opening() -> Opening:
    """Capture the real secure opener before installing an observing callback."""
    secure, pathname = receipts._open_source, Path.open

    def opened(path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if _SOURCE_OPEN.get() and mode == "rb":
            if args or kwargs:
                raise TypeError(
                    "Descriptor observation accepts only binary source reads"
                )
            return secure(path)
        return pathname(path, mode, *args, **kwargs)

    return opened


def observe_opening(monkeypatch: pytest.MonkeyPatch, observed: Opening) -> None:
    """Count one real source open, keeping stream wrappers on the actual FD."""

    def pathname(path: Path, *args: Any, **kwargs: Any) -> Any:
        token = _SOURCE_OPEN.set(False)
        try:
            return observed(path, *args, **kwargs)
        finally:
            _SOURCE_OPEN.reset(token)

    def descriptor(path: Path) -> Any:
        token = _SOURCE_OPEN.set(True)
        try:
            return observed(path, "rb")
        finally:
            _SOURCE_OPEN.reset(token)

    monkeypatch.setattr(Path, "open", pathname)
    monkeypatch.setattr(receipts, "_open_source", descriptor)
