"""Full body validation is independent of line wrapping and selected window size."""

from dataclasses import replace
from io import BytesIO

import pytest

from bijux_pollenomics.collection.sources.hyde.ascii import (
    AsciiWindowLimits,
    AsciiWindowSelection,
)
from bijux_pollenomics.collection.sources.hyde.ascii.parsing import (
    parse_header,
    select_cells,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

from .test_preparation import BODY, HEADER


@pytest.mark.parametrize("chunk", [1, 2, 7, 19, 1024])
def test_wrapping_and_chunk_boundaries_preserve_source_indices(chunk: int) -> None:
    stream = BytesIO(HEADER + BODY.replace(b" ", b"\n\t"))
    limits = AsciiWindowLimits(chunk_bytes=chunk)
    header = parse_header(stream, limits)
    selection = AsciiWindowSelection("a.zip", 0, "a.asc", 0, 2, 1, 3)
    assert select_cells(stream, header, selection, limits) == (
        ("0", "1.2500", "-0", "-9999.0"),
        (False, False, False, True),
    )


@pytest.mark.parametrize(
    "body",
    [
        b"1 2 3 4 5",
        b"1 2 3 4 5 6 7",
        b"1 2 3 4 5 NaN",
        b"1 2 3 4 5 inf",
        b"1 2 3 4 5 " + b"1" * 129,
        b"1 2 3 4 5 \xff",
    ],
)
def test_invalid_unselected_trailing_data_refuses(body: bytes) -> None:
    stream = BytesIO(HEADER + body)
    limits = AsciiWindowLimits(chunk_bytes=3)
    header = parse_header(stream, limits)
    with pytest.raises(IntakeRefusal):
        select_cells(
            stream,
            header,
            AsciiWindowSelection("a.zip", 0, "a.asc", 0, 1, 0, 1),
            limits,
        )


@pytest.mark.parametrize(
    "old,new",
    [
        (b"ncols 3", b"ncols 0"),
        (b"nrows 2", b"nrows 2.0"),
        (b"cellsize 0.0833333", b"cellsize 0"),
        (b"xllcorner", b"xllcenter"),
        (b"NODATA_value -9999", b"nrows 2"),
        (b"yllcorner -90", b"yllcorner NaN"),
    ],
)
def test_explicit_header_profile_refuses_unsupported_or_invalid_header(
    old: bytes, new: bytes
) -> None:
    with pytest.raises(IntakeRefusal):
        parse_header(BytesIO(HEADER.replace(old, new)), AsciiWindowLimits())


def test_window_outside_source_and_cell_limits_refuse() -> None:
    limits = AsciiWindowLimits()
    for selection in [
        AsciiWindowSelection("a.zip", 0, "a.asc", 0, 3, 0, 1),
        AsciiWindowSelection("a.zip", 0, "a.asc", 0, 2, 0, 3),
    ]:
        stream = BytesIO(HEADER + BODY)
        header = parse_header(stream, limits)
        with pytest.raises(IntakeRefusal):
            select_cells(
                stream, header, selection, replace(limits, maximum_selected_cells=2)
            )
