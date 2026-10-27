"""Analytical coupled-partition and nonclosed-observation controls."""

from fractions import Fraction
import math

import pytest

from .metrics import METRICS, closure, deposition, metric_bounds


def test_equal_source_cover_cancels_partition_uncertainty_exactly() -> None:
    assert deposition(
        Fraction(1),
        (Fraction(1, 4), Fraction(3, 4)),
        Fraction(3, 5),
        Fraction(3, 5),
        Fraction(2),
    ) == (Fraction(6, 5), Fraction(6, 5))


def test_affine_deposition_tracks_the_sign_before_positive_closure() -> None:
    first = deposition(
        Fraction(4),
        (Fraction(1), Fraction(3)),
        Fraction(1, 5),
        Fraction(4, 5),
        Fraction(2),
    )
    second = deposition(
        Fraction(4),
        (Fraction(1), Fraction(3)),
        Fraction(3, 5),
        Fraction(1, 5),
        Fraction(1),
    )
    assert first == (Fraction(14, 5), Fraction(26, 5))
    assert second == (Fraction(6, 5), Fraction(2))
    bounds = closure(first, second)
    assert bounds == (
        (Fraction(7, 12), Fraction(13, 16)),
        (Fraction(3, 16), Fraction(5, 12)),
    )


def test_nonclosed_observations_do_not_have_a_forced_zero_minimum() -> None:
    observed = Fraction(2, 5), Fraction(7, 10)
    bounds = metric_bounds((Fraction(3, 10), Fraction(2, 5)), observed)
    assert (
        bounds[METRICS[0]] == bounds[METRICS[1]] == (Fraction(1, 20), Fraction(1, 20))
    )
    expected_h = abs(math.sqrt(1.1) - 1) / math.sqrt(2)
    assert bounds[METRICS[2]][0] > 0
    assert float(bounds[METRICS[2]][0]) == pytest.approx(expected_h, abs=2e-15)


@pytest.mark.parametrize(
    "limits,observed",
    [
        ((Fraction(0), Fraction(1)), (Fraction(1, 4), Fraction(3, 4))),
        ((Fraction(1, 10), Fraction(1, 5)), (Fraction(2, 5), Fraction(7, 10))),
        ((Fraction(4, 5), Fraction(9, 10)), (Fraction(2, 5), Fraction(7, 10))),
        ((Fraction(1, 4), Fraction(3, 4)), (Fraction(0), Fraction(1))),
    ],
)
def test_exact_score_enclosures_contain_separate_dense_point_arithmetic(
    limits: tuple[Fraction, Fraction], observed: tuple[Fraction, Fraction]
) -> None:
    bounds = metric_bounds(limits, observed)
    for index in range(2001):
        p = float(limits[0] + (limits[1] - limits[0]) * index / 2000)
        q0, q1 = map(float, observed)
        mae = (abs(p - q0) + abs(1 - p - q1)) / 2
        h = math.sqrt(
            (
                (math.sqrt(p) - math.sqrt(q0)) ** 2
                + (math.sqrt(1 - p) - math.sqrt(q1)) ** 2
            )
            / 2
        )
        for key, value in zip(METRICS, (mae, mae, h), strict=True):
            assert (
                float(bounds[key][0]) - 2e-14 <= value <= float(bounds[key][1]) + 2e-14
            )


def test_extreme_and_identical_closed_compositions_have_known_distances() -> None:
    distance = metric_bounds((Fraction(0), Fraction(0)), (Fraction(1), Fraction(0)))
    assert all(bounds == (Fraction(1), Fraction(1)) for bounds in distance.values())
    same = metric_bounds(
        (Fraction(1, 4), Fraction(3, 4)), (Fraction(1, 2), Fraction(1, 2))
    )
    assert same[METRICS[0]] == same[METRICS[1]] == (Fraction(0), Fraction(1, 4))
    assert same[METRICS[2]][0] == 0


@pytest.mark.parametrize(
    "first,second",
    [
        ((Fraction(0), Fraction(0)), (Fraction(0), Fraction(0))),
        ((Fraction(-1), Fraction(1)), (Fraction(1), Fraction(2))),
        ((Fraction(2), Fraction(1)), (Fraction(1), Fraction(2))),
    ],
)
def test_nonpositive_or_reversed_closure_refuses(
    first: tuple[Fraction, Fraction], second: tuple[Fraction, Fraction]
) -> None:
    with pytest.raises(ValueError):
        closure(first, second)
