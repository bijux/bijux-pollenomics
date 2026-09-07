"""Strict cardinality contracts."""

from __future__ import annotations

import pytest

from bijux_pollenomics.collection.contracts.cardinality import (
    require_nonnegative_count,
    resolve_declared_count,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord


def test_nonnegative_count_preserves_zero() -> None:
    assert require_nonnegative_count(0, field="records") == 0
    assert resolve_declared_count(
        {"record_count": 0},
        "record_count",
        field="records",
        absent_default=1,
    ) == 0


@pytest.mark.parametrize("value", [None, "", "0", False, True, -1, 0.0])
def test_nonnegative_count_refuses_malformed_declarations(value: object) -> None:
    with pytest.raises(ValueError, match="must be a nonnegative integer"):
        require_nonnegative_count(value, field="records")


def test_declared_count_uses_fallback_only_when_field_is_absent() -> None:
    assert resolve_declared_count(
        {}, "record_count", field="records", absent_default=1
    ) == 1
    with pytest.raises(ValueError, match="must be a nonnegative integer"):
        resolve_declared_count(
            {"record_count": None},
            "record_count",
            field="records",
            absent_default=1,
        )


def test_context_point_contract_rejects_invalid_count() -> None:
    with pytest.raises(ValueError, match="context point record_count"):
        ContextPointRecord(
            source="Source",
            layer_key="context",
            layer_label="Context",
            category="Context",
            country="Sweden",
            record_id="context-1",
            name="Context one",
            latitude=59,
            longitude=18,
            geometry_type="Point",
            subtitle="Context",
            description="Context record",
            source_url="",
            record_count=True,
            popup_rows=(),
        )
