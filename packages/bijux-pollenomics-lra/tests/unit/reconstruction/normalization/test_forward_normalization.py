"""Exact composition oracles for finite forward deposition masses."""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

from bijux_pollenomics_lra.api import ValidationError, forward_deposition


def _exact_composition(masses: np.ndarray) -> np.ndarray:
    """Round only final ratios of the actual binary64 input masses."""
    exact = [Fraction(float(value)) for value in masses]
    mass = sum(exact, Fraction())
    return np.array([float(value / mass) for value in exact])


@pytest.mark.parametrize("unit_scale", [1.0, 1e307, 4e307])
def test_common_deposition_units_preserve_composition_and_mass(
    unit_scale: float,
) -> None:
    # Two rings: unequal PPE and cover produce local masses 2, 3.
    # The independent regional background adds masses 0.5, 1, respectively.
    kernels = np.array([[2.0, 3.0], [4.0, 2.0]]) * unit_scale
    regional = np.array([0.5, 1.0]) * unit_scale
    expected_local = np.array([2.0, 3.0]) * unit_scale
    expected_total = np.array([2.5, 4.0]) * unit_scale
    result = forward_deposition([0.25, 0.75], regional, kernels, [1.0, 0.5], [2.0, 1.0])
    np.testing.assert_array_equal(result.local_deposition, expected_local)
    np.testing.assert_array_equal(result.regional_deposition, regional)
    np.testing.assert_array_equal(result.total_deposition, expected_total)
    np.testing.assert_allclose(
        result.pollen_fraction, _exact_composition(expected_total), rtol=2e-16, atol=0
    )
    assert np.isfinite(result.pollen_fraction).all()
    assert result.pollen_fraction.sum() == pytest.approx(1.0, abs=2e-16)


@pytest.mark.parametrize(
    "masses",
    [
        [1e308, 1e308],
        [1e308, 1e308, 0.0],
        [1e308, 1e308, 1e-15],
    ],
)
def test_overflowing_aggregate_has_exact_rational_composition(
    masses: list[float], monkeypatch: pytest.MonkeyPatch
) -> None:
    # No assumption that longdouble has more precision than float64 on macOS.
    monkeypatch.setattr(np, "longdouble", np.float64)
    regional = np.array(masses)
    expected = _exact_composition(regional)
    result = forward_deposition(
        np.full(regional.size, 1 / regional.size),
        regional,
        np.zeros((1, regional.size)),
        [1.0],
        np.ones(regional.size),
    )
    # Exact equality detects loss of the representable minimum-subnormal tail.
    np.testing.assert_array_equal(result.pollen_fraction, expected)
    np.testing.assert_array_equal(result.total_deposition, regional)
    np.testing.assert_array_equal(result.local_deposition, np.zeros(regional.size))
    assert np.isfinite(result.pollen_fraction).all()
    assert result.pollen_fraction.sum() == 1.0


def test_ordinary_finite_sum_preserves_existing_arithmetic() -> None:
    masses = np.array([0.3, 0.7, 1.1])
    result = forward_deposition(
        [0.25, 0.25, 0.5], masses, [[0.0, 0.0, 0.0]], [1.0], [1.0, 1.0, 1.0]
    )
    np.testing.assert_array_equal(result.pollen_fraction, masses / masses.sum())


def test_unrepresentable_individual_deposition_remains_refused() -> None:
    with (
        np.errstate(over="ignore"),
        pytest.raises(ValidationError, match="nonfinite or zero total mass"),
    ):
        forward_deposition([0.5, 0.5], [0.0, 0.0], [[1e308, 1e308]], [1.0], [4.0, 4.0])


def test_zero_deposition_remains_refused() -> None:
    with pytest.raises(ValidationError, match="zero total mass"):
        forward_deposition([0.5, 0.5], [0.0, 0.0], [[0.0, 0.0]], [1.0], [1.0, 1.0])
