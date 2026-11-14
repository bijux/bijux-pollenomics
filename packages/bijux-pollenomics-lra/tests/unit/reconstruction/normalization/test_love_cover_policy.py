"""Nonnegative LOVE cover assumptions and retained source diagnostics."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.models.configuration import (
    LoveConfig,
    RegionalDrawLoveConfig,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.resources.examples import load_love_example
from bijux_pollenomics_lra.workflows.local import run_love


@pytest.mark.parametrize(
    "values,expected",
    [
        ([70, 35, -5], [2 / 3, 1 / 3, 0]),
        ([80, 35, -10, -5], [16 / 23, 7 / 23, 0, 0]),
        ([0, -4, 7], [0, 0, 1]),
        ([0.2, 0.3, 0.5], [0.2, 0.3, 0.5]),
        ([1e308, 1e308, -1e308], [0.5, 0.5, 0]),
        ([5e-324, 5e-324, -5e-324], [0.5, 0.5, 0]),
    ],
)
def test_cover_clips_then_closes_without_changing_taxa_or_input(
    values: list[float], expected: list[float]
) -> None:
    from bijux_pollenomics_lra.reconstruction.composition import close_love_cover

    raw = np.array([[values]], dtype=float)
    original = raw.copy()
    result = close_love_cover(raw, np.array([True]))
    np.testing.assert_allclose(result[0, 0], expected, rtol=2e-15, atol=0)
    np.testing.assert_array_equal(raw, original)
    assert result.sum() == pytest.approx(1)


@pytest.mark.parametrize("values", [[0, 0], [-1, -2], [np.nan, 2], [np.inf, 2]])
def test_undefined_supported_cover_refuses_instead_of_inventing_mass(
    values: list[float],
) -> None:
    from bijux_pollenomics_lra.reconstruction.composition import close_love_cover

    with pytest.raises(ValidationError) as failure:
        close_love_cover(np.array([[values]], dtype=float), np.array([True]))
    assert failure.value.reason_code in {
        "nonfinite_love_cover",
        "zero_positive_love_cover",
    }


def test_draw_closure_preserves_missing_rings_and_precedes_aggregation() -> None:
    from bijux_pollenomics_lra.reconstruction.composition import close_love_cover

    raw = np.array([[[np.nan] * 3, [80, 30, -10]], [[np.nan] * 3, [10, 40, 50]]])
    result = close_love_cover(raw, np.array([False, True]))
    assert np.isnan(result[:, 0]).all()
    np.testing.assert_allclose(result[:, 1], [[8 / 11, 3 / 11, 0], [0.1, 0.4, 0.5]])
    np.testing.assert_allclose(result[:, 1].mean(axis=0), [91 / 220, 37 / 110, 0.25])


@pytest.mark.parametrize("retain", [False, True])
def test_actual_workflow_publishes_adjusted_cover_and_retains_source(
    retain: bool, tmp_path: Path
) -> None:
    local, regional, params, rings = load_love_example()
    config = LoveConfig(
        "analytical",
        "lake",
        300,
        12.9,
        10,
        repeats=4,
        stochastic=True,
        seed=17,
        retain_samples=retain,
    )
    result = run_love(local, regional, params["ppes"], rings, config)
    assert (result.cover["mean"].dropna().to_numpy() >= 0).all()
    np.testing.assert_allclose(result.cover["mean"].dropna().sum(axis=1), 1)
    assert (
        result.manifest.parameters["analytical_cover_policy"] == "clip-and-renormalize"
    )
    assert result.manifest.compatibility_mode == "analytical-love-clip-and-renormalize"
    source = run_love(
        local,
        regional,
        params["ppes"],
        rings,
        replace(config, analytical_cover_policy="source-raw", retain_samples=True),
    )
    assert (source.cover["mean"].to_numpy() < 0).any()
    pd.testing.assert_frame_equal(
        result.auxiliary["raw_cover_mean"], source.cover["mean"]
    )
    assert result.outlier is not None and source.outlier is not None
    pd.testing.assert_series_equal(result.outlier, source.outlier)
    raw = source.samples["cover"]
    valid = source.auxiliary["valid_ring"].to_numpy(dtype=bool)
    clipped = np.maximum(raw, 0)
    expected = clipped / clipped.sum(axis=2, keepdims=True)
    np.testing.assert_allclose(
        result.cover["mean"].loc[valid], expected[:, valid].mean(axis=0)
    )
    np.testing.assert_allclose(
        result.cover["q10"].loc[valid], np.quantile(expected[:, valid], 0.1, axis=0)
    )
    np.testing.assert_allclose(
        result.cover["sd"].loc[valid], np.std(expected[:, valid], axis=0, ddof=1)
    )
    assert bool(result.samples) == retain
    if retain:
        np.testing.assert_allclose(result.samples["cover"], expected, equal_nan=True)
        np.testing.assert_array_equal(result.samples["raw_cover"], raw)
    destination = result.write(tmp_path / "love")
    contract = json.loads((destination / "result_contract.json").read_text())
    assert contract["cover_is_not_clipped"] is False
    assert contract["analytical_cover_policy"] == "clip-and-renormalize"
    assert contract["raw_cover_is_not_clipped"] is True
    assert (destination / "aux_raw_cover_mean.csv").is_file()
    assert source.manifest.compatibility_mode == "disqover-0.9.14"


@pytest.mark.parametrize("kind", [LoveConfig, RegionalDrawLoveConfig])
def test_analytical_cover_policy_rejects_unknown_rules(kind: type) -> None:
    args = ("analytical", "lake", 300, 12.9, 10) if kind is LoveConfig else (12.9, 10)
    with pytest.raises(ValidationError, match="analytical_cover_policy"):
        kind(*args, analytical_cover_policy="absolute-values")
