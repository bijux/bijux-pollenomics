"""Retain exact types and differences without approving normalization semantics."""

from __future__ import annotations

from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.sead.chronology_annotations.comparison import (
    compare_field,
)


@pytest.mark.parametrize(
    "raw,stored,category",
    [
        (None, "", "null_to_empty_string"),
        (None, False, "null_to_boolean"),
        (None, 0, "null_to_other_value"),
        (True, 1, "boolean_type_changed"),
        (True, False, "boolean_value_changed"),
        (False, 0, "boolean_type_changed"),
        (1845.0, 1845, "numeric_representation_changed_equal_value"),
        (1.75, 1, "numeric_value_changed"),
        (" source ", "source", "text_whitespace_changed"),
        ("a", "b", "text_value_changed"),
        ([1], {"value": 1}, "json_type_or_value_changed"),
        (-0.0, 0.0, "numeric_representation_changed_equal_value"),
    ],
)
def test_exact_difference_categories_do_not_approve_equivalence(
    raw: object, stored: object, category: str
) -> None:
    report = compare_field("field", raw, {"field": stored})
    assert report["category"] == category
    assert report["stored_present"] is True
    assert report["scientific_equivalence_approved"] is False


def test_unknown_flag_does_not_become_a_known_false_native_flag() -> None:
    result = compare_field("low_is_uncertain", None, {"low_is_uncertain": False})
    assert result["raw_type"] == "null" and result["stored_type"] == "boolean"
    assert result["native_unknown_flag"] is True
    assert result["category"] == "null_to_boolean"


@pytest.mark.parametrize("value", [None, False, 0, 1.0, "", [], {}])
def test_exact_native_value_remains_exact_with_original_type(value: Any) -> None:
    result = compare_field("field", value, {"field": value})
    assert result["category"] == "exact"
    assert result["scientific_equivalence_approved"] is False


def test_omission_is_distinct_from_a_present_native_null() -> None:
    absent = compare_field("field", None, {})
    present = compare_field("field", None, {"field": None})
    assert absent["category"] == "omitted" and absent["stored_present"] is False
    assert present["category"] == "exact" and present["stored_present"] is True


def test_large_integer_value_is_not_equal_after_float_rounding() -> None:
    result = compare_field("field", 9007199254740993, {"field": 9007199254740992.0})
    assert result["category"] == "numeric_value_changed"
