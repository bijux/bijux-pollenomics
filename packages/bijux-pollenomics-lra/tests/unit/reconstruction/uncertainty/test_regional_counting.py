"""Exact source-equation tests for conditional local/regional counting sets."""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from math import inf, nextafter
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.uncertainty import regional_counting as core


def run(**changes: Any) -> core.RegionalCountingSet:
    inputs: dict[str, Any] = {
        "local_counts": [3, 7],
        "regional_counts": [3, 5],
        "local_kernel": [2.0, 3.0],
        "regional_kernel": [4.0, 1.0],
        "regional_deposition": [3.0, 2.0],
        "ppe": [2.0, 1.0],
        "local_taxon_measured": [True, True],
        "regional_taxon_measured": [True, True],
    }
    inputs.update(changes)
    return core.regional_two_taxon_counting_set(**inputs)


def source_inverse(
    p: Fraction,
    c: Fraction,
    local: tuple[Fraction, ...],
    regional: tuple[Fraction, ...],
    ppe: tuple[Fraction, ...],
) -> Fraction:
    """Solve p/(1-p) through the original taxon-specific pollen balance."""
    d = c * local[0] + (1 - c) * local[1]
    return (
        p * ppe[1] * (d + (1 - c) * regional[1]) - (1 - p) * ppe[0] * c * regional[0]
    ) / (d * ((1 - p) * ppe[0] + p * ppe[1]))


@pytest.mark.parametrize(
    "local,regional,ppe",
    [
        ((2.0, 3.0), (4.0, 1.0), (2.0, 1.0)),
        ((1.0, 1.0), (0.0, 0.0), (1.0, 1.0)),
        ((0.1, 4.0), (0.0, 3.0), (0.7, 2.1)),
    ],
)
def test_exact_rectangle_corners_grid_and_matched_control(
    local: tuple[float, ...], regional: tuple[float, ...], ppe: tuple[float, ...]
) -> None:
    result = run(local_kernel=local, regional_kernel=regional, ppe=ppe)
    k, b, q = [
        tuple(map(Fraction.from_float, values)) for values in (local, regional, ppe)
    ]
    p0, p1 = map(Fraction.from_float, result.local_counting.pollen_probability_interval)
    c0, c1 = map(Fraction, result.regional_cover_interval)
    expected = [source_inverse(p, c, k, b, q) for p, c in product((p0, p1), (c0, c1))]
    assert [Fraction(c.signed_cover[0]) for c in result.corners] == expected
    left, right = min(expected), max(expected)
    assert Fraction(result.image.signed_cover_lower_exact[0]) == left
    assert Fraction(result.image.signed_cover_upper_exact[0]) == right
    assert expected[result.signed_lower_corner] == left
    assert expected[result.signed_upper_corner] == right
    for i, j in product(range(7), repeat=2):
        p, c = p0 + (p1 - p0) * i / 6, c0 + (c1 - c0) * j / 6
        assert left <= source_inverse(p, c, k, b, q) <= right
        assert source_inverse(
            1 - p, 1 - c, k[::-1], b[::-1], q[::-1]
        ) == 1 - source_inverse(p, c, k, b, q)
    control = result.fixed_regional_control
    cp = Fraction(result.regional_point_cover_exact[0])
    assert c0 <= cp <= c1
    assert control.local_confidence_level == result.marginal_confidence_level
    fixed = [source_inverse(p, cp, k, b, q) for p in (p0, p1)]
    assert [Fraction(pair[0]) for pair in control.pollen_endpoint_signed_cover] == fixed
    assert left <= fixed[0] <= fixed[1] <= right
    assert Fraction(control.image.signed_cover_lower_exact[0]) == fixed[0]
    assert Fraction(control.image.signed_cover_upper_exact[0]) == fixed[1]
    for image in (result.image, control.image):
        for exact, display in zip(
            image.signed_cover_lower_exact, image.signed_cover_lower, strict=True
        ):
            assert Fraction.from_float(display) <= Fraction(exact)
        for exact, display in zip(
            image.signed_cover_upper_exact, image.signed_cover_upper, strict=True
        ):
            assert Fraction.from_float(display) >= Fraction(exact)
        if image.status == "nonempty":
            assert image.cover_lower is not None and image.cover_upper is not None
            assert (
                image.cover_lower_exact is not None
                and image.cover_upper_exact is not None
            )
            for exact, display in zip(
                image.cover_lower_exact, image.cover_lower, strict=True
            ):
                assert 0 <= Fraction.from_float(display) <= Fraction(exact) <= 1
            for exact, display in zip(
                image.cover_upper_exact, image.cover_upper, strict=True
            ):
                assert 0 <= Fraction(exact) <= Fraction.from_float(display) <= 1


def test_exact_regional_transform_and_control_do_not_reuse_rounded_covers() -> None:
    result = run()
    assert Fraction(result.regional_point_cover_exact[0]) == Fraction(1, 6)
    assert Fraction(
        result.fixed_regional_control.regional_cover_exact[0]
    ) != Fraction.from_float(result.regional_counting.cover[0])
    for endpoint, c in zip(
        result.regional_counting.pollen_probability_interval,
        result.regional_cover_interval,
        strict=True,
    ):
        r = Fraction.from_float(endpoint)
        assert Fraction(c) == (r / 6) / (r / 6 + (1 - r) / 2)
    assert Fraction(result.regional_cover_interval[0]) != Fraction.from_float(
        result.regional_counting.cover_lower[0]
    )


