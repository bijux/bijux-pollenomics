"""Refuse source R dimension drops without copying cross-taxon recycling."""

from __future__ import annotations

from typing import NoReturn

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.api import (
    LoveConfig,
    RevealsConfig,
    ValidationError,
    run_love,
    run_reveals,
)
from bijux_pollenomics_lra.reconstruction import optimized


def _inputs(
    fractions: list[float], *, taxa_count: int = 3
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    taxa = ["Alnus", "Betula", "Pinus"][:taxa_count]
    local = pd.DataFrame(
        {
            "coordinate": [1],
            **dict(zip(taxa, [[30], [50], [20]][:taxa_count], strict=True)),
        }
    )
    regional = pd.DataFrame(
        {
            "coordinate": [1],
            **dict(zip(taxa, [[60], [10], [30]][:taxa_count], strict=True)),
        }
    )
    params = pd.DataFrame(
        {
            "Taxon": taxa,
            "fallspeed": [0.024, 0.035, 0.06][:taxa_count],
            "ppe": [0.7, 2.2, 5.5][:taxa_count],
            "ppe.error": [0.0] * taxa_count,
        }
    )
    inner = np.array([10.0, 30.0, 100.0, 500.0])
    outer = np.array([30.0, 100.0, 500.0, 100000.0])
    area = np.pi * (outer**2 - inner**2)
    rings = pd.DataFrame(
        {
            "inner": inner,
            "outer": outer,
            "mean": (inner + outer) / 2,
            "ring": area,
            "terrestrial": area * fractions,
        }
    )
    return local, regional, params, rings


def _config(maximum: int, *, method: str = "optimized") -> LoveConfig:
    return LoveConfig(
        method=method,
        regional_basin_type="lake",
        regional_basin_diameter_m=300,
        local_basin_diameter_m=12,
        max_ring=maximum,
        repeats=1,
        stochastic=False,
    )


@pytest.mark.parametrize(
    ("fractions", "maximum"),
    [([1.0, 0.7, 0.9, 0.6], 1), ([1.0, 0.7, 0.9, 0.6], 2), ([0.0, 0.7, 0.9, 0.6], 3)],
)
def test_source_dimension_drop_is_refused_before_optimizer(
    fractions: list[float], maximum: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_optimizer(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Unsupported source dimensions reached the optimizer")

    monkeypatch.setattr(optimized, "optimize_box", unexpected_optimizer)
    with pytest.raises(ValidationError) as raised:
        run_love(*_inputs(fractions), _config(maximum))
    assert raised.value.reason_code == "unsupported_source_ring_dimensions"


@pytest.mark.parametrize("maximum", [2, 3])
def test_zero_land_dimension_cases_remain_supported(maximum: int) -> None:
    result = run_love(
        *_inputs([0.0, 0.7, 0.9, 0.0]),
        _config(maximum),
        replay_candidates=np.array([[0.2, 0.5, 0.3], [0.6, 0.1, 0.3]]),
    )
    assert result.cover["mean"].iloc[0].isna().all()
    assert np.isfinite(result.cover["mean"].iloc[1:].to_numpy()).all()
    assert len(result.diagnostics) == maximum - 1


def test_single_taxon_does_not_have_cross_taxon_recycling() -> None:
    result = run_love(
        *_inputs([1.0, 0.7, 0.9, 0.6], taxa_count=1),
        _config(1),
        replay_candidates=np.array([[1.0]]),
        regional_cover_draws=np.array([[1.0]]),
    )
    np.testing.assert_array_equal(result.cover["mean"].to_numpy(), [[1.0]])


def test_analytical_one_ring_does_not_use_ring_matrix_column_sums() -> None:
    result = run_love(*_inputs([1.0, 0.7, 0.9, 0.6]), _config(1, method="analytical"))
    assert np.isfinite(result.cover["mean"].to_numpy()).all()


@pytest.mark.parametrize("iterations", [1, 2])
def test_single_taxon_regional_source_wrapper_is_refused(iterations: int) -> None:
    _, regional, params, _ = _inputs([1.0, 0.7, 0.9, 0.6], taxa_count=1)
    with pytest.raises(ValidationError) as raised:
        run_reveals(
            regional,
            params,
            RevealsConfig(
                basin_type="lake",
                basin_diameter_m=300,
                iterations=iterations,
                stochastic=False,
            ),
        )
    assert raised.value.reason_code == "unsupported_source_taxon_dimensions"


@pytest.mark.parametrize("method", ["analytical", "optimized"])
def test_single_taxon_internal_regional_recomputation_is_refused(method: str) -> None:
    with pytest.raises(ValidationError) as raised:
        run_love(
            *_inputs([1.0, 0.7, 0.9, 0.6], taxa_count=1), _config(1, method=method)
        )
    assert raised.value.reason_code == "unsupported_source_taxon_dimensions"


def test_single_taxon_supplied_regional_analytical_path_remains_supported() -> None:
    result = run_love(
        *_inputs([1.0, 0.7, 0.9, 0.6], taxa_count=1),
        _config(1, method="analytical"),
        regional_cover_draws=np.array([[1.0]]),
    )
    np.testing.assert_allclose(result.cover["mean"].to_numpy(), [[1.0]], atol=1e-14)
