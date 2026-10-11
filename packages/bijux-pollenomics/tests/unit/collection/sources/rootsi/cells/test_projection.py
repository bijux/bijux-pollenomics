"""Representation contracts independent of BIFF decoding implementation."""

from __future__ import annotations

import math

import pytest

from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics.collection.sources.rootsi.cells.models import (
    decoded,
    encoded,
    object_value,
)
from bijux_pollenomics.collection.sources.rootsi.cells.projection import (
    cell_record,
    validate_cell,
)


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        (0, ""),
        (1, ""),
        (1, "Å"),
        (2, 0.0),
        (2, -0.0),
        (2, 1.25),
        (2, -50.75),
        (2, math.inf),
        (2, math.nan),
        (3, 1.5),
        (4, 0),
        (4, 1),
        (5, 7),
        (6, ""),
        (8, "unknown"),
    ],
)
def test_typed_roundtrip(kind: int, value: object) -> None:
    """Safe JSON retains every supported category and explicit refused numbers."""
    record = cell_record(
        workbook_id="w",
        sheet_ordinal=0,
        row=0,
        column=0,
        cell_type=kind,
        value=value,
        xf_index=1,
    )
    reread = object_value(decoded(encoded(record)), "cell")
    assert encoded(validate_cell(reread)) == encoded(record)


@pytest.mark.parametrize(
    ("kind", "value"),
    [(2, True), (2, 1), (0, "not empty"), (4, True), (4, 2), (5, -1), (1, None)],
)
def test_malformed_decoder_values_refuse(kind: int, value: object) -> None:
    """Do not coerce decoder type contradictions into count-like values."""
    with pytest.raises(IntakeRefusal):
        cell_record(
            workbook_id="w",
            sheet_ordinal=0,
            row=0,
            column=0,
            cell_type=kind,
            value=value,
            xf_index=None,
        )


def test_number_and_locator_contradictions_refuse() -> None:
    """Rehashing cannot hide a disagreement between typed values and positions."""
    record = cell_record(
        workbook_id="w",
        sheet_ordinal=0,
        row=0,
        column=0,
        cell_type=2,
        value=1.25,
        xf_index=None,
    )
    for field, value in (
        ("decoded_value", 2.0),
        ("row", True),
        ("cell_id", "replacement"),
        ("binary64_hex", "0x1.4000000000000p+1"),
    ):
        with pytest.raises(IntakeRefusal):
            validate_cell({**record, field: value})
