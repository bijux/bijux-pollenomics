"""Independent scalar closure and uncertainty under heterogeneous site weights."""

from __future__ import annotations

from fractions import Fraction
from math import sqrt

import numpy as np
import pytest

from bijux_pollenomics_lra.reconstruction.uncertainty.joint_site_draws import (
    JointSiteDrawResult,
    joint_site_cover_draws,
)

DrawInputs = tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
ClosureOracle = tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]


def inputs() -> DrawInputs:
    counts = np.array([[9, 1, 5], [2, 8, 3]])
    geometry = np.array([[1.0, 2.0, 4.0], [4.0, 1.0, 2.0]])
    sites = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    draws = np.broadcast_to(counts, (4, 2, 3)).copy()
    draws[0, 0] = [8, 2, 5]
    draws[1, 1] = [3, 7, 3]
    ppe = np.array([[1.0, 3.0, 2.0], [2.0, 3.0, 1.0], [1.0, 2.0, 3.0], [3.0, 1.0, 2.0]])
    return counts, geometry, sites, draws, ppe


def scalar_oracle(
    geometry: np.ndarray, sites: np.ndarray, draws: np.ndarray, ppe: np.ndarray
) -> ClosureOracle:
    """Evaluate separate site corrections/shared PPE and covariance with rationals."""
    rows = []
    for iteration, identities in enumerate(sites.tolist()):
        weights = [
            sum(
                (
                    Fraction(int(draws[iteration, site, taxon]))
                    / Fraction.from_float(float(geometry[site, taxon]))
                    for site in identities
                ),
                Fraction(),
            )
            / Fraction.from_float(float(ppe[iteration, taxon]))
            for taxon in range(ppe.shape[1])
        ]
        total = sum(weights, Fraction())
        rows.append([value / total for value in weights])
    means = [sum(column, Fraction()) / len(rows) for column in zip(*rows, strict=True)]
    covariance = [
        [
            sum(((row[i] - means[i]) * (row[j] - means[j]) for row in rows), Fraction())
            / (len(rows) - 1)
            for j in range(len(means))
        ]
        for i in range(len(means))
    ]
    return (
        np.array(rows, dtype=float),
        np.array(means, dtype=float),
        np.array(covariance, dtype=float),
        np.array([sqrt(float(covariance[i][i])) for i in range(len(means))]),
    )


def verify_case(
    counts: np.ndarray,
    geometry: np.ndarray,
    sites: np.ndarray,
    draws: np.ndarray,
    ppe: np.ndarray,
) -> JointSiteDrawResult:
    expected = scalar_oracle(geometry, sites, draws, ppe)
    result = joint_site_cover_draws(
        counts,
        geometry,
        sites,
        draws,
        ppe,
        taxon_measured=np.ones_like(counts, dtype=bool),
    )
    for actual, oracle in zip(
        (
            result.cover_draws,
            result.mean_cover,
            result.covariance,
            result.standard_error,
        ),
        expected,
        strict=True,
    ):
        assert np.isfinite(actual).all()
        np.testing.assert_allclose(actual, oracle, rtol=1e-11, atol=1e-14)
        assert not actual.flags.writeable
    np.testing.assert_allclose(result.cover_draws.sum(axis=1), 1.0, rtol=0, atol=5e-15)
    np.testing.assert_allclose(result.covariance.sum(axis=0), 0.0, rtol=0, atol=5e-15)
    return result


def test_finite_taxon_weights_with_overflowed_closure_total_stay_on_simplex() -> None:
    counts = np.ones((2, 3), dtype=int)
    geometry = np.array([[2.5e-308] * 3, [2e-308] * 3])
    sites = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    draws = np.broadcast_to(counts, (4, 2, 3)).copy()
    ppe = np.array([[1.0] * 3, [1.0] * 3, [1.0] * 3, [2.0] * 3])
    verify_case(counts, geometry, sites, draws, ppe)


@pytest.mark.parametrize(
    "geometry_scale,ppe_scale",
    [
        (1.0, 1.0),
        (1e-308, 1.0),
        (1.0, 1e-308),
        (1e-308, 1e-308),
        (1e307, 1e307),
        (1e-308, 1e307),
        (1e307, 1e-308),
    ],
)
def test_explicit_joint_uncertainty_matches_rational_oracle_across_unit_scales(
    geometry_scale: float, ppe_scale: float
) -> None:
    counts, geometry, sites, draws, ppe = inputs()
    verify_case(counts, geometry * geometry_scale, sites, draws, ppe * ppe_scale)


