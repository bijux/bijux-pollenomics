"""Analytic controls for the fixed-input admissibility diagnostic only."""

from fractions import Fraction

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.admissibility import (
    algebra,
)


def test_exact_boundary_with_unequal_ppe_and_counts() -> None:
    # n/PPE = (1, 3); equal background makes the feasible q interval [1/4,3/4].
    result = algebra([2, 3], [2, 1], ["0.5", "0.5"], [1, 1], [1, 1])
    assert result["conditional_nonnegative_cover_exists"] is True
    first, second = result["taxa"]
    assert first["lower_admissible_bound"] == Fraction(1, 4)
    assert first["upper_admissible_bound"] == Fraction(3, 4)
    assert first["implied_cover"] == 0 and second["implied_cover"] == 1
    assert first["lower_margin"] == 0 and second["upper_margin"] == 0


def test_signed_local_mismatch_remains_outside_physical_simplex() -> None:
    result = algebra([1, 7], [1, 1], ["0.5", "0.5"], [1, 1], [1, 1])
    assert result["conditional_nonnegative_cover_exists"] is False
    first, second = result["taxa"]
    assert first["below_lower"] is True and first["lower_margin"] == -Fraction(1, 8)
    assert second["above_upper"] is True and second["upper_margin"] == -Fraction(1, 8)
    assert first["implied_cover"] == -Fraction(1, 4)
    assert second["implied_cover"] == Fraction(5, 4)


def test_undefined_fixed_background_is_refused_without_imputed_cover() -> None:
    with pytest.raises(ValueError, match="denominator"):
        algebra([1, 7], [1, 1], ["0.5", "0.5"], [0, 0], [1, 1])
