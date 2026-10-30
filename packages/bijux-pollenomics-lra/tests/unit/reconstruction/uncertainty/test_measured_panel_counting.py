"""Exact nested-panel regions, full-outcome coverage and missingness refusals."""

from __future__ import annotations

from dataclasses import asdict, replace
from fractions import Fraction
from itertools import product
import json
from math import comb, inf, nextafter
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.uncertainty import (
    measured_panel_counting as core,
)
from bijux_pollenomics_lra.reconstruction.uncertainty.two_taxon_counting import (
    TwoTaxonCountingInterval,
)


def run(**changes: Any) -> core.MeasuredPanelCountingRegion:
    arguments: dict[str, Any] = {
        "complete_counts": [4, 2, 6],
        "partial_counts": [2, 8],
        "complete_responses": [2.0, 3.0, 1.0],
        "partial_responses": [1.0, 3.0],
        "complete_taxon_measured": [True, True, True],
        "partial_taxon_measured": [True, True],
    }
    arguments.update(changes)
    return core.measured_panel_counting_region(**arguments)


def in_joint(
    result: core.MeasuredPanelCountingRegion, cover: tuple[Fraction, Fraction, Fraction]
) -> bool:
    x, y, z = cover
    if result.status == "empty" or min(cover) < 0 or sum(cover) != 1 or x + z <= 0:
        return False
    lower, upper = map(Fraction, result.ratio_interval_exact)
    qlower, qupper = map(Fraction.from_float, result.complete_only_probability_interval)
    a0, a1, a2 = map(Fraction.from_float, result.complete_responses)
    return (
        (1 - lower) * x >= lower * z
        and (1 - upper) * x <= upper * z
        and a1 * (1 - qlower) * y >= qlower * (a0 * x + a2 * z)
        and a1 * (1 - qupper) * y <= qupper * (a0 * x + a2 * z)
    )


def test_exact_joint_polygon_certificates_extrema_and_directed_display() -> None:
    result = run()
    assert result.status == "nonempty" and len(result.corners) == 4
    assert result.excluded_complete_only_vertex is False
    assert result.lower_attained == result.upper_attained == (True, True, True)
    for corner in result.corners:
        v = tuple(map(Fraction, corner.cover))
        assert in_joint(result, (v[0], v[1], v[2]))
        assert v[0] / (v[0] + v[2]) == Fraction(corner.shared_cover_ratio)
        a0, a1, a2 = map(Fraction.from_float, result.complete_responses)
        assert a1 * v[1] / (a0 * v[0] + a1 * v[1] + a2 * v[2]) == Fraction(
            corner.complete_only_pollen_probability
        )
    assert result.cover_lower_exact is not None and result.cover_upper_exact is not None
    assert result.cover_lower is not None and result.cover_upper is not None
    assert (
        result.lower_corner_indices is not None
        and result.upper_corner_indices is not None
    )
    for i in range(3):
        low, high = (
            Fraction(result.cover_lower_exact[i]),
            Fraction(result.cover_upper_exact[i]),
        )
        assert low == min(Fraction(c.cover[i]) for c in result.corners)
        assert high == max(Fraction(c.cover[i]) for c in result.corners)
        assert (
            Fraction.from_float(result.cover_lower[i])
            <= low
            <= high
            <= Fraction.from_float(result.cover_upper[i])
        )
        assert Fraction(result.corners[result.lower_corner_indices[i]].cover[i]) == low
        assert Fraction(result.corners[result.upper_corner_indices[i]].cover[i]) == high
    certificates = [s.counting_interval for s in result.shared_panel_constraints] + [
        result.complete_only_counting
    ]
    for interval in certificates:
        assert (
            interval is not None
            and interval.confidence_level == result.marginal_confidence_level
        )
    assert json.loads(json.dumps(asdict(result)))["profile"] == core.PROFILE


@pytest.mark.parametrize("confidence", [0.95, 0.8, 0.1, nextafter(0.0, 1.0)])
def test_three_way_budget_is_exact_and_minimally_rounded_up(confidence: float) -> None:
    requested, marginal, guarantee = core._confidence(confidence)
    target = (2 + Fraction.from_float(requested)) / 3
    assert Fraction.from_float(marginal) >= target
    assert Fraction.from_float(nextafter(marginal, 0.0)) < target
    assert (
        guarantee
        == 3 * Fraction.from_float(marginal) - 2
        >= Fraction.from_float(confidence)
    )