@pytest.mark.parametrize("extreme", [False, True])
def test_joint_count_and_ppe_draws_respect_site_and_taxon_permutations(
    extreme: bool,
) -> None:
    counts, geometry, sites, draws, ppe = inputs()
    if extreme:
        geometry *= 1e-308
    first = verify_case(counts, geometry, sites, draws, ppe)
    second = verify_case(counts[::-1], geometry[::-1], 1 - sites, draws[:, ::-1], ppe)
    np.testing.assert_allclose(
        second.cover_draws, first.cover_draws, rtol=1e-12, atol=1e-14
    )
    taxa = [2, 0, 1]
    permuted = verify_case(
        counts[:, taxa], geometry[:, taxa], sites, draws[:, :, taxa], ppe[:, taxa]
    )
    np.testing.assert_allclose(
        permuted.cover_draws, first.cover_draws[:, taxa], rtol=1e-12, atol=1e-14
    )
    np.testing.assert_allclose(
        permuted.covariance,
        first.covariance[np.ix_(taxa, taxa)],
        rtol=1e-12,
        atol=1e-14,
    )


def test_observed_zero_taxon_is_exact_zero_through_joint_extreme_uncertainty() -> None:
    counts, geometry, sites, draws, ppe = inputs()
    counts[:, 2] = 0
    draws[:, :, 2] = 0
    result = verify_case(counts, geometry * 1e-308, sites, draws, ppe)
    np.testing.assert_array_equal(result.cover_draws[:, 2], 0.0)
    np.testing.assert_array_equal(result.covariance[2], 0.0)
    assert result.standard_error[2] == 0


def test_ordinary_float32_draws_keep_supported_precision() -> None:
    counts, geometry, sites, draws, ppe = inputs()
    result = joint_site_cover_draws(
        counts.astype(np.float32),
        geometry.astype(np.float32),
        sites,
        draws.astype(np.float32),
        ppe.astype(np.float32),
        taxon_measured=np.ones_like(counts, dtype=bool),
    )
    expected = scalar_oracle(geometry, sites, draws, ppe)
    np.testing.assert_allclose(result.cover_draws, expected[0], rtol=5e-7, atol=1e-8)
    assert np.isfinite(result.covariance).all()


def test_ordinary_longdouble_input_retains_supported_precision() -> None:
    counts, geometry, sites, draws, ppe = inputs()
    extended_geometry = geometry.astype(np.longdouble)
    extended_ppe = ppe.astype(np.longdouble)
    result = joint_site_cover_draws(
        counts,
        extended_geometry,
        sites,
        draws,
        extended_ppe,
        taxon_measured=np.ones_like(counts, dtype=bool),
    )
    weights = (
        draws[np.arange(len(sites))[:, None], sites] / extended_geometry[sites]
    ).sum(axis=1) / extended_ppe
    direct = weights / weights.sum(axis=1, keepdims=True)
    np.testing.assert_array_equal(result.cover_draws, direct)
    assert result.cover_draws.dtype == direct.dtype
    np.testing.assert_array_equal(
        result.covariance, np.cov(direct, rowvar=False, ddof=1)
    )


@pytest.mark.skipif(
    np.finfo(np.longdouble).maxexp <= np.finfo(np.float64).maxexp,
    reason="Host longdouble has no extended exponent range; Linux extended dtype not qualified here",
)
def test_extended_longdouble_fallback_preserves_finite_geometry() -> None:
    counts = np.ones((2, 3), dtype=int)
    geometry = np.full((2, 3), np.finfo(np.longdouble).tiny, dtype=np.longdouble)
    sites = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    draws = np.broadcast_to(counts, (4, 2, 3)).copy()
    ppe = np.ones((4, 3), dtype=np.longdouble)
    ppe[-1] = 2
    with np.errstate(over="ignore"):
        weights = (draws[np.arange(len(sites))[:, None], sites] / geometry[sites]).sum(
            axis=1
        ) / ppe
        assert np.isfinite(weights).all()
        assert not np.isfinite(weights.sum(axis=1)[:3]).any()
    result = joint_site_cover_draws(
        counts,
        geometry,
        sites,
        draws,
        ppe,
        taxon_measured=np.ones_like(counts, dtype=bool),
    )
    assert result.cover_draws.dtype == np.dtype(np.longdouble)
    assert np.isfinite(result.cover_draws).all()
    np.testing.assert_allclose(
        result.cover_draws, np.longdouble(1) / 3, rtol=1e-15, atol=0
    )
    np.testing.assert_allclose(result.covariance, 0, rtol=0, atol=1e-30)
