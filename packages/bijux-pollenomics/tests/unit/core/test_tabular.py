"""Tests for deterministic tabular record serialization."""

from __future__ import annotations

import pytest
from bijux_pollenomics.core.tabular import render_csv_rows


def test_render_csv_rows_preserves_schema_order_and_normalizes_values() -> None:
    rows = (
        {
            "identifier": "record-1",
            "accepted": True,
            "labels": ["direct", "dated"],
            "interval": (100, 200),
        },
        {
            "identifier": "record-2",
            "accepted": False,
            "labels": [],
            "interval": (),
        },
    )

    assert render_csv_rows(rows) == (
        "identifier,accepted,labels,interval\n"
        "record-1,true,direct;dated,100;200\n"
        "record-2,false,,\n"
    )


def test_render_csv_rows_returns_empty_text_for_no_records() -> None:
    assert render_csv_rows(()) == ""


def test_render_csv_rows_rejects_fields_outside_first_record_schema() -> None:
    rows = ({"identifier": "record-1"}, {"identifier": "record-2", "extra": 1})

    with pytest.raises(ValueError, match="fields not in fieldnames"):
        render_csv_rows(rows)
