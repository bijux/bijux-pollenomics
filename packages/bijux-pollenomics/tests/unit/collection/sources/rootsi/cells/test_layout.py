"""Native layout postures remain distinct from cached-value and scientific authority."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics.collection.sources.rootsi.cells.layout import (
    LayoutBook,
    LayoutSheet,
    worksheet_layout_records,
)

from .support import SyntheticParser, capture_fixture


def decoder_fixture() -> SyntheticParser:
    decoder = SyntheticParser()
    cast(LayoutBook, decoder.book).codepage = 1252
    cast(LayoutBook, decoder.book).encoding = "cp1252"
    for ordinal, sheet in enumerate(decoder.book.pages):
        cast(LayoutSheet, sheet).visibility = ordinal
    return decoder


@pytest.mark.parametrize("visibility", [0, 1, 2])
def test_hidden_and_empty_layout_is_retained(tmp_path: Path, visibility: int) -> None:
    capture = capture_fixture(tmp_path)
    decoder = decoder_fixture()
    cast(LayoutSheet, decoder.book.pages[0]).visibility = visibility
    rows = list(
        worksheet_layout_records(capture.workbooks[0], capture.archive_sha256, decoder)
    )
    assert len(rows) == 2
    assert rows[0]["sheet_visibility_code"] == visibility
    assert rows[1]["sheet_visibility"] == "hidden"
    assert rows[1]["rectangle_positions"] == 0
    assert rows[0]["codepage"] == 1252 and rows[0]["decoder_encoding"] == "cp1252"
    assert rows[0]["cached_error_code_counts"] == {"7": 1}
    assert rows[0]["cached_values_recalculated"] is False
    assert rows[0]["formula_origin"] == "unavailable"
    assert rows[0]["physical_biff_record_presence"] == "unavailable"
    assert rows[0]["scientific_admission"] == "refused"
    assert decoder.book.released


@pytest.mark.parametrize("visibility", [-1, 3, True])
def test_invalid_visibility_refuses_and_releases(
    tmp_path: Path, visibility: object
) -> None:
    capture = capture_fixture(tmp_path)
    decoder = decoder_fixture()
    cast(LayoutSheet, decoder.book.pages[0]).visibility = cast(int, visibility)
    with pytest.raises(IntakeRefusal):
        list(
            worksheet_layout_records(
                capture.workbooks[0], capture.archive_sha256, decoder
            )
        )
    assert decoder.book.released


@pytest.mark.parametrize("corruption", ["codepage", "merged", "duplicate_sheet"])
def test_unavailable_or_contradictory_layout_refuses(
    tmp_path: Path, corruption: str
) -> None:
    capture = capture_fixture(tmp_path)
    decoder = decoder_fixture()
    if corruption == "codepage":
        cast(LayoutBook, decoder.book).codepage = True
    elif corruption == "merged":
        decoder.book.pages[0].merged_cells = [(0, 0, 0, 1)]
    else:
        decoder.book.pages[1].name = decoder.book.pages[0].name
    with pytest.raises(IntakeRefusal):
        list(
            worksheet_layout_records(
                capture.workbooks[0], capture.archive_sha256, decoder
            )
        )
    assert decoder.book.released
