"""Publication input refusals preserve units and missingness."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import numpy as np
import pytest

from bijux_pollenomics_lra.api import (
    MultisiteRevealsInput,
    PublicationRevealsConfig,
    ValidationError,
)


@pytest.mark.parametrize(
    "changes",
    [
        {"counts": np.full((2, 1, 3), 0.5)},
        {"counts": np.zeros((2, 1, 3))},
        {"counts": np.full((2, 1, 3), "10")},
        {"availability": np.ones((2, 1), dtype=int)},
        {"basin_type": np.array([["bog"], ["lake"]])},
        {"basin_radius_m": np.array([[0.0], [100.0]])},
        {"ppe_covariance": np.diag([-1.0, 0.0, 0.0])},
        {"bin_bounds_bp": np.array([[100.0, 0.0]])},
        {"site_ids": ("duplicate", "duplicate")},
    ],
)
def test_invalid_publication_input_is_refused(
    publication_inputs: MultisiteRevealsInput, changes: dict[str, object]
) -> None:
    dynamic_replace: Callable[..., MultisiteRevealsInput] = replace
    with pytest.raises(ValidationError):
        dynamic_replace(publication_inputs, **changes)


def test_source_arrays_are_owned_and_readonly(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    inputs = publication_inputs
    assert not inputs.counts.flags.writeable
    assert not inputs.availability.flags.writeable
    assert not inputs.ppe.flags.writeable


@pytest.mark.parametrize(
    "changes",
    [{"time_bin_profile": ""}, {"wind_speed_m_s": True}, {"profile": "corrected"}],
)
def test_no_implicit_publication_profile(changes: dict[str, object]) -> None:
    dynamic_replace: Callable[..., PublicationRevealsConfig] = replace
    with pytest.raises(ValidationError):
        dynamic_replace(PublicationRevealsConfig("synthetic-bp-v1"), **changes)


SOURCE_ARRAY_FIELDS = (
    "counts",
    "basin_radius_m",
    "bin_bounds_bp",
    "ppe",
    "ppe_covariance",
    "fall_speed_m_s",
    "availability",
    "basin_type",
)


@pytest.mark.parametrize("field", SOURCE_ARRAY_FIELDS)
def test_unresolved_source_mask_cannot_become_observed_support(
    publication_inputs: MultisiteRevealsInput, field: str
) -> None:
    original = getattr(publication_inputs, field)
    mask = np.zeros(original.shape, dtype=bool)
    mask.flat[0] = True
    masked = np.ma.array(original, mask=mask)
    dynamic_replace: Callable[..., MultisiteRevealsInput] = replace
    with pytest.raises(ValidationError, match=field + " contains masked"):
        dynamic_replace(publication_inputs, **{field: masked})


@pytest.mark.parametrize("field", SOURCE_ARRAY_FIELDS)
def test_false_source_masks_preserve_observed_and_unavailable_values(
    publication_inputs: MultisiteRevealsInput, field: str
) -> None:
    counts = publication_inputs.counts.astype(float)
    counts[1] = np.nan
    expected = replace(
        publication_inputs,
        counts=counts,
        availability=np.array([[True], [False]]),
        basin_radius_m=np.array([[25.0], [np.nan]]),
        basin_type=np.array([["peatland"], [None]], dtype=object),
    )
    original = getattr(expected, field)
    masked = np.ma.array(original, mask=np.zeros(original.shape, dtype=bool))
    dynamic_replace: Callable[..., MultisiteRevealsInput] = replace
    actual = dynamic_replace(expected, **{field: masked})
    for name in ("site_ids", "bin_ids", "taxon_ids"):
        assert getattr(actual, name) == getattr(expected, name)
    for name in SOURCE_ARRAY_FIELDS:
        observed = getattr(actual, name)
        baseline = getattr(expected, name)
        np.testing.assert_array_equal(observed, baseline)
        assert observed.dtype == baseline.dtype
        assert observed.tobytes() == baseline.tobytes()
        assert not observed.flags.writeable
