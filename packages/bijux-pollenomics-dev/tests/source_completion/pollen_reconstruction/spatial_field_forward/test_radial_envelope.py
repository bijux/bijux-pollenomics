"""Exact finite-target and nonclosed-observation envelope controls."""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward import (
    radial_envelope as exact,
)


@pytest.mark.parametrize(
    "value",
    [
        Fraction(0),
        Fraction(1),
        Fraction(1, 4),
        Fraction(2),
        Fraction(7, 13),
        Fraction(2**160 + 1, 3),
    ],
)
def test_root_certificate_is_outward_by_exact_squaring(value: Fraction) -> None:
    lower, upper = exact.root_bounds(value)
    assert 0 <= lower <= upper
    assert lower * lower <= value <= upper * upper
    assert upper - lower <= Fraction(1, 2**96)


def test_negative_root_and_coincident_anchors_refuse() -> None:
    with pytest.raises(ValueError, match="Negative"):
        exact.root_bounds(Fraction(-1, 10**40))
    with pytest.raises(ValueError, match="Distinct"):
        exact.angular_certificate(1, [2, 3], [2, 3])


def test_algebraic_circle_mean_matches_independent_high_precision_expression() -> None:
    record = exact.angular_certificate(1, [1, 0], [2, 0])
    lower, upper = exact.decoded(record["weight_bounds_exact"])
    assert Fraction(record["sqrt_radicand_exact"]) == 13
    with localcontext() as context:
        context.prec = 120
        # At this geometry A=7, |a+b|²=9 and Delta=3.
        expected = Decimal(1) / 2 + Decimal(1) / 6 * (
            1 + Decimal(2) / Decimal(13).sqrt()
        )
        assert (
            Decimal(lower.numerator) / lower.denominator
            <= expected
            <= Decimal(upper.numerator) / upper.denominator
        )
    assert upper - lower <= Fraction(2, 2**96)


def test_symmetric_and_point_limits_keep_exact_geometry_scope() -> None:
    symmetric = exact.angular_certificate(100, [-3, 4], [3, -4])
    assert symmetric["symmetry"] is True
    assert exact.decoded(symmetric["weight_bounds_exact"]) == (
        Fraction(1, 2),
        Fraction(1, 2),
    )
    point = exact.angular_certificate(0, [1, 0], [2, 0])
    lower, upper = exact.decoded(point["weight_bounds_exact"])
    assert lower <= Fraction(4, 5) <= upper
    values = [
        exact.decoded(
            exact.angular_certificate(r, [1, 0], [2, 0])["weight_bounds_exact"]
        )
        for r in (0, 1, 10, 100)
    ]
    assert all(
        left[0] >= right[1] for left, right in zip(values[:-1], values[1:], strict=True)
    )


def test_refined_mass_sum_is_not_replaced_by_a_rounded_old_total() -> None:
    certificates = [
        {"weight_bounds_exact": exact.encoded((Fraction(1, 4), Fraction(1, 4)))}
    ] * 3
    total, (first, second) = exact.coefficients([0.1, 0.2], certificates)
    assert total == Fraction(0.1) + Fraction(0.2)
    assert total != Fraction(0.3)
    assert first == (total / 4, total / 4)
    assert second == (total * 3 / 4, total * 3 / 4)
    assert first[0] + second[1] == total


def test_complementary_affine_bounds_preserve_sign_and_remove_unattainable_extrema() -> (
    None
):
    total = Fraction(1)
    interval = Fraction(1, 5), Fraction(4, 5)
    assert exact.deposition(total, interval, [0.25, 0.25], 2) == (
        Fraction(1, 2),
        Fraction(1, 2),
    )
    positive = exact.deposition(total, interval, [0.75, 0.25], 2)
    negative = exact.deposition(total, interval, [0.25, 0.75], 2)
    assert positive == negative == (Fraction(7, 10), Fraction(13, 10))
    # Independently taking both anchor lower endpoints would falsely give0.4.
    assert 2 * interval[0] * (Fraction(3, 4) + Fraction(1, 4)) < positive[0]


def test_normalization_preserves_complementary_probability_range() -> None:
    result = exact.normalized(((Fraction(1), Fraction(2)), (Fraction(3), Fraction(4))))
    assert result == (Fraction(1, 5), Fraction(2, 5))
    with pytest.raises(ValueError, match="Undefined"):
        exact.normalized(((Fraction(0), Fraction(0)), (Fraction(0), Fraction(0))))


def test_nonclosed_observation_retains_positive_hellinger_minimum() -> None:
    result = exact.metric_ranges((Fraction(0), Fraction(1)), [0.25, 0.25])
    assert exact.decoded(result[exact.METRICS[0]]) == (Fraction(1, 4), Fraction(1, 2))
    assert result[exact.METRICS[0]] == result[exact.METRICS[1]]
    minimum, maximum = exact.decoded(result[exact.METRICS[2]])
    root = exact.root_bounds(Fraction(1, 2))
    assert 0 < minimum <= root[0] - Fraction(1, 2)
    assert maximum == Fraction(1, 2)
    at_wrong_center = exact.hellinger_at(
        Fraction(1, 4), (Fraction(1, 4), Fraction(1, 4))
    )
    assert at_wrong_center[0] > root[1] - Fraction(1, 2)


def test_closed_point_identity_and_signed_interval_squares_are_constructive() -> None:
    point = exact.metric_ranges((Fraction(1, 4), Fraction(1, 4)), [0.25, 0.75])
    assert exact.decoded(point[exact.METRICS[0]]) == (Fraction(0), Fraction(0))
    assert exact.decoded(point[exact.METRICS[2]])[0] == 0
    assert exact.decoded(point[exact.METRICS[2]])[1] <= Fraction(2, 2**96)
    assert exact.squared((Fraction(-2), Fraction(3))) == (Fraction(0), Fraction(9))
    assert exact.squared((Fraction(-3), Fraction(-2))) == (Fraction(4), Fraction(9))


@pytest.mark.parametrize("masses", [[0.0], [-1.0], [float("nan")], [float("inf")]])
def test_invalid_ring_mass_refuses_without_clipping(masses: list[float]) -> None:
    certificate = {"weight_bounds_exact": ["1/2", "1/2"]}
    with pytest.raises(ValueError):
        exact.coefficients(masses, [certificate, certificate])
