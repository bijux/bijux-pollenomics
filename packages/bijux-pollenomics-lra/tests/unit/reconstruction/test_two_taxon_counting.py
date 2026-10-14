"""Independent boundaries and scope refusals for two-taxon intervals."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal, Underflow
from fractions import Fraction
from math import comb
from typing import Any

import numpy as np
import pytest

import bijux_pollenomics_lra as lra
from bijux_pollenomics_lra import api
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction import two_taxon_counting as interval_module
from bijux_pollenomics_lra.reconstruction.two_taxon_counting import (
    PROFILE,
    fixed_two_taxon_counting_interval,
)


def test_additive_api_preserves_joint_aliquot_exports() -> None:
    for symbol in [
        "AliquotCountInput",
        "AliquotResultInput",
        "JointAliquotCovariance",
        "joint_aliquot_covariance",
    ]:
        assert getattr(api, symbol).__module__.endswith("joint_aliquot_covariance")
        assert symbol in api.__all__
    capabilities = api.extension_descriptor()["capabilities"]
    assert "lra.reveals.multisite.joint-aliquot-delta-covariance" in capabilities
    assert "lra.reveals.two-taxon.fixed-response-binomial-interval" in capabilities


def test_public_facade_and_zero_count_closed_form() -> None:
    assert lra.fixed_two_taxon_counting_interval is fixed_two_taxon_counting_interval
    result = fixed_two_taxon_counting_interval(
        [0, 10], [1, 1], [1, 1], taxon_measured=[True, True]
    )
    expected = 1 - ((1 - 0.95) / 2) ** (1 / 10)
    assert result.cover == (0, 1)
    assert result.cover_lower[0] == 0
    assert result.cover_upper[0] == pytest.approx(expected, abs=2e-15)
    assert 0 < result.cover_upper[0] < 1
    assert result.total_count == 10
    assert result.profile == PROFILE
    with pytest.raises(FrozenInstanceError):
        result.total_count = 20  # type: ignore[misc]


def test_fixed_response_transform_and_joint_complement() -> None:
    result = fixed_two_taxon_counting_interval(
        [40, 60], [1, 1], [1, 2], taxon_measured=[True, True]
    )
    assert result.cover == pytest.approx((4 / 7, 3 / 7))
    assert result.cover_lower[0] < result.cover[0] < result.cover_upper[0]
    low_p, high_p = map(Fraction.from_float, result.pollen_probability_interval)
    assert Fraction.from_float(result.cover_lower[1]) <= (1 - high_p) / (1 + high_p)
    assert Fraction.from_float(result.cover_upper[1]) >= (1 - low_p) / (1 + low_p)
    reverse = fixed_two_taxon_counting_interval(
        [60, 40], [1, 1], [2, 1], taxon_measured=[True, True]
    )
    assert reverse.cover == pytest.approx(result.cover[::-1], abs=2e-15)
    assert reverse.cover_lower == pytest.approx(result.cover_lower[::-1], abs=2e-15)
    assert reverse.cover_upper == pytest.approx(result.cover_upper[::-1], abs=2e-15)


@pytest.mark.parametrize("count", [0, 1, 4, 9, 10])
def test_confidence_nesting_and_common_response_scale(count: int) -> None:
    low = fixed_two_taxon_counting_interval(
        [count, 10 - count],
        [2, 4],
        [3, 1],
        taxon_measured=[True, True],
        confidence_level=0.8,
    )
    high = fixed_two_taxon_counting_interval(
        [count, 10 - count],
        [2, 4],
        [3, 1],
        taxon_measured=[True, True],
        confidence_level=0.99,
    )
    scaled = fixed_two_taxon_counting_interval(
        [count, 10 - count],
        [2000, 4000],
        [3, 1],
        taxon_measured=[True, True],
        confidence_level=0.8,
    )
    assert high.cover_lower[0] <= low.cover_lower[0]
    assert high.cover_upper[0] >= low.cover_upper[0]
    assert low.cover_lower == pytest.approx(scaled.cover_lower, abs=2e-15)
    assert low.cover_upper == pytest.approx(scaled.cover_upper, abs=2e-15)


@pytest.mark.parametrize(
    "counts",
    [
        [0, 0],
        [-1, 10],
        [0.5, 10],
        [True, False],
        [True, 9],
        [1, np.bool_(True)],
        ["1", "9"],
        [1, 2, 3],
        [[1, 9]],
        [np.nan, 1],
        [np.inf, 1],
        [2**53, 0],
        [2**53 - 1, 1],
    ],
)
def test_invalid_counts_and_repeated_sample_axes_refuse(counts: Any) -> None:
    with pytest.raises(ValidationError):
        fixed_two_taxon_counting_interval(
            counts, [1, 1], [1, 1], taxon_measured=[True, True]
        )


@pytest.mark.parametrize("level", [0, 1, -0.1, np.nan, np.inf, True, "0.95", [0.95]])
def test_invalid_confidence_refuses(level: Any) -> None:
    with pytest.raises(ValidationError):
        fixed_two_taxon_counting_interval(
            [1, 9], [1, 1], [1, 1], taxon_measured=[True, True], confidence_level=level
        )


@pytest.mark.parametrize(
    "mask", [[True, False], [False, False], [1, 1], [[True, True]]]
)
def test_unmeasured_or_untyped_masks_refuse(mask: Any) -> None:
    with pytest.raises(ValidationError):
        fixed_two_taxon_counting_interval([0, 10], [1, 1], [1, 1], taxon_measured=mask)


@pytest.mark.parametrize(
    "response",
    [
        [0, 1],
        [-1, 1],
        [np.nan, 1],
        [np.inf, 1],
        [1, 2, 3],
        [True, True],
        [True, 1],
        ["1", "1"],
    ],
)
def test_invalid_response_or_productivity_refuses(response: Any) -> None:
    with pytest.raises(ValidationError):
        fixed_two_taxon_counting_interval(
            [1, 9], response, [1, 1], taxon_measured=[True, True]
        )
    with pytest.raises(ValidationError):
        fixed_two_taxon_counting_interval(
            [1, 9], [1, 1], response, taxon_measured=[True, True]
        )


def test_product_overflow_and_unrepresentable_ratio_refuse() -> None:
    with pytest.raises(ValidationError, match="finite positive"):
        fixed_two_taxon_counting_interval(
            [1, 9], [1e308, 1], [1e308, 1], taxon_measured=[True, True]
        )
    with pytest.raises(ValidationError, match="interior cover"):
        fixed_two_taxon_counting_interval(
            [1, 9], [1e-250, 1], [1, 1], taxon_measured=[True, True]
        )


def test_failed_predecessor_case_has_exact_rational_tail_certificates() -> None:
    result = fixed_two_taxon_counting_interval(
        [2, 3], [1, 1], [1, 1], taxon_measured=[True, True]
    )
    lower, upper = map(Fraction.from_float, result.pollen_probability_interval)
    target = (1 - Fraction.from_float(0.95)) / 2
    lower_tail = sum(
        Fraction(comb(5, count)) * lower**count * (1 - lower) ** (5 - count)
        for count in range(2, 6)
    )
    upper_tail = sum(
        Fraction(comb(5, count)) * upper**count * (1 - upper) ** (5 - count)
        for count in range(3)
    )
    assert lower_tail <= target and upper_tail <= target
    assert result.pollen_probability_interval[0] < 0.052744950526316926
    for certificate in result.pollen_tail_upper_bounds:
        assert certificate is not None
        assert Decimal(certificate) <= Decimal(result.tail_target_lower_bound)


def test_maximum_count_domain_and_outside_refusal() -> None:
    result = fixed_two_taxon_counting_interval(
        [0, 10000], [1, 1], [1, 1], taxon_measured=[True, True]
    )
    assert result.total_count == 10000
    assert result.cover_lower[0] == 0 < result.cover_upper[0]
    assert result.pollen_tail_upper_bounds[0] is None
    with pytest.raises(ValidationError):
        fixed_two_taxon_counting_interval(
            [1, 10000], [1, 1], [1, 1], taxon_measured=[True, True]
        )


def test_invalid_inverse_seed_refuses_with_finite_adjustment_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    interval_module._probability_bounds.cache_clear()
    monkeypatch.setattr(interval_module, "betaincinv", lambda *args: 0.5)
    monkeypatch.setattr(interval_module, "MAX_TAIL_EVALUATIONS", 2)
    try:
        with pytest.raises(ValidationError, match="evaluation budget"):
            fixed_two_taxon_counting_interval(
                [2, 3],
                [1, 1],
                [1, 1],
                taxon_measured=[True, True],
                confidence_level=0.94,
            )
    finally:
        interval_module._probability_bounds.cache_clear()


def test_range_loss_is_trapped_and_complement_is_exact() -> None:
    tiny = Decimal.from_float(float.fromhex("0x0.0000000000001p-1022"))
    complement = interval_module._complement(tiny)
    assert Fraction(complement) + Fraction(tiny) == 1
    for upper in [False, True]:
        with pytest.raises(Underflow):
            interval_module._power(
                Decimal("1e-1000000"),
                10000,
                interval_module._context(upper=upper),
            )


def test_rational_cover_conversion_protects_both_complements() -> None:
    result = fixed_two_taxon_counting_interval(
        [2, 3], [0.1, 0.7], [0.3, 1.1], taxon_measured=[True, True]
    )
    first_factor = 1 / (Fraction.from_float(0.1) * Fraction.from_float(0.3))
    second_factor = 1 / (Fraction.from_float(0.7) * Fraction.from_float(1.1))
    lower, upper = map(Fraction.from_float, result.pollen_probability_interval)
    low = first_factor * lower / (first_factor * lower + second_factor * (1 - lower))
    high = first_factor * upper / (first_factor * upper + second_factor * (1 - upper))
    assert Fraction.from_float(result.cover_lower[0]) <= low
    assert Fraction.from_float(result.cover_upper[0]) >= high
    assert Fraction.from_float(result.cover_lower[1]) <= 1 - high
    assert Fraction.from_float(result.cover_upper[1]) >= 1 - low


def test_large_inverse_seed_error_is_bracketed_without_padding_budget() -> None:
    result = fixed_two_taxon_counting_interval(
        [494, 506],
        [1, 1],
        [1, 1],
        taxon_measured=[True, True],
        confidence_level=0.8,
    )
    assert result.pollen_probability_interval[1] > 0.5147563571785774
    assert all(1 <= count <= 128 for count in result.bound_search_evaluations)
    assert result.bound_search_evaluations[1] < 32
    for certificate in result.pollen_tail_upper_bounds:
        assert certificate is not None
        assert Decimal(certificate) <= Decimal(result.tail_target_lower_bound)


def test_exact_domain_boundaries_remain_safe_when_seed_is_extreme(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    interval_module._probability_bounds.cache_clear()
    monkeypatch.setattr(interval_module, "betaincinv", lambda *args: 0.0)
    monkeypatch.setattr(interval_module, "betainccinv", lambda *args: 1.0)
    try:
        result = fixed_two_taxon_counting_interval(
            [2, 3],
            [1, 1],
            [1, 1],
            taxon_measured=[True, True],
            confidence_level=0.93,
        )
        assert result.pollen_probability_interval == (0, 1)
        assert result.pollen_tail_upper_bounds == ("0", "0")
        assert result.bound_search_evaluations == (1, 1)
    finally:
        interval_module._probability_bounds.cache_clear()
