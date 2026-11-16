"""Production source reads have real descriptor and finite buffer boundaries."""

import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.production import validation


def test_production_read_refuses_oversize_before_buffering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.json"
    source.write_bytes(b"1234")
    monkeypatch.setattr(validation, "SOURCE_MAX_BYTES", 3, raising=False)
    with pytest.raises(ValueError, match="budget|bound"):
        validation.read_regular_file(source)


def test_production_read_refuses_fifo_substituted_at_real_open_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.json"
    source.write_bytes(b"{}")
    opening = os.open
    actual: list[int] = []

    def swapped(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if str(path) == source.name:
            source.unlink()
            os.mkfifo(source)
        descriptor = opening(path, flags, *args, **kwargs)
        if str(path) == source.name:
            assert flags & os.O_NONBLOCK
            actual.append(descriptor)
        return descriptor

    monkeypatch.setattr(os, "open", swapped)
    with pytest.raises(ValueError, match="regular|identity|changed"):
        validation.read_regular_file(source)
    assert len(actual) == 1
    for descriptor in actual:
        with pytest.raises(OSError):
            os.fstat(descriptor)
