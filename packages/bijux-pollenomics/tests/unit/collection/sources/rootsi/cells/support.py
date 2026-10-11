"""Explicit synthetic decoded objects; these do not stand in for XLS parser proof."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.rootsi.authority import ARCHIVE_SHA256
from bijux_pollenomics.collection.sources.rootsi.cells import reading
from bijux_pollenomics.collection.sources.rootsi.cells.decoding import Book, Cell, Sheet
from bijux_pollenomics.collection.sources.rootsi.cells.models import (
    Capture,
    WorkbookInput,
    decoded,
    encoded,
    object_value,
)
from bijux_pollenomics.collection.sources.rootsi.cells.publication import file_identity


@contextmanager
def synthetic_capture_authority(capture: Capture) -> Iterator[None]:
    """Scope the retained-reader pin to this explicit decoded-object fixture only.

    Public prepare authority is never patched; native hash/size/mutation checks
    remain active. Actual XLS integration uses the historical pin unmodified.
    """
    with pytest.MonkeyPatch.context() as context:
        context.setattr(reading, "RETAINED_INVENTORY_SHA256", capture.inventory_sha256)
        yield


@dataclass
class SyntheticCell:
    """A public-decoder protocol value, not a native workbook cell."""

    ctype: int
    value: object
    xf_index: int | None = 1


class SyntheticSheet:
    """Small position-complete synthetic sheet."""

    def __init__(self, name: str, rows: list[list[SyntheticCell]]) -> None:
        self.name = name
        self.rows = rows
        self.nrows = len(rows)
        self.ncols = len(rows[0]) if rows else 0
        self.merged_cells: list[tuple[int, int, int, int]] = []

    def cell(self, rowx: int, colx: int) -> Cell:
        """Return the synthetic object at its exact position."""
        return self.rows[rowx][colx]


class SyntheticBook:
    """Workbook with all supported cell kinds and an empty sheet."""

    datemode = 0

    def __init__(self) -> None:
        self.released = False
        self.pages: list[Sheet] = [
            SyntheticSheet(
                "Åge",
                [
                    [
                        SyntheticCell(0, ""),
                        SyntheticCell(1, "  rå \U0001f33f "),
                        SyntheticCell(2, 0.0),
                        SyntheticCell(2, -0.0),
                        SyntheticCell(2, 1.25),
                        SyntheticCell(2, -50.75),
                        SyntheticCell(3, 42000.5),
                        SyntheticCell(4, 1),
                        SyntheticCell(5, 7),
                        SyntheticCell(6, ""),
                        SyntheticCell(1, ""),
                    ]
                ],
            ),
            SyntheticSheet("empty", []),
        ]

    def sheets(self) -> list[Sheet]:
        """Retain source order."""
        return self.pages

    def release_resources(self) -> None:
        """Record the public parser cleanup call."""
        self.released = True


class SyntheticParser:
    """An explicit decoder-boundary double, never a BIFF implementation."""

    def __init__(self) -> None:
        self.book = SyntheticBook()

    def open_workbook(self, *, file_contents: bytes, formatting_info: bool) -> Book:
        """Require the source buffer and formatting scope."""
        assert file_contents == b"synthetic decoder-boundary bytes"
        assert formatting_info is True
        return self.book


def capture_fixture(tmp_path: Path) -> Capture:
    """Construct an internal synthetic capture; public real-capture pin is untouched."""
    raw = tmp_path / "raw"
    raw.mkdir()
    workbook = raw / "synthetic.xls"
    payload = b"synthetic decoder-boundary bytes"
    workbook.write_bytes(payload)
    inventory = raw / "inventory.json"
    rows = [
        {
            "archive_member": "rootsi/synthetic.xls",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "byte_count": len(payload),
        }
    ]
    rows.extend(
        {
            "archive_member": f"rootsi/unused-{index}.xls",
            "sha256": "a" * 64,
            "byte_count": 1,
        }
        for index in range(78)
    )
    inventory.write_bytes(
        encoded(
            {
                "fixture_kind": "synthetic_decoder_boundary",
                "archive_sha256": ARCHIVE_SHA256,
                "source_unchanged": True,
                "workbook_count": 79,
                "workbooks": rows,
            }
        )
    )
    return Capture(
        inventory,
        hashlib.sha256(inventory.read_bytes()).hexdigest(),
        inventory.stat().st_size,
        ARCHIVE_SHA256,
        "selected_workbooks",
        79,
        (
            WorkbookInput(
                "rootsi/synthetic.xls",
                workbook,
                hashlib.sha256(payload).hexdigest(),
                len(payload),
            ),
        ),
    )


def repin(directory: Path) -> str:
    """Rehash a changed retained bundle to challenge internal consistency."""
    manifest = object_value(
        decoded((directory / "manifest.json").read_bytes()), "manifest"
    )
    members = object_value(manifest["members"], "members")
    manifest["members"] = {name: file_identity(directory / name) for name in members}
    (directory / "manifest.json").write_bytes(encoded(manifest))
    return hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest()
