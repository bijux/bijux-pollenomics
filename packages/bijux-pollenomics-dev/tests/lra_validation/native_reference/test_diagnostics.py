"""Retained vector diagnostics preserve failures, nonfinite masks and exact axes."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.lra_validation.native_reference.diagnostics import (
    vector_diagnostics,
)
from bijux_pollenomics_dev.lra_validation.native_reference.diagnostics_verification import (
    verify_metrics,
)


def test_finite_differences_remain_visible_within_original_tolerance() -> None:
    result = vector_diagnostics(
        np.array([1.0 + 1e-8, 0.0]), np.array([1.0, 0.0]), rtol=1e-7, atol=0.0
    )
    assert result["status"] == "passed"
    assert result["differing_entry_count"] == 1
    assert result["max_absolute_error"] == pytest.approx(1e-8)
    assert result["max_relative_error"] == pytest.approx(1e-8)
    assert result["out_of_tolerance_indices"] == []


def test_zero_reference_residual_has_no_invented_relative_denominator() -> None:
    result = vector_diagnostics(
        np.array([1e-8, 2.0]), np.array([0.0, 1.0]), rtol=0.0, atol=1e-7
    )
    assert result["status"] == "failed"
    assert result["zero_reference_difference_indices"] == [0]
    assert result["differing_entries"][0]["relative_error"] is None
    assert result["max_relative_error"] == 1.0
    assert result["out_of_tolerance_indices"] == [1]


def test_nonfinite_positions_and_signs_cannot_be_erased() -> None:
    result = vector_diagnostics(
        np.array([np.nan, np.inf, -np.inf, 0.0]),
        np.array([np.nan, -np.inf, -np.inf, np.nan]),
        rtol=1.0,
        atol=1.0,
    )
    assert result["status"] == "failed"
    assert result["nonfinite_mismatch_indices"] == [1, 3]
    assert result["out_of_tolerance_indices"] == [1, 3]
    assert result["differing_entries"][0]["actual"] == "Infinity"
    assert result["differing_entries"][0]["expected"] == "-Infinity"


def test_exact_coordinates_refuse_even_with_large_approximate_tolerance() -> None:
    result = vector_diagnostics(
        np.array([1.0, 2.0]),
        np.array([1.01, 2.01]),
        rtol=1.0,
        atol=1.0,
        exact_indices=(1,),
    )
    assert result["out_of_tolerance_indices"] == [1]
    assert result["differing_entry_count"] == 2


def test_ordered_labels_require_exact_identity() -> None:
    result = vector_diagnostics(
        np.array(["Betula", "Poaceae"]),
        np.array(["Poaceae", "Betula"]),
        rtol=0.0,
        atol=0.0,
    )
    assert result["comparison_kind"] == "exact_strings"
    assert result["out_of_tolerance_indices"] == [0, 1]
    assert result["max_absolute_error"] is None


@pytest.mark.parametrize(
    "options",
    [
        {"rtol": -1.0},
        {"atol": np.inf},
        {"exact_indices": (2,)},
        {"exact_indices": (0, 0)},
        {"exact_indices": (True,)},
    ],
)
def test_invalid_comparison_protocol_refuses(options: dict[str, Any]) -> None:
    protocol = {"rtol": 0.0, "atol": 0.0, **options}
    with pytest.raises(ValueError):
        vector_diagnostics(np.array([1.0]), np.array([1.0]), **protocol)


def test_different_shapes_are_not_flattened_into_apparent_agreement() -> None:
    with pytest.raises(ValueError, match="one-dimensional"):
        vector_diagnostics(np.array([[1.0, 2.0]]), np.array([1.0, 2.0]), rtol=0, atol=0)


@pytest.mark.parametrize("tamper", ["maximum", "entry_value", "entry_index"])
def test_independent_scalar_review_refuses_modified_diagnostics(tamper: str) -> None:
    result = vector_diagnostics(
        np.array([1.0, 0.0]), np.array([2.0, 0.0]), rtol=0.0, atol=0.0
    )
    assert verify_metrics([1.0, 0.0], [2.0, 0.0], result) == 2
    if tamper == "maximum":
        result["max_relative_error"] = 0.0
    elif tamper == "entry_value":
        result["differing_entries"][0]["actual"] = 2.0
    else:
        result["differing_entries"][0]["index"] = 1
    with pytest.raises(ValueError):
        verify_metrics([1.0, 0.0], [2.0, 0.0], result)


@pytest.mark.parametrize(
    "field",
    [
        "zero_reference_difference_indices",
        "nonfinite_mismatch_indices",
        "expected_nonfinite_entries",
        "actual_nonfinite_entries",
        "comparison_kind",
        "relative_error_denominator",
    ],
)
def test_independent_review_refuses_each_mask_or_kind_claim(field: str) -> None:
    actual = [0.0, float("nan"), float("inf"), 1.0]
    expected = [1.0, float("nan"), -float("inf"), 0.0]
    report = vector_diagnostics(
        np.asarray(actual), np.asarray(expected), rtol=0.0, atol=0.0
    )
    assert verify_metrics(actual, expected, report) == 4
    report[field] = (
        "different"
        if field in {"comparison_kind", "relative_error_denominator"}
        else []
    )
    with pytest.raises(ValueError):
        verify_metrics(actual, expected, report)
