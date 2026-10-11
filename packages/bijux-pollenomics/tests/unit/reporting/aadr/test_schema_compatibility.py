"""Compatibility typing and refusal behavior for AADR schema selectors."""

from __future__ import annotations

import pytest

from bijux_pollenomics.reporting.aadr.schema import (
    find_column,
    find_optional_column,
    resolve_schema,
)
from bijux_pollenomics.reporting.models import SchemaError

_REQUIRED_FIELDS = (
    "Genetic ID",
    "Master ID",
    "Group ID",
    "Locality",
    "Political Entity",
    "Lat.",
    "Long.",
    "Publication abbreviation",
    "Full Date",
    "Date mean in BP",
    "Data type",
    "Molecular Sex",
)


def test_schema_selector_preserves_required_and_optional_column_types() -> None:
    schema = resolve_schema(_REQUIRED_FIELDS)
    assert schema["genetic_id"] == "Genetic ID"
    assert schema["year_first_published"] is None
    assert schema["date_stddev_bp"] is None
    assert find_column(_REQUIRED_FIELDS, "Genetic ID") == "Genetic ID"
    assert find_column(_REQUIRED_FIELDS, "Date standard deviation in BP") is None
    assert find_optional_column(_REQUIRED_FIELDS, "Year first published") is None


def test_schema_selector_wraps_missing_required_column_as_schema_error() -> None:
    fields = tuple(field for field in _REQUIRED_FIELDS if field != "Genetic ID")
    with pytest.raises(SchemaError, match="Genetic ID"):
        resolve_schema(fields)


def test_schema_selector_keeps_unknown_lookup_optional_only() -> None:
    with pytest.raises(SchemaError, match="Could not find any"):
        find_column(_REQUIRED_FIELDS, "Unknown column")
    assert find_optional_column(_REQUIRED_FIELDS, "Unknown column") is None
