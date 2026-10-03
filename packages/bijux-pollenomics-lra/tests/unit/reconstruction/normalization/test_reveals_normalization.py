"""Independent equation B1 ratios across finite floating-point input scales."""

from __future__ import annotations

from fractions import Fraction
import warnings

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.regional import REVEALS, reveals_cover


def _exact_percentages(
    counts: list[float], ppe: list[float], deposition: list[float]
) -> list[float]:
    """Use exact binary input rationals, without floating products or logarithms."""
    weights = [
        Fraction(count) / Fraction(productivity) / Fraction(kernel)
        for count, productivity, kernel in zip(counts, ppe, deposition, strict=True)
    ]
    total = sum(weights, Fraction())
    return [float(100 * weight / total) for weight in weights]


@pytest.mark.parametrize(
    "count_scale,ppe_scale,kernel_scale",
    [
        (1.0, 1e-200, 1e-200),
        (1.0, 1e200, 1e200),
        (1e100, 1e-200, 1e-100),
        (1e307, 1.0, 1.0),
        (1.0, 1.0, 1.0),
        (1.0, 1e-200, 1e-120),
        (1e-200, 1e100, 1e20),
    ],
)
def test_common_units_preserve_exact_ratio_and_closed_cover(
    count_scale: float,
    ppe_scale: float,
    kernel_scale: float,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # macOS ARM can expose longdouble with only float64 precision. The equation
    # must remain stable without relying on an extended NumPy scalar type.
    monkeypatch.setattr(np, "longdouble", np.float64)
    counts = [2 * count_scale, 8 * count_scale, 0.0]
    ppe = [ppe_scale, 4 * ppe_scale, 2 * ppe_scale]
    deposition = [kernel_scale] * 3
    before = [values.copy() for values in (counts, ppe, deposition)]
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        actual = reveals_cover(counts, ppe, deposition, round_digits=None)
    np.testing.assert_allclose(
        actual, _exact_percentages(counts, ppe, deposition), rtol=0, atol=1e-10
    )
    assert actual.dtype == np.dtype(np.float64)
    assert actual.sum() == pytest.approx(100.0, abs=1e-10)
    assert actual[2] == 0.0
    assert [counts, ppe, deposition] == before


@pytest.mark.parametrize("kernel_scale", [1e-200, 1e200])
def test_supplied_draw_summaries_use_closed_independent_ratios(
    kernel_scale: float,
) -> None:
    counts = np.array([[2.0, 8.0, 0.0], [0.0, 8.0, 4.0], [1.0, 4.0, 2.0]])
    ppe = np.tile(np.array([1.0, 4.0, 2.0]) * kernel_scale, (3, 1))
    deposition = [kernel_scale] * 3
    counts_before, ppe_before = counts.copy(), ppe.copy()
    params = pd.DataFrame({"ppe": [1.0, 4.0, 2.0], "ppe.error": [0.0, 0.0, 0.0]})
    generator = np.random.default_rng(123)
    state = generator.bit_generator.state
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = REVEALS(
            [1500.0, 2.0, 8.0, 0.0],
            3,
            params,
            deposition=deposition,
            pollen_draws=counts,
            ppe_draws=ppe,
            rng=generator,
            return_samples=True,
        )
    # The three adjusted count rows are exactly proportional to (1,1,0),
    # (0,1,1), and (1,1,1); source draw rounding precedes the summaries.
    expected = np.array(
        [[50.0, 50.0, 0.0], [0.0, 50.0, 50.0], [33.333, 33.333, 33.333]]
    )
    np.testing.assert_array_equal(result["samples"], expected)
    np.testing.assert_allclose(
        result["meansim"],
        [27.777666666666665, 44.44433333333333, 27.777666666666665],
        rtol=0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result["mediansim"], [33.333, 50.0, 33.333], rtol=0, atol=1e-12
    )
    np.testing.assert_allclose(
        result["q10sim"], [6.6666, 36.6664, 6.6666], rtol=0, atol=1e-12
    )
    np.testing.assert_allclose(
        result["q90sim"], [46.6666, 50.0, 46.6666], rtol=0, atol=1e-12
    )
    np.testing.assert_allclose(
        result["sdsim"],
        [25.458717491918822, 9.622696936583493, 25.458717491918822],
        rtol=0,
        atol=1e-10,
    )
    np.testing.assert_array_equal(counts, counts_before)
    np.testing.assert_array_equal(ppe, ppe_before)
    assert generator.bit_generator.state == state


@pytest.mark.parametrize(
    "counts,ppe,deposition",
    [([0, 0], [1, 1], [1, 1]), ([2, 8], [0, 4], [1, 1]), ([2, 8], [1, 4], [0, 1])],
)
def test_scaling_fallback_does_not_admit_zero_mass_or_denominators(
    counts: list[float], ppe: list[float], deposition: list[float]
) -> None:
    with pytest.raises(ValidationError):
        reveals_cover(counts, ppe, deposition)


def test_positive_cover_survives_an_underflowed_factor_product() -> None:
    counts = [1.0, 1.0]
    ppe = [1e-308, 1.0]
    deposition = [1e-308, 1e-308]
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        actual = reveals_cover(counts, ppe, deposition, round_digits=None)
    expected = _exact_percentages(counts, ppe, deposition)
    assert 0.0 < actual[1] < 1e-300
    np.testing.assert_allclose(actual, expected, rtol=1e-10, atol=0)


@pytest.mark.parametrize("ppe_scale", [1.0, 1e200])
@pytest.mark.parametrize("second_ppe_ratio", [10.0, 100.0])
def test_smallest_count_has_a_representable_positive_percentage(
    ppe_scale: float, second_ppe_ratio: float, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(np, "longdouble", np.float64)
    smallest = float(np.nextafter(0.0, 1.0))
    counts = [1.0, smallest]
    ppe = [ppe_scale, second_ppe_ratio * ppe_scale]
    deposition = [1.0, 1.0]
    expected = _exact_percentages(counts, ppe, deposition)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        actual = reveals_cover(counts, ppe, deposition, round_digits=None)
    assert expected[1] > 0.0
    # Absolute comparisons would accept zero at this scale; exact equality
    # verifies the independently rounded rational percentage survives.
    np.testing.assert_array_equal(actual, expected)
    assert actual.sum() == 100.0
