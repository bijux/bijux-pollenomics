"""Exact masked-ratio and ordered-block controls for simulation precision."""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_monte_carlo import (
    batch_means,
)


def residual_covariance(
    arrays: list[np.ndarray],
    masks: list[np.ndarray],
    pooled: bool,
) -> list[list[Fraction]]:
    """Hand-size scalar residual calculation independent of the ratio Jacobian."""
    dimension = arrays[0].shape[1]
    population = sum(len(a) for a in arrays)
    complete = sum(int(mask.sum()) for mask in masks)
    if pooled:
        probability = Fraction(complete, population)
        center = [
            sum(
                (
                    Fraction.from_float(float(row[j]))
                    for array, mask in zip(arrays, masks, strict=True)
                    for row in array[mask]
                ),
                Fraction(0),
            )
            / complete
            for j in range(dimension)
        ]
    else:
        assert len(arrays) == 1
        probability = Fraction(complete, population)
        center = [
            sum(
                (Fraction.from_float(float(row[j])) for row in arrays[0][masks[0]]),
                Fraction(0),
            )
            / complete
            for j in range(dimension)
        ]
    covariance = [[Fraction(0) for _ in range(dimension)] for _ in range(dimension)]
    for array, mask in zip(arrays, masks, strict=True):
        rows = len(array)
        residual = [
            [
                (Fraction.from_float(float(row[j])) - center[j]) / probability
                if observed
                else Fraction(0)
                for j in range(dimension)
            ]
            for row, observed in zip(array, mask, strict=True)
        ]
        batches = [
            [
                sum((row[j] for row in residual[start : start + 2]), Fraction(0)) / 2
                for j in range(dimension)
            ]
            for start in range(0, rows, 2)
        ]
        mean = [
            sum((row[j] for row in batches), Fraction(0)) / len(batches)
            for j in range(dimension)
        ]
        scale = Fraction(2, len(batches) - 1) * Fraction(rows, population**2)
        for i in range(dimension):
            for j in range(dimension):
                covariance[i][j] += scale * sum(
                    ((row[i] - mean[i]) * (row[j] - mean[j]) for row in batches),
                    Fraction(0),
                )
    return covariance


def test_masked_ratio_and_pooled_crosscovariance_match_exact_residuals() -> None:
    first = np.array(
        [
            [1, 2],
            [3, -1],
            [np.nan, np.nan],
            [5, 4],
            [2, 0],
            [np.nan, np.nan],
            [-1, 2],
            [4, 3],
        ],
        dtype=float,
    )
    second = np.array(
        [[2, 3], [0, 2], [3, 5], [1, 2], [4, -2], [5, 1], [2, 4], [-1, 3]], dtype=float
    )
    arrays = [first, second]
    masks = [np.isfinite(array[:, 0]) for array in arrays]
    chains = [batch_means.prepare(a, m, 2) for a, m in zip(arrays, masks, strict=True)]
    mapping = np.array([[1, 0], [0, 1], [-1, 1]], dtype=float)
    actual = batch_means.estimate(chains, mapping)
    for index in range(2):
        expected = np.array(
            residual_covariance([arrays[index]], [masks[index]], False), dtype=float
        )
        np.testing.assert_allclose(
            actual["chain_covariances"][index], expected, atol=1e-15, rtol=1e-14
        )
    pooled = np.array(residual_covariance(arrays, masks, True), dtype=float)
    np.testing.assert_allclose(
        actual["pooled_covariance"], pooled, atol=1e-15, rtol=1e-14
    )
    expected_contrast_variance = pooled[0, 0] + pooled[1, 1] - 2 * pooled[0, 1]
    assert actual["pooled_variances"][2] == pytest.approx(
        expected_contrast_variance, abs=1e-15
    )
    expected_mean = np.concatenate(
        [a[m] for a, m in zip(arrays, masks, strict=True)]
    ).mean(axis=0)
    pooled_joint = actual["pooled_joint_mean"]
    np.testing.assert_allclose(pooled_joint[1:] / pooled_joint[0], expected_mean)
    assert not np.allclose(expected_mean, (chains[0].mean + chains[1].mean) / 2)
    compressed = batch_means.prepare(first[masks[0]], np.ones(6, dtype=bool), 2)
    compressed_covariance = batch_means.contribution(
        compressed, compressed.joint_mean, 1, mapping
    )[0]
    assert not np.allclose(compressed_covariance, actual["chain_covariances"][0])


