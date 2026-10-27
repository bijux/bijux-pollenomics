"""Analytical masked-ratio, chain-weighting and signed-contrast controls."""

from fractions import Fraction
import math

import pytest

from .independent_sampling import (
    conditional_mean,
    indicator_variance,
    mean_covariance,
    pooled_covariance,
    residual_batches,
    sample_crossproducts,
    scalar_axes,
    scalar_projection,
    variance_display,
)


def test_missing_state_keeps_random_denominator_and_native_batch_position() -> None:
    rows = ((1.0,), None, (3.0,), (5.0,))
    p, mean = conditional_mean(rows)
    assert p == 0.75 and mean == (3.0,)
    assert residual_batches(rows, mean, p, 2) == [(-4 / 3,), (4 / 3,)]
    assert mean_covariance(rows, mean, p, 2)[0][0] == pytest.approx(
        float(Fraction(16, 9))
    )
    assert indicator_variance(rows, 2) == (
        1 / 16,
        "observed_indicator_variation_no_mixing_guarantee",
    )
    with pytest.raises(ValueError, match="partition"):
        residual_batches(tuple(row for row in rows if row is not None), mean, p, 2)


def test_pooled_complete_weights_are_not_equal_chain_mean_weights() -> None:
    chains = [((1.0,),) * 4, ((3.0,), (3.0,), None, None)]
    p, mean, covariance = pooled_covariance(chains, 2)
    assert p == 0.75 and mean == (5 / 3,)
    assert mean != (2.0,)
    # Chain 2 common-target residual batches are (16/9, 0).
    assert covariance[0][0] == pytest.approx(float(Fraction(16, 81)))


def test_pool_centers_batches_within_chains_not_across_chain_offsets() -> None:
    chains = [((1.0,),) * 4, ((3.0,),) * 4]
    _, mean, covariance = pooled_covariance(chains, 2)
    assert mean == (2.0,) and covariance == ((0.0,),)
    assert (
        variance_display(0)[0]
        == "empirically_zero_batch_variation_not_zero_target_error"
    )


def test_correlated_component_contrast_cancels_before_square_root() -> None:
    rows = tuple(tuple(float(v + j % 5) for j in range(20)) for v in (1, 3, 5, 7))
    p, mean = conditional_mean(rows)
    cov = mean_covariance(rows, mean, p, 2)
    scalars = scalar_projection(mean, cov)
    assert len(scalar_axes()) == len(scalars) == 50
    assert all(variance > 0 for _, variance in scalars[:20])
    assert all(mu == 0 and variance == 0 for mu, variance in scalars[20:])


def test_constant_indicator_warns_instead_of_certifying_mixing() -> None:
    assert indicator_variance(((1.0,),) * 4, 2) == (
        0.0,
        "empirically_constant_indicator_insufficient_transitions",
    )


@pytest.mark.parametrize(
    "rows", [(), (None,) * 4, ((math.nan,),) * 4, ((1.0,), (2.0, 3.0))]
)
def test_invalid_conditional_population_refuses(
    rows: tuple[tuple[float, ...] | None, ...],
) -> None:
    with pytest.raises(ValueError):
        conditional_mean(rows)


@pytest.mark.parametrize("size", [0, True, 3, 4])
def test_partition_never_drops_a_tail_or_uses_one_batch(size: int) -> None:
    with pytest.raises(ValueError):
        residual_batches(((1.0,),) * 4, (1.0,), 1.0, size)


@pytest.mark.parametrize("value", [-1e-30, math.nan, math.inf])
def test_negative_or_nonfinite_variance_is_not_clipped(value: float) -> None:
    assert variance_display(value) == ("refused_signed_or_nonfinite_variance", None)


def test_positive_variation_underflow_refuses_instead_of_certifying_zero() -> None:
    with pytest.raises(ValueError, match="underflow"):
        sample_crossproducts(((0.0,), (1e-200,)), 1.0)


def test_ratio_residuals_agree_exact_joint_vector_fraction_control() -> None:
    chains = [
        ((1.0, 2.0), (2.0, 3.0), (3.0, 5.0), (4.0, 8.0)),
        ((2.0, 9.0), None, (6.0, 7.0), (8.0, 6.0)),
    ]
    # An exact independent joint-vector calculation includes the random denominator.
    joint: list[list[tuple[Fraction, ...]]] = [
        [
            (Fraction(0),) * 3 if row is None else (Fraction(1), *map(Fraction, row))
            for row in chain
        ]
        for chain in chains
    ]
    center = tuple(
        sum((row[i] for chain in joint for row in chain), Fraction(0)) * Fraction(1, 8)
        for i in range(3)
    )
    mu = tuple(center[i + 1] / center[0] for i in range(2))
    jacobian = [
        (-mu[i] / center[0], *[Fraction(int(i == j)) / center[0] for j in range(2)])
        for i in range(2)
    ]
    expected = [[Fraction(0) for _ in range(2)] for _ in range(2)]
    for chain in joint:
        fraction_mean = tuple(
            sum((row[i] for row in chain), Fraction(0)) * Fraction(1, 4)
            for i in range(3)
        )
        batches = [
            tuple(
                sum((row[i] for row in chain[start : start + 2]), Fraction(0))
                * Fraction(1, 2)
                for i in range(3)
            )
            for start in (0, 2)
        ]
        batch_cov = [
            [
                2
                * sum(
                    (batch[i] - fraction_mean[i]) * (batch[j] - fraction_mean[j])
                    for batch in batches
                )
                for j in range(3)
            ]
            for i in range(3)
        ]
        for i in range(2):
            for j in range(2):
                term = sum(
                    jacobian[i][k] * batch_cov[k][column] * jacobian[j][column]
                    for k in range(3)
                    for column in range(3)
                ) * Fraction(1, 16)
                assert isinstance(term, Fraction)
                expected[i][j] += term
    p, mean, observed = pooled_covariance(chains, 2)
    assert p == float(center[0])
    assert mean == tuple(map(float, mu))
    for i in range(2):
        for j in range(2):
            assert observed[i][j] == pytest.approx(float(expected[i][j]), abs=1e-15)
