"""Independent mass-balance counterexamples for forward pollen prediction."""

from __future__ import annotations

import numpy as np
import pytest

from bijux_pollenomics_lra.api import ValidationError, forward_deposition


def test_unequal_ppe_local_and_regional_mass_remain_separate() -> None:
    cover = np.array([0.25, 0.75])
    regional = np.array([0.5, 1.0])
    kernels = np.array([[2.0, 3.0], [4.0, 2.0]])
    result = forward_deposition(cover, regional, kernels, [1.0, 0.5], [2.0, 1.0])
    np.testing.assert_allclose(result.local_deposition, [2.0, 3.0])
    np.testing.assert_allclose(result.total_deposition, [2.5, 4.0])
    np.testing.assert_allclose(result.pollen_fraction, [2.5 / 6.5, 4.0 / 6.5])
    result.regional_deposition[0] = 20.0
    assert regional[0] == 0.5
    assert result.method_profile == "disqover-0.9.14-homogeneous-local-forward"


@pytest.mark.parametrize(
    "field,value",
    [
        ("local_cover", [25.0, 75.0]),
        ("regional_deposition", [-1.0, 1.0]),
        ("local_k", [[1.0, np.nan]]),
        ("local_k", [[1.0]]),
        ("terrestrial_fraction", [1.1]),
        ("ppe", [0.0, 1.0]),
        ("local_k", []),
        ("ppe", [1.0]),
    ],
)
def test_forward_refuses_unsupported_mass_or_shape(field: str, value: object) -> None:
    inputs = {
        "local_cover": [0.25, 0.75],
        "regional_deposition": [0.0, 0.0],
        "local_k": [[2.0, 3.0]],
        "terrestrial_fraction": [1.0],
        "ppe": [2.0, 1.0],
    }
    inputs[field] = value
    with pytest.raises(ValidationError):
        forward_deposition(**inputs)


def test_zero_mass_is_a_refusal_not_nan_prediction() -> None:
    with pytest.raises(ValidationError, match="zero total mass"):
        forward_deposition([0.25, 0.75], [0.0, 0.0], [[0.0, 0.0]], [1.0], [2.0, 1.0])
