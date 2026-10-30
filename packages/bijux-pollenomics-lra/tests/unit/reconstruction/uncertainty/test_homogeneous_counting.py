"""Exact scalar inverse laws and finite binomial coverage for fixed background."""

from decimal import Decimal, localcontext
from fractions import Fraction
from math import comb
from typing import Any

import numpy as np
import pytest

import bijux_pollenomics_lra as lra
from bijux_pollenomics_lra import api
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.uncertainty.homogeneous_counting import (
    PROFILE,
    homogeneous_two_taxon_counting_set,
)
from bijux_pollenomics_lra.reconstruction.uncertainty.two_taxon_counting import (
    fixed_two_taxon_counting_interval,
)


def test_public_contract_and_nonzero_background_scalar_mle() -> None:
    assert lra.homogeneous_two_taxon_counting_set is homogeneous_two_taxon_counting_set
    assert (
        "lra.love.two-taxon.fixed-background-binomial-set"
        in api.extension_descriptor()["capabilities"]
    )
    out = homogeneous_two_taxon_counting_set(
        [4, 6], np.array([1, 2]), [0.5, 0.25], taxon_measured=[True, True]
    )
    # p(v)=(v+1/2)/(11/4-v); p=2/5 gives v=3/7.
    assert out.point_cover == pytest.approx((3 / 7, 4 / 7), abs=1e-15)
    assert (
        out.status == "nonempty"
        and out.cover_lower is not None
        and out.cover_upper is not None
    )
    assert out.cover_lower[0] <= out.point_cover[0] <= out.cover_upper[0]
    assert out.profile == PROFILE


@pytest.mark.parametrize("first", [0, 1, 4, 9, 10])
def test_zero_background_recovers_existing_counting_set_exactly(first: int) -> None:
    old = fixed_two_taxon_counting_interval(
        [first, 10 - first], [2, 4], [1, 1], taxon_measured=[True, True]
    )
    current = homogeneous_two_taxon_counting_set(
        [first, 10 - first], [2, 4], [0, 0], taxon_measured=[True, True]
    )
    assert current.status == "nonempty"
    assert current.point_cover == old.cover
    assert current.cover_lower == old.cover_lower
    assert current.cover_upper == old.cover_upper
    assert current.pollen_tail_upper_bounds == old.pollen_tail_upper_bounds


def test_confidence_set_can_be_empty_without_manufacturing_a_boundary_interval() -> (
    None
):
    out = homogeneous_two_taxon_counting_set(
        [0, 10], [1, 1], [100, 0], taxon_measured=[True, True]
    )
    assert out.status == "empty"
    assert out.cover_lower is out.cover_upper is None
    assert out.point_cover == (0.0, 1.0)
    assert Fraction(out.feasible_pollen_probability_bounds[0]) == Fraction(100, 101)
    assert out.pollen_probability_interval[1] < 0.5
    assert out.pollen_tail_upper_bounds[1] is not None


def test_existing_converged_boundary_fit_can_have_an_empty_conditional_set() -> None:
    # Exact input tuple already maintained in the homogeneous point-fit test.
    # A converged boundary MLE does not itself establish model compatibility.
    out = homogeneous_two_taxon_counting_set(
        [1, 99], [1, 2], [0.4, 0.1], taxon_measured=[True, True]
    )
    assert out.point_cover == (0.0, 1.0)
    assert out.status == "empty"
    assert out.cover_lower is out.cover_upper is None
    assert out.pollen_probability_interval[1] < 0.1
    assert Fraction(out.feasible_pollen_probability_bounds[0]) > Fraction(1, 10)


@pytest.mark.parametrize(
    "counts,background,expected",
    [([0, 1], [3, 0], (0.0, 1.0)), ([1, 0], [0, 3], (1.0, 0.0))],
)
def test_closed_intersection_retains_isolated_model_endpoint(
    counts: list[int], background: list[int], expected: tuple[float, float]
) -> None:
    # N=1 and confidence1/2 give exact binomial endpoints3/4 or1/4.
    # Matching a feasible endpoint leaves a singleton, not an empty set.
    out = homogeneous_two_taxon_counting_set(
        counts, [1, 1], background, taxon_measured=[True, True], confidence_level=0.5
    )
    assert out.status == "nonempty"
    assert out.cover_lower == out.cover_upper == expected


def test_independent_decimal_forward_encloses_the_clipped_pollen_interval() -> None:
    out = homogeneous_two_taxon_counting_set(
        [4, 6], [1, 2], [0.5, 0.25], taxon_measured=[True, True]
    )
    assert out.cover_lower is not None and out.cover_upper is not None
    with localcontext() as context:
        context.prec = 80
        lower, upper = map(Decimal.from_float, (out.cover_lower[0], out.cover_upper[0]))
        # Direct forward equation independent of the implementation's inverse.
        forward_low = (lower + Decimal("0.5")) / (Decimal("2.75") - lower)
        forward_high = (upper + Decimal("0.5")) / (Decimal("2.75") - upper)
        cp_low, cp_high = map(Decimal.from_float, out.pollen_probability_interval)
        permitted_low = max(Decimal(2) / 11, cp_low)
        permitted_high = min(Decimal(6) / 7, cp_high)
        assert forward_low <= permitted_low + Decimal("1e-70")
        assert forward_high >= permitted_high - Decimal("1e-70")


