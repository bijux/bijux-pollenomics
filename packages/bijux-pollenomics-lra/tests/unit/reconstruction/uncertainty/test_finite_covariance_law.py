"""Exact finite-distribution moments distinguish the fixed-site delta approximation."""

from __future__ import annotations

from fractions import Fraction
from math import comb

import numpy as np
import pytest

import bijux_pollenomics_lra as lra
from bijux_pollenomics_lra.reconstruction.fixed_site_covariance import PROFILE


def _finite_covariance_law(
    ppe_states: tuple[tuple[Fraction, Fraction], ...],
) -> tuple[Fraction, Fraction, int]:
    """Enumerate independent fixed-margin counts and an independent shared PPE law.

    K=((1,2),(3,1)); the two binomials have N=(3,4), p=(1/3,1/2).
    These are constructed estimator inputs, not a physical-cover truth model.
    """
    law: list[tuple[Fraction, Fraction]] = []
    for first in range(4):
        for second in range(5):
            probability = (
                comb(3, first)
                * Fraction(1, 3) ** first
                * Fraction(2, 3) ** (3 - first)
                * comb(4, second)
                * Fraction(1, 2) ** 4
                / len(ppe_states)
            )
            for ppe in ppe_states:
                weights = (
                    (first + Fraction(second, 3)) / ppe[0],
                    (Fraction(3 - first, 2) + 4 - second) / ppe[1],
                )
                assert sum(weights) > 0
                cover = weights[0] / sum(weights)
                assert 0 <= cover <= 1
                law.append((probability, cover))
    assert sum(probability for probability, _ in law) == 1
    mean = sum((probability * cover for probability, cover in law), Fraction())
    variance = sum(
        (probability * (cover - mean) ** 2 for probability, cover in law),
        Fraction(),
    )
    return mean, variance, len(law)


@pytest.mark.parametrize("shared_ppe", [False, True])
def test_exact_finite_law_distinguishes_moments_from_delta_approximation(
    shared_ppe: bool,
) -> None:
    """Exact finite-law moments and first-order propagation are different targets."""
    ppe_states = (
        ((Fraction(9, 10), Fraction(21, 10)), (Fraction(11, 10), Fraction(19, 10)))
        if shared_ppe
        else ((Fraction(1), Fraction(2)),)
    )
    exact_mean, exact_variance, states = _finite_covariance_law(ppe_states)
    ppe_mean = tuple(
        sum((row[i] for row in ppe_states), Fraction()) / len(ppe_states)
        for i in range(2)
    )
    assert ppe_mean == (Fraction(1), Fraction(2))
    ppe_covariance = tuple(
        tuple(
            sum(
                ((row[i] - ppe_mean[i]) * (row[j] - ppe_mean[j]) for row in ppe_states),
                Fraction(),
            )
            / len(ppe_states)
            for j in range(2)
        )
        for i in range(2)
    )
    # Independent scalar derivatives along each site's fixed-count-total axis.
    factors = ((Fraction(1), Fraction(1, 4)), (Fraction(1, 3), Fraction(1, 2)))
    weights = (Fraction(5, 3), Fraction(3, 2))
    total = sum(weights)
    point = weights[0] / total
    counting_variance = sum(
        (
            ((1 - point) * first + point * second) ** 2 / total**2 * variance
            for (first, second), variance in zip(
                factors, (Fraction(2, 3), Fraction(1)), strict=True
            )
        ),
        Fraction(),
    )
    gradient = (-point * (1 - point), point * (1 - point) / 2)
    parameter_variance = sum(
        (
            gradient[i] * ppe_covariance[i][j] * gradient[j]
            for i in range(2)
            for j in range(2)
        ),
        Fraction(),
    )
    delta_variance = counting_variance + parameter_variance
    actual = lra.fixed_site_cover_covariance(
        np.array([[1, 2], [2, 2]]),
        np.array([[1, 2], [3, 1]]),
        np.array([1.0, 2.0]),
        np.array(ppe_covariance, dtype=float),
        taxon_measured=np.ones((2, 2), dtype=bool),
    )
    np.testing.assert_allclose(
        actual.cover, [float(point), float(1 - point)], rtol=0, atol=1e-15
    )
    for name, variance in (
        ("counting_covariance", counting_variance),
        ("ppe_covariance", parameter_variance),
        ("total_covariance", delta_variance),
    ):
        expected = float(variance) * np.array([[1, -1], [-1, 1]])
        np.testing.assert_allclose(getattr(actual, name), expected, rtol=0, atol=1e-15)
    assert actual.profile == PROFILE
    assert states == (40 if shared_ppe else 20)
    assert exact_variance > 0 and exact_mean != point
    assert exact_variance != delta_variance
    print(
        f"finite-law shared_ppe={shared_ppe} states={states} "
        f"exact_mean={exact_mean} exact_variance={exact_variance} "
        f"delta_point={point} delta_variance={delta_variance} "
        f"mean_gap={float(exact_mean - point):.17g} "
        f"variance_gap={float(exact_variance - delta_variance):.17g}"
    )
