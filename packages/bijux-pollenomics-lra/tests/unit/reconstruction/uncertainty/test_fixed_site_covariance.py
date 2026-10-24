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
        counts,
        np.ones_like(counts),
        np.ones(2),
        np.zeros((2, 2)),
        taxon_measured=np.ones_like(counts, dtype=bool),
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
    result = fixed_site_cover_covariance(
        counts,
        deposition,
        ppe,
        covariance,
        taxon_measured=np.ones_like(counts, dtype=bool),
    )
    diagonal_only = fixed_site_cover_covariance(
        counts,
        deposition,
        ppe,
        np.diag(np.diag(covariance)),
        taxon_measured=np.ones_like(counts, dtype=bool),
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
        taxon_measured=np.ones_like(counts, dtype=bool)[:, permutation],
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
            taxon_measured=np.ones_like(counts, dtype=bool),
        )
    with pytest.raises(ValidationError, match="numeric"):
        fixed_site_cover_covariance(
            counts.astype(str),
            np.ones_like(counts),
            np.ones(2),
            np.eye(2),
            taxon_measured=np.ones_like(counts, dtype=bool),
        )
    with pytest.raises(ValidationError, match="numeric"):
        fixed_site_cover_covariance(
            counts * 2**53,
            np.ones_like(counts),
            np.ones(2),
            np.eye(2),
            taxon_measured=np.ones_like(counts, dtype=bool),
        )


def test_unmeasured_taxon_is_not_a_zero_count() -> None:
    counts = np.array([[30, 70], [80, 20]])
    measured = np.ones_like(counts, dtype=bool)
    measured[1, 0] = False
    with pytest.raises(ValidationError) as error:
        fixed_site_cover_covariance(
            counts, np.ones_like(counts), np.ones(2), np.eye(2), taxon_measured=measured
        )
    assert error.value.reason_code == "taxon_measurement_unresolved"


@pytest.mark.parametrize("ppe_unit", [1.0, 1e-6])
@pytest.mark.parametrize(
    "declared_covariance",
    [
        [[-0.1, 0.0], [0.0, 0.0]],
        [[0.1, 0.2], [0.2, 0.1]],
        [[0.1, 0.01], [0.02, 0.1]],
        [[0.0, 0.02], [0.02, 0.1]],
        [[0.0, 0.0], [1e-14, 0.1]],
    ],
    ids=[
        "negative-variance",
        "indefinite",
        "asymmetric",
        "zero-variance-coupling",
        "zero-variance-column-coupling",
    ],
)
def test_invalid_parameter_covariance_refused_in_every_common_ppe_unit(
    ppe_unit: float, declared_covariance: list[list[float]]
) -> None:
    # An uncertainty matrix cannot become valid merely by changing PPE units.
    with pytest.raises(ValidationError, match="PPE covariance"):
        fixed_site_cover_covariance(
            np.array([[1, 1]]),
            np.ones((1, 2)),
            np.full(2, ppe_unit),
            np.array(declared_covariance) * ppe_unit**2,
            taxon_measured=np.ones((1, 2), dtype=bool),
        )


@pytest.mark.parametrize("ppe_unit", [1e-6, 1.0, 1e6])
@pytest.mark.parametrize("common_parameter_error", [False, True])
def test_valid_ppe_covariance_matches_independent_two_taxon_variance(
    ppe_unit: float, common_parameter_error: bool
) -> None:
    # A binomial with N=2 and p=1/2 gives Var(cover)=p(1-p)/N=1/8.
    # At equal PPE, differentiating the scalar odds formula gives an added
    # variance (C11+C22-2*C12)/(16*PPE**2), here 1/80. A perfectly shared
    # multiplicative PPE error leaves those odds unchanged, giving zero.
    counting_variance = 1 / 8
    ppe_variance = 0.0 if common_parameter_error else 1 / 80
    covariance = (
        np.full((2, 2), 0.25)
        if common_parameter_error
        else np.array([[0.2, 0.1], [0.1, 0.2]])
    )
    result = fixed_site_cover_covariance(
        np.array([[1, 1]]),
        np.ones((1, 2)),
        np.full(2, ppe_unit),
        covariance * ppe_unit**2,
        taxon_measured=np.ones((1, 2), dtype=bool),
    )
    closed_axis = np.array([[1.0, -1.0], [-1.0, 1.0]])
    np.testing.assert_array_equal(result.cover, [0.5, 0.5])
    np.testing.assert_allclose(
        result.counting_covariance, closed_axis * counting_variance, rtol=2e-15
    )
    np.testing.assert_allclose(
        result.ppe_covariance,
        closed_axis * ppe_variance,
        rtol=2e-15,
        atol=np.finfo(float).eps ** 2 if common_parameter_error else 0,
    )
    np.testing.assert_allclose(
        result.total_covariance,
        closed_axis * (counting_variance + ppe_variance),
        rtol=2e-15,
    )
    np.testing.assert_allclose(
        result.standard_error, np.sqrt(counting_variance + ppe_variance), rtol=2e-15
    )