@pytest.mark.parametrize("confidence", [0.95, 0.8, 0.1, nextafter(0.0, 1.0)])
def test_directed_confidence_budget_retains_both_tail_certificates(
    confidence: float,
) -> None:
    result = run(confidence_level=confidence)
    target = (1 + Fraction.from_float(confidence)) / 2
    marginal = Fraction.from_float(result.marginal_confidence_level)
    assert marginal >= target
    assert (
        Fraction.from_float(nextafter(result.marginal_confidence_level, 0.0)) < target
    )
    assert (
        Fraction(result.guaranteed_joint_confidence_lower_bound)
        == 2 * marginal - 1
        >= Fraction.from_float(confidence)
    )
    for interval in (result.local_counting, result.regional_counting):
        assert interval.confidence_level == result.marginal_confidence_level
        assert all(
            certificate is not None for certificate in interval.pollen_tail_upper_bounds
        )
        assert all(0 < n <= 128 for n in interval.bound_search_evaluations)


def test_empty_full_singleton_and_signed_point_are_distinct() -> None:
    empty = run(
        local_counts=[0, 100],
        regional_counts=[100, 0],
        local_kernel=[1.0, 1.0],
        regional_kernel=[1.0, 1.0],
        regional_deposition=[1.0, 1.0],
        ppe=[1.0, 1.0],
    )
    assert empty.image.status == "empty"
    assert empty.image.cover_lower is empty.image.cover_upper is None
    assert empty.image.cover_lower_exact is empty.image.cover_upper_exact is None
    assert empty.signed_point_cover == (-1.0, 2.0)
    assert Fraction(empty.image.signed_cover_upper_exact[0]) < 0
    full = run(
        local_counts=[0, 1],
        regional_counts=[1, 0],
        local_kernel=[1.0, 1.0],
        regional_kernel=[1.0, 1.0],
        regional_deposition=[1.0, 1.0],
        ppe=[1.0, 1.0],
    )
    assert full.image.status == "nonempty"
    assert full.image.cover_lower == (0.0, 0.0) and full.image.cover_upper == (1.0, 1.0)
    assert full.signed_point_cover == (-1.0, 2.0)
    singleton = core._image(Fraction(-1), Fraction(0))
    assert singleton.status == "nonempty"
    assert singleton.cover_lower == singleton.cover_upper == (0.0, 1.0)


def test_zero_background_removes_all_regional_sensitivity() -> None:
    result = run(regional_kernel=[0.0, 0.0])
    assert result.image == result.fixed_regional_control.image
    assert result.corners[0].signed_cover == result.corners[1].signed_cover
    assert result.corners[2].signed_cover == result.corners[3].signed_cover


@pytest.mark.parametrize(
    "changes",
    [
        {"local_kernel": [0.0, 1.0]},
        {"regional_kernel": [-1.0, 1.0]},
        {"regional_deposition": [0.0, 1.0]},
        {"ppe": [True, 1.0]},
        {"local_counts": [False, 2]},
        {"regional_counts": [1.5, 2]},
        {"local_counts": [0, 0]},
        {"regional_counts": [10_000, 1]},
        {"local_taxon_measured": [True, False]},
        {"regional_taxon_measured": [False, True]},
        {"confidence_level": True},
        {"confidence_level": 1.0},
        {"confidence_level": nextafter(1.0, 0.0)},
        {"ppe": [inf, 1.0]},
        {"regional_deposition": [nextafter(0.0, 1.0), 1.0]},
        {"local_kernel": [nextafter(0.0, 1.0)] * 2, "regional_kernel": [1e308, 1e308]},
    ],
)
def test_strict_admission_and_numerical_refusals(changes: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        run(**changes)


def test_tail_certification_refusal_is_not_replaced_by_a_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(*args: Any, **kwargs: Any) -> Any:
        raise ValidationError(
            "Controlled tail-certification refusal",
            reason_code="counting_interval_certification",
        )

    monkeypatch.setattr(core, "fixed_two_taxon_counting_interval", refuse)
    with pytest.raises(ValidationError, match="tail-certification"):
        run()


def test_signed_outward_display_encloses_negative_fractions() -> None:
    value = Fraction(-1, 3)
    assert Fraction.from_float(core._signed_display(value, upper=False)) <= value
    assert Fraction.from_float(core._signed_display(value, upper=True)) >= value
    with pytest.raises(ValidationError, match="finite binary64"):
        core._signed_display(Fraction(10**400), upper=True)


def test_unresolved_confidence_cannot_receive_a_bonferroni_budget() -> None:
    with pytest.raises(ValidationError, match="masked, unresolved missing"):
        run(confidence_level=np.ma.array(0.95, mask=True))


def test_fully_observed_masks_preserve_regional_set_exactly() -> None:
    expected = run()
    observed = run(
        local_counts=np.ma.array([3, 7], mask=False),
        regional_counts=np.ma.array([3, 5], mask=False),
        local_kernel=np.ma.array([2.0, 3.0], mask=False),
        regional_kernel=np.ma.array([4.0, 1.0], mask=False),
        regional_deposition=np.ma.array([3.0, 2.0], mask=False),
        ppe=np.ma.array([2.0, 1.0], mask=False),
        local_taxon_measured=np.ma.array([True, True], mask=False),
        regional_taxon_measured=np.ma.array([True, True], mask=False),
        confidence_level=np.ma.array(0.95, mask=False),
    )
    assert observed == expected
