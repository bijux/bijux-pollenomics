"""Analytical positive and refusal controls independent of native engine imports."""

from decimal import Decimal
from fractions import Fraction as Q
import math

import pytest

from .scalar import (
    admitted_cover,
    forward,
    metrics,
    number,
    percent_round,
    reveals,
    signed_love,
    spatial_cover,
    spatial_weights,
)


def test_scalar_reveals_retains_percent_rounding_without_reclosing() -> None:
    cover = reveals([1, 2], [1, 1], [1, 1])
    assert tuple(float(value) for value in cover) == pytest.approx(
        (0.33333, 0.66667), abs=1e-15
    )
    assert reveals([3, 1], [3, 1], [2, 2]) == (Q(1, 2), Q(1, 2))


@pytest.mark.parametrize(
    "value,expected",
    [
        (Q(5, 4), 1.25),
        (Q(2501, 2000), 1.25),
        (Q(2503, 2000), 1.252),
        (Q(-2503, 2000), -1.252),
    ],
)
def test_percentage_grid_and_tie_rounding(value: Q, expected: float) -> None:
    assert percent_round(value) == expected


def test_signed_love_algebra_preserves_impossible_cover() -> None:
    assert signed_love([3, 1], [1, 1], [0.5, 0.5], [1, 1], [2, 2]) == (
        Q(5, 4),
        Q(-1, 4),
    )
    signed = signed_love([3, 1], [1, 1], [0.5, 0.5], [1, 1], [2, 2])
    assert sum(signed) == 1
    with pytest.raises(ValueError, match="signed LOVE"):
        admitted_cover(signed)
    with pytest.raises(ValueError, match="signed LOVE"):
        spatial_cover([signed, (Q(1, 2), Q(1, 2))], [Q(1, 2), Q(1, 2)])


def test_nonnegative_love_is_not_replaced_with_regional_cover() -> None:
    cover = signed_love([3, 2], [1, 2], [0.5, 0.5], [2, 2], [1, 1])
    assert cover == (Q(7, 8), Q(1, 8))
    assert admitted_cover(cover) == cover


@pytest.mark.parametrize(
    "method,distances,expected",
    [
        ("training_mean", [2, 4], (Q(1, 2), Q(1, 2))),
        ("nearest_site", [2, 4], (Q(1), Q(0))),
        ("nearest_site", [4, 4], (Q(1, 2), Q(1, 2))),
        ("inverse_distance_squared", [2, 4], (Q(4, 5), Q(1, 5))),
        ("inverse_distance_squared", [0, 4], (Q(1), Q(0))),
        ("inverse_distance_squared", [0, 0], (Q(1, 2), Q(1, 2))),
    ],
)
def test_two_predictor_weights(
    method: str, distances: list[int], expected: tuple[Q, Q]
) -> None:
    assert spatial_weights(method, distances) == expected
    assert spatial_cover([(Q(1), Q(0)), (Q(0), Q(1))], expected) == expected


def test_forward_keeps_ppe_weighted_regional_deposition_separate_from_local_cover() -> (
    None
):
    predicted = forward(
        [Q(3, 4), Q(1, 4)], [1, 2], [[2, 4], [4, 2]], [0.5, 0.25], [2, 1]
    )
    assert predicted == (Q(32, 53), Q(21, 53))
    score = metrics(predicted, [2, 3])
    assert score == {
        "mean_absolute_fraction_error": Q(54, 265),
        "total_variation": Q(54, 265),
    }


@pytest.mark.parametrize(
    "value", [True, "1", None, math.inf, math.nan, Decimal("NaN"), 10**400]
)
def test_native_number_refuses_nonnumeric_nonfinite_and_unrepresentable(
    value: object,
) -> None:
    with pytest.raises(ValueError):
        number(value)


@pytest.mark.parametrize(
    "operation",
    [
        lambda: reveals([0, 0], [1, 1], [1, 1]),
        lambda: reveals([1, 2], [0, 1], [1, 1]),
        lambda: signed_love([1, 1], [1, 1], [0.5, 0.5], [0, 0], [1, 1]),
        lambda: spatial_weights("training_mean", [-1, 2]),
        lambda: spatial_weights("fallback", [1, 2]),
        lambda: forward([Q(1, 2), Q(1, 2)], [0, 0], [[1, 1]], [2], [1, 1]),
    ],
)
def test_numerical_domains_refuse_without_fallback(operation: object) -> None:
    assert callable(operation)
    with pytest.raises(ValueError):
        operation()
