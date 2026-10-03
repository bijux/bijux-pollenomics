"""Independent analytical LOVE scale and finite-correction regressions."""

from __future__ import annotations

from decimal import Decimal, localcontext

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.analytical import lov

SMALLEST = float(np.nextafter(0.0, 1.0))


def parameters(size: int, *, tiny_error: bool = False) -> dict[str, object]:
    return {
        "ppes": pd.DataFrame(
            {
                "Taxon": [f"T{i}" for i in range(size)],
                "fallspeed": np.full(size, 0.02),
                "ppe": np.full(size, SMALLEST if tiny_error else 1.0),
                "ppe.error": np.full(size, SMALLEST if tiny_error else 0.0),
            }
        ),
        "error": tiny_error,
    }


def sample(counts: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"age": [0.0], **{f"T{i}": [v] for i, v in enumerate(counts)}})


def cross_product_oracle(
    counts: list[float], ppe: list[float], background: list[float]
) -> np.ndarray:
    # Eliminate reciprocal-PPE weights and closure before evaluating the two
    # local fractions. Decimal holds the exact supplied binary-float scalars;
    # this is independent of the engine's vector normalization/fallback path.
    with localcontext() as context:
        context.prec = 1800
        a, b = map(Decimal.from_float, counts)
        pa, pb = map(Decimal.from_float, ppe)
        sa, sb = map(Decimal.from_float, background)
        denominator = a * pb + b * pa
        first = (a * pb * (1 + sb) - b * pa * sa) / denominator
        second = (b * pa * (1 + sa) - a * pb * sb) / denominator
        return np.array([float(first), float(second)])


@pytest.mark.parametrize(
    "counts,ppe,background",
    [
        ([1e308, 1e308], [1e-308, 1e-308], [0.25, 0.125]),
        ([1e308, 1e308], [1.0, 1.0], [0.25, 0.125]),
        ([SMALLEST, SMALLEST], [1e308, 1e308], [0.25, 0.125]),
        ([SMALLEST, 1.0], [10.0, 1.0], [0.0, 9.0]),
        ([1e-300, 1.0], [1e50, 1.0], [0.0, 1e100]),
        ([1.0, 1.0], [1.0, 1.0], [1e100, 1e100]),
        ([1.0, 1.0], [1.0, 1.0], [1e308, 1e308]),
        ([1.0, 0.0], [1e-308, 1e-308], [0.0, 2.0]),
    ],
    ids=[
        "weight-overflow",
        "sum-overflow",
        "all-weight-underflow",
        "amplified-smallest-subnormal",
        "amplified-underflow-and-subtraction",
        "background-loses-unit",
        "background-sum-overflow",
        "zero-count-outlier",
    ],
)
def test_finite_equation_uses_only_final_representable_local_cover(
    counts: list[float], ppe: list[float], background: list[float]
) -> None:
    observed = sample(counts)
    original = observed.copy(deep=True)
    expected = cross_product_oracle(counts, ppe, background)
    with np.errstate(all="ignore"):
        result = lov(observed, background, parameters(2), alpha=ppe, stochastic=False)
        reverse = lov(
            sample(counts[::-1]),
            background[::-1],
            parameters(2),
            alpha=ppe[::-1],
            stochastic=False,
        )
    np.testing.assert_array_equal(result, expected)
    np.testing.assert_array_equal(reverse[::-1], expected)
    assert np.isfinite(result).all()
    pd.testing.assert_frame_equal(observed, original)
    if background == [0.0, 9.0]:
        assert result[0] == SMALLEST
    if background == [0.0, 2.0]:
        assert result[0] > 1 and result[1] < 0


@pytest.mark.parametrize(
    "count_scale,ppe_scale", [(1e307, 1e-308), (1e-308, 1e307), (1.0, 1.0)]
)
def test_common_count_and_ppe_units_preserve_local_composition(
    count_scale: float, ppe_scale: float
) -> None:
    counts = [count_scale, 2 * count_scale]
    ppe = [ppe_scale, 4 * ppe_scale]
    background = [0.5, 0.125]
    expected = cross_product_oracle(counts, ppe, background)
    with np.errstate(all="ignore"):
        result = lov(
            sample(counts), background, parameters(2), alpha=ppe, stochastic=False
        )
    np.testing.assert_allclose(result, expected, rtol=2e-16, atol=0)
    np.testing.assert_allclose(result, [7 / 12, 5 / 12], rtol=2e-16, atol=0)


def test_ordinary_equation_keeps_original_arithmetic_and_raw_outliers() -> None:
    counts, ppe, background = (
        np.array([10.0, 90.0]),
        np.array([1.0, 2.0]),
        np.array([2.0, 0.0]),
    )
    weighted = counts / ppe
    source_equation = weighted / weighted.sum() * (1 + background.sum()) - background
    result = lov(
        sample(counts.tolist()), background, parameters(2), alpha=ppe, stochastic=False
    )
    np.testing.assert_array_equal(result, source_equation)
    assert result[0] < 0 and result[1] > 1


def test_actual_zero_ppe_draw_refuses_an_undefined_equation() -> None:
    expected_draw = np.random.default_rng(2).normal(
        [SMALLEST, SMALLEST], [SMALLEST, SMALLEST]
    )
    assert expected_draw[0] > 0 and expected_draw[1] == 0
    with pytest.raises(ValidationError, match="PPE.*strictly positive"):
        lov(
            sample([10.0, 20.0]),
            [0.25, 0.125],
            parameters(2, tiny_error=True),
            rng=2,
            stochastic=True,
            counts=[10.0, 20.0],
        )


def test_unrepresentable_final_equation_is_refused_without_clipping() -> None:
    largest = float(np.finfo(float).max)
    with (
        np.errstate(all="ignore"),
        pytest.raises(ValidationError, match="finite floating-point range"),
    ):
        lov(
            sample([1.0, 0.0, 0.0]),
            [0.0, largest, largest],
            parameters(3),
            stochastic=False,
        )


def test_actual_overflowed_ppe_draw_refuses_an_undefined_equation() -> None:
    largest = float(np.finfo(float).max)
    params = parameters(2)
    table = params["ppes"]
    assert isinstance(table, pd.DataFrame)
    table["ppe"] = largest
    table["ppe.error"] = largest
    params["error"] = True
    with np.errstate(all="ignore"):
        expected_draw = np.random.default_rng(0).normal(
            [largest, largest], [largest, largest]
        )
        assert np.isinf(expected_draw[0]) and expected_draw[1] > 0
        with pytest.raises(ValidationError, match="PPE.*finite.*strictly positive"):
            lov(
                sample([10.0, 20.0]),
                [0.25, 0.125],
                params,
                rng=0,
                stochastic=True,
                counts=[10.0, 20.0],
            )