@pytest.mark.parametrize("count_dtype", [np.int64, np.uint64, np.float64])
@pytest.mark.parametrize(
    "count_pair", [[2**53 - 1, 1], [2**53 - 1, 2], [2**53 - 1, 2**53 - 1]]
)
def test_inexact_site_count_total_is_refused(
    count_dtype: type[np.generic], count_pair: list[int]
) -> None:
    # Each cell is representable, but the multinomial denominator must also
    # stay within the consecutive binary64 integer range.
    counts = np.array([count_pair], dtype=count_dtype)
    with pytest.raises(ValidationError, match="counts"):
        fixed_site_cover_covariance(
            counts,
            np.ones((1, 2)),
            np.ones(2),
            np.zeros((2, 2)),
            taxon_measured=np.ones((1, 2), dtype=bool),
        )


def test_largest_exact_site_total_retains_binomial_covariance() -> None:
    total = 2**53 - 1
    counts = np.array([[2**52, 2**52 - 1]], dtype=np.int64)
    result = fixed_site_cover_covariance(
        counts,
        np.ones((1, 2)),
        np.ones(2),
        np.zeros((2, 2)),
        taxon_measured=np.ones((1, 2), dtype=bool),
    )
    probability = 2**52 / total
    variance = probability * (1 - probability) / total
    np.testing.assert_allclose(result.cover, [probability, 1 - probability], rtol=2e-15)
    np.testing.assert_allclose(
        result.counting_covariance,
        np.array([[variance, -variance], [-variance, variance]]),
        rtol=2e-15,
    )


@pytest.mark.parametrize(
    "field", ["counts", "deposition", "ppe", "ppe_covariance", "taxon_measured"]
)
@pytest.mark.parametrize("unresolved", [True, False])
def test_masks_cannot_become_observed_backing_values(
    field: str, unresolved: bool
) -> None:
    values = {
        "counts": np.array([[30, 20, 50], [20, 65, 15]]),
        "deposition": np.array([[0.4, 0.8, 0.5], [0.8, 0.3, 0.7]]),
        "ppe": np.array([1.0, 1.5, 0.75]),
        "ppe_covariance": np.array(
            [[0.04, 0.015, -0.005], [0.015, 0.09, 0.01], [-0.005, 0.01, 0.0225]]
        ),
        "taxon_measured": np.ones((2, 3), dtype=bool),
    }
    expected = fixed_site_cover_covariance(**values)
    original = values[field]
    mask = np.zeros(original.shape, dtype=bool)
    mask.flat[0] = unresolved
    values[field] = np.ma.array(original, mask=mask)
    if unresolved:
        with pytest.raises(ValidationError, match=field + " contains masked"):
            fixed_site_cover_covariance(**values)
    else:
        actual = fixed_site_cover_covariance(**values)
        assert actual.profile == expected.profile
        for name in (
            "cover",
            "counting_covariance",
            "ppe_covariance",
            "total_covariance",
            "standard_error",
        ):
            observed = getattr(actual, name)
            baseline = getattr(expected, name)
            np.testing.assert_array_equal(observed, baseline)
            assert observed.dtype == baseline.dtype
            assert observed.tobytes() == baseline.tobytes()
            assert not observed.flags.writeable
