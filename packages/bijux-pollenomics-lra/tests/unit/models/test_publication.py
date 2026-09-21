"""Publication input refusals preserve units and missingness."""

from __future__ import annotations

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
    with pytest.raises(ValidationError):
        replace(publication_inputs, **changes)


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
    with pytest.raises(ValidationError):
        replace(PublicationRevealsConfig("synthetic-bp-v1"), **changes)
