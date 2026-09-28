"""Independent fixed-site counting and parameter covariance checks."""

from __future__ import annotations

import numpy as np
import pytest

import bijux_pollenomics_lra as lra
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.fixed_site_covariance import (
    PROFILE,
    fixed_site_cover_covariance,
)


def test_two_sites_reduce_to_conditional_binomial_variance() -> None:
    assert lra.fixed_site_cover_covariance is fixed_site_cover_covariance
    counts = np.array([[30, 70], [80, 20]])
    result = fixed_site_cover_covariance(
        counts, np.ones_like(counts), np.ones(2), np.zeros((2, 2))
    )
    expected = (100 * 0.3 * 0.7 + 100 * 0.8 * 0.2) / 200**2
    np.testing.assert_allclose(result.cover, [0.55, 0.45], atol=1e-15)
    np.testing.assert_allclose(np.diag(result.counting_covariance), expected)
    np.testing.assert_allclose(result.counting_covariance[0, 1], -expected)
    np.testing.assert_array_equal(result.ppe_covariance, np.zeros((2, 2)))
    assert result.profile == PROFILE


def test_heterogeneous_geometry_full_ppe_covariance_and_order_invariance() -> None:
    counts = np.array([[30, 20, 50], [20, 65, 15]])
    deposition = np.array([[0.4, 0.8, 0.5], [0.8, 0.3, 0.7]])
    ppe = np.array([1.0, 1.5, 0.75])
    covariance = np.array(
        [[0.04, 0.015, -0.005], [0.015, 0.09, 0.01], [-0.005, 0.01, 0.0225]]
    )
    result = fixed_site_cover_covariance(counts, deposition, ppe, covariance)
    diagonal_only = fixed_site_cover_covariance(
        counts, deposition, ppe, np.diag(np.diag(covariance))
    )
    assert not np.allclose(result.ppe_covariance, diagonal_only.ppe_covariance)
    assert not np.allclose(result.standard_error, diagonal_only.standard_error)
    np.testing.assert_allclose(result.cover.sum(), 1, atol=1e-15)
    np.testing.assert_allclose(result.total_covariance.sum(axis=0), 0, atol=1e-16)
    permutation = [2, 0, 1]
    reordered = fixed_site_cover_covariance(
        counts[:, permutation],
        deposition[:, permutation],
        ppe[permutation],
        covariance[np.ix_(permutation, permutation)],
    )
    np.testing.assert_allclose(reordered.cover, result.cover[permutation])
    np.testing.assert_allclose(
        reordered.total_covariance,
        result.total_covariance[np.ix_(permutation, permutation)],
    )
    assert not result.total_covariance.flags.writeable


def test_invalid_parameter_covariance_and_count_types_are_refused() -> None:
    counts = np.array([[30, 70], [80, 20]])
    with pytest.raises(ValidationError, match="covariance"):
        fixed_site_cover_covariance(
            counts,
            np.ones_like(counts),
            np.ones(2),
            np.array([[1, 2], [2, 1]]),
        )
    with pytest.raises(ValidationError, match="numeric"):
        fixed_site_cover_covariance(
            counts.astype(str), np.ones_like(counts), np.ones(2), np.eye(2)
        )
    with pytest.raises(ValidationError, match="numeric"):
        fixed_site_cover_covariance(
            counts * 2**53, np.ones_like(counts), np.ones(2), np.eye(2)
        )
