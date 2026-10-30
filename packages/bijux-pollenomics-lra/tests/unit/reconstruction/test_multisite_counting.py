"""Independent exact inversion, small-count coverage and admission controls."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from itertools import product
from math import comb, inf, nextafter
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.uncertainty import multisite_counting as core
from bijux_pollenomics_lra.reconstruction.uncertainty.two_taxon_counting import (
    TwoTaxonCountingInterval,
)


def run(**changes: Any) -> core.MultisiteCountingSet:
    values: dict[str, Any] = {
        "counts": [[3, 7], [4, 6]],
        "responses": [[2.0, 1.0], [1.0, 3.0]],
        "taxon_measured": [[True, True], [True, True]],
    }
    values.update(changes)
    return core.multisite_two_taxon_counting_set(**values)


def inverse(p: Fraction, a: tuple[float, float]) -> Fraction:
    first, second = map(Fraction.from_float, a)
    # Independently solve p/(1-p) = a1*v/(a2*(1-v)).
    return p * second / ((1 - p) * first + p * second)


def forward(v: Fraction, a: tuple[float, float]) -> Fraction:
    first, second = map(Fraction.from_float, a)
    return first * v / (first * v + second * (1 - v))


def test_exact_inverse_intersection_tail_proofs_and_outward_display() -> None:
    result = run(counts=[[4, 6], [7, 3]])
    limits = []
    for site, a in zip(result.sites, result.responses, strict=True):
        bounds = tuple(
            inverse(Fraction.from_float(p), a) for p in site.pollen_probability_interval
        )
        assert tuple(map(Fraction, site.first_cover_interval_exact)) == bounds
        for v, p in zip(bounds, site.pollen_probability_interval, strict=True):
            assert forward(v, a) == Fraction.from_float(p)
        limits.append(bounds)
        interval = site.counting_interval
        assert interval is not None
        assert interval.confidence_level == result.marginal_confidence_level
        target = Decimal(interval.tail_target_lower_bound)
        assert (
            Fraction(target)
            <= (1 - Fraction.from_float(result.marginal_confidence_level)) / 2
        )
        assert all(
            bound is not None and Decimal(bound) <= target
            for bound in interval.pollen_tail_upper_bounds
        )
        assert all(0 < work <= 128 for work in interval.bound_search_evaluations)
    left, right = max(v[0] for v in limits), min(v[1] for v in limits)
    assert result.status == "nonempty"
    assert tuple(map(Fraction, result.intersection_limits_exact)) == (left, right)
    assert result.lower_attaining_site_indices == tuple(
        i for i, value in enumerate(limits) if value[0] == left
    )
    assert result.upper_attaining_site_indices == tuple(
        i for i, value in enumerate(limits) if value[1] == right
    )
    assert result.cover_lower_exact == (str(left), str(1 - right))
    assert result.cover_upper_exact == (str(right), str(1 - left))
    assert result.cover_lower is not None and result.cover_upper is not None
    for exact, shown in zip((left, 1 - right), result.cover_lower, strict=True):
        assert Fraction.from_float(shown) <= exact
    for exact, shown in zip((right, 1 - left), result.cover_upper, strict=True):
        assert Fraction.from_float(shown) >= exact


@pytest.mark.parametrize("level", [0.95, 0.8, 0.1, nextafter(0.0, 1.0)])
def test_confidence_budget_rounded_upward_exactly(level: float) -> None:
    result = run(confidence_level=level)
    target = (1 + Fraction.from_float(level)) / 2
    marginal = Fraction.from_float(result.marginal_confidence_level)
    assert marginal >= target
    assert (
        Fraction.from_float(nextafter(result.marginal_confidence_level, 0.0)) < target
    )
    assert Fraction(result.guaranteed_joint_confidence_lower_bound) == 2 * marginal - 1
    assert Fraction(
        result.guaranteed_joint_confidence_lower_bound
    ) >= Fraction.from_float(level)


def test_small_count_exact_coverage_under_independent_binomial_example() -> None:
    responses = ((2.0, 1.0), (1.0, 3.0))
    for n0, n1, v in product(
        range(1, 4), range(1, 4), map(Fraction, [0, 0.25, 0.5, 0.75, 1])
    ):
        probabilities = tuple(forward(v, a) for a in responses)
        covered = Fraction(0)
        marginal_failures = [Fraction(0), Fraction(0)]
        for k0, k1 in product(range(n0 + 1), range(n1 + 1)):
            result = run(counts=[[k0, n0 - k0], [k1, n1 - k1]], responses=responses)
            masses = [
                comb(n, k) * p**k * (1 - p) ** (n - k)
                for n, k, p in zip((n0, n1), (k0, k1), probabilities, strict=True)
            ]
            mass = masses[0] * masses[1]
            left, right = map(Fraction, result.intersection_limits_exact)
            if left <= v <= right:
                covered += mass
            for i, site in enumerate(result.sites):
                lower, upper = map(Fraction, site.first_cover_interval_exact)
                if not lower <= v <= upper:
                    marginal_failures[i] += mass
        assert covered >= Fraction(result.guaranteed_joint_confidence_lower_bound)
        for failure in marginal_failures:
            assert failure <= 1 - Fraction.from_float(result.marginal_confidence_level)


def test_empty_intersection_retains_inverted_limits_and_null_cover() -> None:
    result = run(counts=[[0, 100], [100, 0]], responses=[[1, 1], [1, 1]])
    assert result.status == "empty"
    assert Fraction(result.intersection_limits_exact[0]) > Fraction(
        result.intersection_limits_exact[1]
    )
    assert result.cover_lower_exact is result.cover_upper_exact is None
    assert result.cover_lower is result.cover_upper is None


def test_zero_effort_and_observed_zero_are_distinct() -> None:
    result = run(counts=[[0, 100], [0, 0]])
    assert result.status == "nonempty"
    assert result.excluded_zero_total_site_indices == (1,)
    assert result.sites[1].used is False
    assert result.sites[1].counting_interval is None
    assert result.sites[1].first_cover_interval_exact == ("0", "1")
    left, right = map(Fraction, result.intersection_limits_exact)
    assert left == 0 < right < 1
    assert result.sites[0].counting_interval is not None
    assert result.sites[0].counting_interval.pollen_tail_upper_bounds[0] is None
    swapped = run(counts=[[0, 0], [100, 0]])
    assert swapped.excluded_zero_total_site_indices == (0,)
    left, right = map(Fraction, swapped.intersection_limits_exact)
    assert 0 < left < right == 1


def test_site_permutation_common_scale_and_taxon_permutation() -> None:
    result = run()
    swapped = run(counts=[[4, 6], [3, 7]], responses=[[1, 3], [2, 1]])
    assert result.intersection_limits_exact == swapped.intersection_limits_exact
    scaled = run(responses=[[16, 8], [0.25, 0.75]])
    assert result.intersection_limits_exact == scaled.intersection_limits_exact
    taxa = run(counts=[[7, 3], [6, 4]], responses=[[1, 2], [3, 1]])
    left, right = map(Fraction, result.intersection_limits_exact)
    assert tuple(
        float(Fraction(v)) for v in taxa.intersection_limits_exact
    ) == pytest.approx((float(1 - right), float(1 - left)), abs=1e-14)


def test_supplied_rounded_response_is_authoritative() -> None:
    a = 0.3 * 0.7
    result = run(responses=[[a, 1], [a, 1]])
    assert result.responses[0][0] == a
    p = Fraction.from_float(result.sites[0].pollen_probability_interval[0])
    actual = Fraction(result.sites[0].first_cover_interval_exact[0])
    assert actual == p / (Fraction.from_float(a) * (1 - p) + p)
    assert actual != p / (
        Fraction.from_float(0.3) * Fraction.from_float(0.7) * (1 - p) + p
    )


@pytest.mark.parametrize("near_empty", [False, True])
def test_exact_singleton_or_sub_ulp_empty_intersection(
    monkeypatch: pytest.MonkeyPatch, near_empty: bool
) -> None:
    template = run().sites[0].counting_interval
    assert template is not None
    bounds = iter(((0.5, 0.75), (0.25, 0.5 if near_empty else 0.75)))
    if not near_empty:
        bounds = iter(((0.25, 0.5), (0.5, 0.75)))

    def interval(*args: Any, **kwargs: Any) -> TwoTaxonCountingInterval:
        return replace(template, pollen_probability_interval=next(bounds))

    monkeypatch.setattr(core, "fixed_two_taxon_counting_interval", interval)
    a = [[1, 1], [nextafter(1.0, 2.0), 1]] if near_empty else [[1, 1], [1, 1]]
    result = run(responses=a)
    if near_empty:
        left, right = map(Fraction, result.intersection_limits_exact)
        assert left > right
        assert Fraction.from_float(float(right)) < right < left
        assert nextafter(float(right), 1.0) == float(left)
        assert result.status == "empty"
    else:
        assert result.status == "nonempty"
        assert result.cover_lower_exact == result.cover_upper_exact == ("1/2", "1/2")


@pytest.mark.parametrize(
    "changes",
    [
        {"counts": [[0, 0], [0, 0]]},
        {"counts": [[3, -1], [1, 2]]},
        {"counts": [[3, 0.5], [1, 2]]},
        {"counts": [[True, 3], [1, 2]]},
        {"counts": [[3, inf], [1, 2]]},
        {"counts": [[3, np.nan], [1, 2]]},
        {"counts": [[10000, 1], [1, 2]]},
        {"counts": [[10**500, 1], [1, 2]]},
        {"counts": [[1, 2]]},
        {"counts": [[1, 2, 3], [3, 2, 1]]},
        {"counts": np.ma.array([[0, 2], [3, 4]], mask=[[True, False], [False, False]])},
        {"responses": [[False, 1], [1, 2]]},
        {"responses": [[0, 1], [1, 2]]},
        {"responses": [[-1, 1], [1, 2]]},
        {"responses": [[inf, 1], [1, 2]]},
        {"responses": [[10**500, 1], [1, 2]]},
        {"responses": [[1, 2]]},
        {
            "responses": np.ma.array(
                [[1, 2], [3, 4]], mask=[[True, False], [False, False]]
            )
        },
        {"taxon_measured": [[True, False], [True, True]]},
        {"taxon_measured": [[1, 1], [1, 1]]},
        {"taxon_measured": [[True, True]]},
        {"taxon_measured": np.ma.array([[True, True], [True, True]], mask=True)},
        {"confidence_level": True},
        {"confidence_level": 0},
        {"confidence_level": 1},
        {"confidence_level": inf},
        {"confidence_level": np.nan},
        {"confidence_level": np.ma.masked},
        {"confidence_level": nextafter(1.0, 0.0)},
    ],
)
def test_invalid_inputs_refuse(changes: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        run(**changes)


def test_raw_count_ceiling_accepts_boundary_and_no_mask_numeric_inputs() -> None:
    result = run(
        counts=np.ma.array([[10000, 0], [0, 0]], mask=False),
        responses=np.ma.array([[1, 1], [1, 1]], mask=False),
    )
    assert result.sites[0].total_count == 10000
    assert result.status == "nonempty"
    assert result.intersection_limits_exact[1] == "1"