def test_correlated_components_cancel_before_contrast_square_root() -> None:
    values = np.repeat(np.array([[0.0], [0.0], [1.0], [1.0]]), 2, axis=1)
    chain = batch_means.prepare(values, np.ones(4, dtype=bool), 2)
    mapping = np.array([[1, 0], [0, 1], [-1, 1]], dtype=float)
    covariance, variances, _ = batch_means.contribution(
        chain, chain.joint_mean, 1, mapping
    )
    assert covariance[0, 1] > 0
    assert variances[0] == variances[1] > 0
    assert variances[2] == 0
    assert variances[0] + variances[1] > 0


def test_fixed_block_membership_preserves_serial_dependence() -> None:
    block = np.array([[0.0]] * 4 + [[1.0]] * 4)
    alternating = np.array([[0.0], [1.0]] * 4)
    mask = np.ones(8, dtype=bool)
    mapping = np.ones((1, 1))
    a = batch_means.prepare(block, mask, 2)
    b = batch_means.prepare(alternating, mask, 2)
    va = batch_means.contribution(a, a.joint_mean, 1, mapping)[1]
    vb = batch_means.contribution(b, b.joint_mean, 1, mapping)[1]
    assert a.mean == b.mean
    assert va[0] > 0 and vb[0] == 0
    within = block.reshape(4, 2, 1)[:, ::-1].reshape(8, 1)
    c = batch_means.prepare(within, mask, 2)
    np.testing.assert_array_equal(a.batch_deviations, c.batch_deviations)


def test_difference_covariance_is_independent_chain_sum() -> None:
    values = np.arange(8, dtype=float).reshape(8, 1)
    chains = [
        batch_means.prepare(v, np.ones(8, dtype=bool), 2) for v in (values, values + 1)
    ]
    result = batch_means.estimate(chains, np.ones((1, 1)))
    assert result["difference_mean"][0] == 1
    np.testing.assert_array_equal(
        result["difference_covariance"], sum(result["chain_covariances"])
    )
    np.testing.assert_array_equal(
        result["difference_variances"], sum(result["chain_variances"])
    )


@pytest.mark.parametrize("batch_size", [0, -2, True, 3, 8])
def test_invalid_or_truncated_batch_partition_refuses(batch_size: int) -> None:
    with pytest.raises(ValueError, match="partition"):
        batch_means.prepare(np.ones((8, 1)), np.ones(8, dtype=bool), batch_size)


def test_undefined_covers_cannot_be_silently_completed_with_zero() -> None:
    with pytest.raises(ValueError, match="remain missing"):
        batch_means.prepare(np.zeros((4, 1)), np.array([True, False, True, True]), 2)


def test_empty_conditioning_and_nonfinite_support_refuse() -> None:
    with pytest.raises(ValueError, match="Empty conditioning"):
        batch_means.prepare(np.full((4, 1), np.nan), np.zeros(4, dtype=bool), 2)
    with pytest.raises(ValueError, match="Supported covers"):
        batch_means.prepare(np.full((4, 1), np.inf), np.ones(4, dtype=bool), 2)


def test_overflow_and_positive_variance_underflow_refuse() -> None:
    with pytest.raises(ValueError, match="batch arithmetic"):
        batch_means.prepare(np.full((4, 1), 1e308), np.ones(4, dtype=bool), 2)
    values = np.array([[0.0], [0.0], [1e-200], [1e-200]])
    chain = batch_means.prepare(values, np.ones(4, dtype=bool), 2)
    with pytest.raises(ValueError, match="underflow"):
        batch_means.contribution(chain, chain.joint_mean, 1, np.ones((1, 1)))


def test_all_scalar_axes_and_closure_maps_are_preserved() -> None:
    mapping = batch_means.scalar_map()
    assert mapping.shape == (50, 20)
    np.testing.assert_array_equal(mapping[:20], np.eye(20))
    np.testing.assert_array_equal(mapping[20:25, :5], -np.eye(5))
    np.testing.assert_array_equal(mapping[20:25, 5:10], np.eye(5))
    assert np.all(mapping[20:].sum(axis=1) == 0)