def test_taxon_swap_and_exact_common_unit_scaling_preserve_the_set() -> None:
    out = homogeneous_two_taxon_counting_set(
        [4, 6], [1, 2], [0.5, 0.25], taxon_measured=[True, True]
    )
    reverse = homogeneous_two_taxon_counting_set(
        [6, 4], [2, 1], [0.25, 0.5], taxon_measured=[True, True]
    )
    assert reverse.cover_lower is not None and reverse.cover_upper is not None
    assert out.point_cover == pytest.approx(reverse.point_cover[::-1], abs=1e-15)
    assert out.cover_lower == pytest.approx(reverse.cover_lower[::-1], abs=2e-15)
    assert out.cover_upper == pytest.approx(reverse.cover_upper[::-1], abs=2e-15)
    scale = 2.0**500
    scaled = homogeneous_two_taxon_counting_set(
        [4, 6],
        [scale, 2 * scale],
        [0.5 * scale, 0.25 * scale],
        taxon_measured=[True, True],
    )
    assert out.point_cover == scaled.point_cover
    assert out.cover_lower == scaled.cover_lower
    assert out.cover_upper == scaled.cover_upper


def test_exhaustive_small_binomial_coverage_by_exact_combinatorial_probability() -> (
    None
):
    # Fixed a=(1,2), b=(1/2,1/4) has p(v)=(v+1/2)/(11/4-v).
    # This oracle enumerates the complete possible count population, without
    # estimating a coverage percentage from random draws or using SciPy tails.
    confidence = 0.8
    for total in range(1, 7):
        sets = [
            homogeneous_two_taxon_counting_set(
                [k, total - k],
                [1, 2],
                [0.5, 0.25],
                taxon_measured=[True, True],
                confidence_level=confidence,
            )
            for k in range(total + 1)
        ]
        for cover in (
            Fraction(0),
            Fraction(1, 7),
            Fraction(1, 2),
            Fraction(6, 7),
            Fraction(1),
        ):
            probability = (cover + Fraction(1, 2)) / (Fraction(11, 4) - cover)
            coverage = Fraction(0)
            for k, interval in enumerate(sets):
                if interval.status == "empty":
                    continue
                assert (
                    interval.cover_lower is not None
                    and interval.cover_upper is not None
                )
                if (
                    Fraction.from_float(interval.cover_lower[0])
                    <= cover
                    <= Fraction.from_float(interval.cover_upper[0])
                ):
                    coverage += (
                        comb(total, k)
                        * probability**k
                        * (1 - probability) ** (total - k)
                    )
            assert coverage >= Fraction.from_float(confidence)


@pytest.mark.parametrize(
    "a,b",
    [
        ([0, 1], [0, 0]),
        ([1, 2], [-1, 0]),
        ([True, 2], [0, 0]),
        ([1, 2], [False, 0]),
        ([1, 2], [float("inf"), 0]),
        ([1, 2, 3], [0, 0]),
        (["1", "2"], [0, 0]),
        ([[1], [2, 3]], [0, 0]),
        ([1, 2], [[0], [0, 1]]),
    ],
)
def test_invalid_fixed_model_is_refused(a: Any, b: Any) -> None:
    with pytest.raises(ValidationError):
        homogeneous_two_taxon_counting_set([4, 6], a, b, taxon_measured=[True, True])


def test_original_counting_support_and_work_refusals_are_not_bypassed() -> None:
    for counts, measured in (
        ([0, 0], [True, True]),
        ([4, 6], [False, True]),
        ([10001, 0], [True, True]),
        ([True, 6], [True, True]),
    ):
        with pytest.raises(ValidationError):
            homogeneous_two_taxon_counting_set(
                counts, [1, 2], [0.5, 0.25], taxon_measured=measured
            )


def test_fixed_background_is_not_an_uncertainty_draw_or_independent_error_bar() -> None:
    out = homogeneous_two_taxon_counting_set(
        [4, 6], [1, 2], [0.5, 0.25], taxon_measured=[True, True]
    )
    assert out.cover_lower is not None and out.cover_upper is not None
    pollen_low = max(
        Fraction(2, 11), Fraction.from_float(out.pollen_probability_interval[0])
    )
    pollen_high = min(
        Fraction(6, 7), Fraction.from_float(out.pollen_probability_interval[1])
    )
    exact_low = (11 * pollen_low - 2) / (4 * (1 + pollen_low))
    exact_high = (11 * pollen_high - 2) / (4 * (1 + pollen_high))
    assert Fraction.from_float(out.cover_lower[0]) <= exact_low
    assert Fraction.from_float(out.cover_upper[0]) >= exact_high
    assert Fraction.from_float(out.cover_lower[1]) <= 1 - exact_high
    assert Fraction.from_float(out.cover_upper[1]) >= 1 - exact_low
    assert (
        out.numerical_certification == "directed-decimal-binomial-and-rational-inverse"
    )
    assert not hasattr(out, "regional_background_uncertainty")