def controlled_intervals(
    monkeypatch: pytest.MonkeyPatch, bounds: tuple[tuple[float, float], ...]
) -> None:
    template = run().complete_only_counting
    assert template is not None
    intervals = iter(bounds)

    def interval(*args: Any, **kwargs: Any) -> TwoTaxonCountingInterval:
        return replace(template, pollen_probability_interval=next(intervals))

    monkeypatch.setattr(core, "fixed_two_taxon_counting_interval", interval)


def test_coordinate_box_contains_points_outside_the_joint_region(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controlled_intervals(monkeypatch, ((0.4, 0.6), (0.4, 0.6), (0.1, 0.2)))
    result = run(complete_responses=[1, 1, 1], partial_responses=[1, 1])
    point = (Fraction(539, 1000), Fraction(111, 1000), Fraction(350, 1000))
    assert result.cover_lower_exact is not None and result.cover_upper_exact is not None
    assert all(
        Fraction(lo) <= v <= Fraction(hi)
        for lo, v, hi in zip(
            result.cover_lower_exact, point, result.cover_upper_exact, strict=True
        )
    )
    assert sum(point) == 1 and not in_joint(result, point)


def test_all_middle_outcome_keeps_other_site_information_and_unattained_limit() -> None:
    result = run(complete_counts=[0, 5, 0], partial_counts=[2, 3])
    assert result.status == "nonempty"
    first = result.shared_panel_constraints[0]
    assert first.used is False and first.counting_interval is None
    assert first.first_cover_interval_exact == ("0", "1")
    assert result.complete_only_counting is not None
    assert result.excluded_complete_only_vertex is True
    assert (
        result.cover_lower_exact is not None
        and result.cover_lower_exact[0] == result.cover_lower_exact[2] == "0"
    )
    assert result.lower_attained == (False, True, False)
    assert result.upper_attained == (True, False, True)
    assert result.cover_upper_exact is not None and result.cover_upper_exact[1] == "1"
    assert not in_joint(result, (Fraction(0), Fraction(1), Fraction(0)))


def test_fixed_zero_effort_design_returns_whole_valid_domain_without_tail_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_tails(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("An uninformative constraint must not call the CP kernel")

    monkeypatch.setattr(core, "fixed_two_taxon_counting_interval", no_tails)
    result = run(complete_counts=[0, 0, 0], partial_counts=[0, 0])
    assert result.status == "nonempty" and result.no_count_information is True
    assert result.ratio_interval_exact == ("0", "1")
    assert result.complete_only_probability_interval == (0.0, 1.0)
    assert result.complete_only_counting is None
    assert result.cover_lower_exact == ("0", "0", "0")
    assert result.cover_upper_exact == ("1", "1", "1")
    assert result.lower_attained == (True, True, True)
    assert result.upper_attained == (True, False, True)
    assert in_joint(result, (Fraction(1, 4), Fraction(1, 2), Fraction(1, 4)))
    assert not in_joint(result, (Fraction(0), Fraction(1), Fraction(0)))


@pytest.mark.parametrize("r", [0.0, 1.0])
def test_degenerate_shared_ratio_preserves_attained_zero_coordinates(
    monkeypatch: pytest.MonkeyPatch, r: float
) -> None:
    controlled_intervals(monkeypatch, ((r, r), (r, r), (0.5, 1.0)))
    result = run(complete_responses=[1, 1, 1], partial_responses=[1, 1])
    assert result.lower_attained is not None and result.upper_attained is not None
    zero = 0 if r == 0 else 2
    other = 2 - zero
    assert result.cover_lower_exact is not None and result.cover_upper_exact is not None
    assert result.cover_lower_exact[zero] == result.cover_upper_exact[zero] == "0"
    assert result.lower_attained[zero] and result.upper_attained[zero]
    assert result.lower_attained[other] is False
    assert result.upper_attained[1] is False


def test_empty_region_retains_all_constraints_without_repairs() -> None:
    result = run(
        complete_counts=[0, 1, 100],
        partial_counts=[100, 0],
        complete_responses=[1, 1, 1],
        partial_responses=[1, 1],
    )
    assert result.status == "empty"
    assert Fraction(result.ratio_interval_exact[0]) > Fraction(
        result.ratio_interval_exact[1]
    )
    assert result.complete_only_counting is not None
    assert result.corners == ()
    assert result.cover_lower_exact is None and result.cover_upper_exact is None
    assert result.cover_lower is None and result.cover_upper is None


def test_complete_outcome_enumeration_includes_random_zero_shared_effort() -> None:
    ncomplete, npartial = 2, 2
    a = (Fraction(2), Fraction(3), Fraction(1))
    b = (Fraction(1), Fraction(3))
    for r, q in product(
        map(Fraction, [0, 0.5, 1]), (Fraction(0), Fraction(1, 2), Fraction(9, 10))
    ):
        # Independent multinomial factorization, including every all-middle
        # outcome; no successful-fit or positive-projection selection.
        pshared = a[0] * r / (a[0] * r + a[2] * (1 - r))
        p = ((1 - q) * pshared, q, (1 - q) * (1 - pshared))
        pp = b[0] * r / (b[0] * r + b[1] * (1 - r))
        covered = Fraction(0)
        for f in range(ncomplete + 1):
            for first in range(ncomplete - f + 1):
                last = ncomplete - f - first
                mass = (
                    comb(ncomplete, f)
                    * comb(ncomplete - f, first)
                    * p[0] ** first
                    * p[1] ** f
                    * p[2] ** last
                )
                for k in range(npartial + 1):
                    result = run(
                        complete_counts=[first, f, last],
                        partial_counts=[k, npartial - k],
                    )
                    totalmass = (
                        mass * comb(npartial, k) * pp**k * (1 - pp) ** (npartial - k)
                    )
                    low, high = map(Fraction, result.ratio_interval_exact)
                    qlow, qhigh = map(
                        Fraction.from_float, result.complete_only_probability_interval
                    )
                    if low <= r <= high and qlow <= q <= qhigh:
                        covered += totalmass
        assert covered >= Fraction(result.guaranteed_joint_confidence_lower_bound)


def test_common_response_scale_and_shared_taxon_permutation() -> None:
    result = run()
    scaled = run(complete_responses=[16, 24, 8], partial_responses=[0.25, 0.75])
    assert result.cover_lower_exact == scaled.cover_lower_exact
    assert result.cover_upper_exact == scaled.cover_upper_exact
    swapped = run(
        complete_counts=[6, 2, 4],
        partial_counts=[8, 2],
        complete_responses=[1, 3, 2],
        partial_responses=[3, 1],
    )
    assert result.cover_lower_exact is not None and result.cover_upper_exact is not None
    assert swapped.cover_lower is not None and swapped.cover_upper is not None
    assert swapped.cover_lower == pytest.approx(
        tuple(float(Fraction(v)) for v in reversed(result.cover_lower_exact)), abs=1e-14
    )
    assert swapped.cover_upper == pytest.approx(
        tuple(float(Fraction(v)) for v in reversed(result.cover_upper_exact)), abs=1e-14
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"complete_counts": [True, 2, 3]},
        {"complete_counts": [1, None, 2]},
        {"complete_counts": [1, 0.5, 2]},
        {"complete_counts": [1, -1, 2]},
        {"complete_counts": [10000, 1, 0]},
        {"complete_counts": [10**500, 0, 0]},
        {"complete_counts": [1, 2]},
        {"partial_counts": [1, 2, 3]},
        {"complete_counts": [1 + 2j, 2, 3]},
        {"complete_counts": ["1", "2", "3"]},
        {"complete_counts": np.ma.array([1, 2, 3], mask=[False, True, False])},
        {"partial_counts": [1, inf]},
        {"complete_responses": [1, 0, 2]},
        {"partial_responses": [False, 1]},
        {"partial_responses": [1, float("nan")]},
        {"complete_taxon_measured": [True, False, True]},
        {"partial_taxon_measured": [True, False]},
        {"complete_taxon_measured": [1, 1, 1]},
        {"partial_taxon_measured": [True]},
        {"confidence_level": True},
        {"confidence_level": 0},
        {"confidence_level": 1},
        {"confidence_level": nextafter(1.0, 0.0)},
        {"confidence_level": np.ma.masked},
    ],
)
def test_invalid_numeric_measurement_and_certification_domains_refuse(
    changes: dict[str, Any],
) -> None:
    with pytest.raises(ValidationError):
        run(**changes)
