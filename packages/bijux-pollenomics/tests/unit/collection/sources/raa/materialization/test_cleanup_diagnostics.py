"""SQLite cleanup retains the consumer failure and releases the admitted descriptor."""

from contextlib import suppress
import os
from pathlib import Path
import sqlite3
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.raa.materialization import reading
from bijux_pollenomics.collection.sources.raa.materialization.custody import (
    SourceConnection,
)
from bijux_pollenomics.core.filesystem import BoundedInputTree

from .test_reading import fixture_database


class _BrokenDiagnostic(OSError):
    def __str__(self) -> str:
        raise RuntimeError("cleanup formatting failed")


@pytest.mark.parametrize("boundary", ["first_cleanup", "later_cleanup"])
@pytest.mark.parametrize("diagnostic", ["notes", "annotation", "format"])
def test_sqlite_cleanup_diagnostics_preserve_primary_and_close_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, boundary: str, diagnostic: str
) -> None:
    class Primary(OSError):
        def add_note(self, note: str) -> None:
            if diagnostic == "annotation":
                raise RuntimeError("annotation failed")
            super().add_note(note)

    primary = Primary("primary consumer failure")
    if diagnostic == "notes":
        primary.__notes__ = ()  # type: ignore[assignment]
    secondary = (
        _BrokenDiagnostic("secondary")
        if diagnostic == "format"
        else OSError("secondary cleanup failure")
    )
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    exiting = False
    descriptors: list[int] = []
    real_connect = sqlite3.connect
    real_validate = BoundedInputTree.validate

    class Connection(SourceConnection):
        def close(self) -> None:
            super().close()
            if exiting:
                raise secondary

    def connected(database: str, **kwargs: Any) -> Any:
        descriptors.append(int(database.split("?", 1)[0].rsplit("/", 1)[1]))
        return real_connect(database, **{**kwargs, "factory": Connection})

    def validated(tree: Any) -> None:
        if exiting and boundary == "later_cleanup":
            raise secondary
        real_validate(tree)

    monkeypatch.setattr(sqlite3, "connect", connected)
    monkeypatch.setattr(BoundedInputTree, "validate", validated)
    try:
        with (
            pytest.raises(Primary) as caught,
            reading.read_only_database(
                path, expected_sha256=pin, expected_byte_count=size
            ),
        ):
            exiting = True
            raise primary
        assert caught.value is primary
        assert len(descriptors) == 1
        with pytest.raises(OSError):
            os.fstat(descriptors[0])
    finally:
        for descriptor in descriptors:
            with suppress(OSError):
                os.close(descriptor)
