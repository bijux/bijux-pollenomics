"""Generated paired extents preserve historical equations and explicit supports."""

from __future__ import annotations

from dataclasses import replace
import math

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.api import (
    LoveConfig,
    LRAConfig,
    RevealsConfig,
    run_lra,
    run_reveals,
)
from bijux_pollenomics_lra.models.errors import ValidationError


def _inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pollen = pd.DataFrame([[3000, 100, 100]], columns=["age", "A", "B"])
    params = pd.DataFrame(
        {
            "species": ["A", "B"],
            "fallspeed": [0.01, 0.15],
            "ppe": [1.0, 1.0],
            "ppe.error": [0.0, 0.0],
        }
    )
    rings = pd.DataFrame({"inner": [11.0], "outer": [500.0], "mean": [255.5]})
    return pollen, params, rings


def _configuration(
    cutoff: float = 100_000, *, method: str = "analytical", coupled: bool = True
) -> LRAConfig:
    return LRAConfig(
        RevealsConfig(
            "peatland",
            100,
            distance_weighting="gpm neutral",
            iterations=1,
            region_cutoff_m=cutoff,
            stochastic=False,
        ),
        LoveConfig(
            method,
            "peatland",
            100,
            20,
            1,
            distance_weighting="gpm neutral",
            repeats=1,
            stochastic=False,
            analytical_cover_policy="source-raw",
            optimized_profile="ring-taxon-preserving"
            if method == "optimized"
            else "disqover-0.9.14-source",
        ),
        seed=1,
        couple_regional_draws=coupled,
    )


def _airborne(distance: float, speed: float) -> float:
    # Independent scalar neutral-GPM expression; no engine kernel/LOVE helper.
    return math.exp(
        -4 * speed * distance**0.125 / (0.25 * 3 * math.sqrt(math.pi) * 0.12)
    )


def _reference(cutoff: float) -> tuple[np.ndarray, np.ndarray]:
    speeds = (0.01, 0.15)
    deposition = np.array([_airborne(100, s) - _airborne(cutoff, s) for s in speeds])
    weights = np.array([100.0, 100.0]) / deposition
    regional = np.round(100 * weights / weights.sum(), 3) / 100
    kreg = np.array([_airborne(500, s) - _airborne(100_000, s) for s in speeds])
    kloc = np.array([_airborne(20, s) - _airborne(500, s) for s in speeds])
    correction = regional * kreg / np.sum(regional * kloc)
    local = np.array([0.5, 0.5]) * (1 + correction.sum()) - correction
    return regional * 100, local


@pytest.mark.parametrize("coupled", [False, True])
def test_generated_historical_control_matches_independent_equations(
    coupled: bool,
) -> None:
    pollen, params, rings = _inputs()
    result = run_lra(pollen, pollen, params, rings, _configuration(coupled=coupled))
    regional, local = _reference(100_000)
    np.testing.assert_allclose(
        result.regional.table.filter(regex=r"\.mean$").iloc[0],
        regional,
        rtol=0,
        atol=1e-10,
    )
    np.testing.assert_allclose(
        result.local.cover["mean"].iloc[0], local, rtol=0, atol=1e-10
    )
    np.testing.assert_allclose(
        local, [0.4200606038485031, 0.5799393961514969], rtol=0, atol=1e-14
    )
    assert result.local.manifest.parameters["analytical_cover_policy"] == "source-raw"


@pytest.mark.parametrize(
    "method,coupled",
    [("analytical", False), ("analytical", True), ("optimized", False)],
)
@pytest.mark.parametrize("cutoff", [50_000, 200_000])
def test_fixed_background_extent_is_refused_before_computation(
    method: str, coupled: bool, cutoff: float
) -> None:
    with pytest.raises(ValidationError, match="100000") as error:
        _configuration(cutoff, method=method, coupled=coupled)
    assert error.value.reason_code == "incompatible_regional_extent"


def test_standalone_reveals_nondefault_cutoff_remains_supported() -> None:
    pollen, params, _ = _inputs()
    config = replace(_configuration().reveals, region_cutoff_m=50_000)
    result = run_reveals(pollen, params, config)
    np.testing.assert_allclose(
        result.table.filter(regex=r"\.mean$").iloc[0],
        _reference(50_000)[0],
        rtol=0,
        atol=1e-10,
    )
    assert result.manifest.parameters["region_cutoff_m"] == 50_000


@pytest.mark.parametrize("coupled", [False, True])
def test_analytical_manifests_publish_effective_extent(coupled: bool) -> None:
    pollen, params, rings = _inputs()
    result = run_lra(pollen, pollen, params, rings, _configuration(coupled=coupled))
    expected = {
        "reveals_cutoff_m": 100_000,
        "love_background_cutoff_m": 100_000,
        "love_background_source": "paired-reveals-draws"
        if coupled
        else "internal-reveals",
        "love_deposition_support": {
            "kind": "historical-analytical",
            "cutoff_m": 100_000,
        },
    }
    assert result.manifest.parameters["effective_regional_extent"] == expected
    assert result.local.manifest.parameters["effective_regional_extent"] == expected


@pytest.mark.parametrize(
    "cutoff,coupled",
    [(50_000, True), (100_000, True), (200_000, True), (100_000, False)],
)
def test_optimized_preserves_ring_defined_support(cutoff: float, coupled: bool) -> None:
    pollen, params, _ = _inputs()
    rings = pd.DataFrame(
        {
            "inner": [11.0, 500.0, 1000.0],
            "outer": [500.0, 1000.0, 4000.0],
            "mean": [255.5, 750.0, 2500.0],
            "ring": [1.0, 1.0, 1.0],
            "terrestrial": [1.0, 1.0, 1.0],
        }
    )
    candidates = np.array([[0.2, 0.8], [0.5, 0.5], [0.8, 0.2]])
    result = run_lra(
        pollen,
        pollen,
        params,
        rings,
        _configuration(cutoff, method="optimized", coupled=coupled),
        replay_candidates=candidates,
    )
    regional = _reference(cutoff)[0] / 100
    speeds = (0.01, 0.15)
    kernels = np.array(
        [
            [_airborne(2 * inner, speed) - _airborne(outer, speed) for speed in speeds]
            for inner, outer in zip(rings["inner"], rings["outer"], strict=True)
        ]
    )
    regional_deposition = (kernels[1:] * regional).sum(axis=0)
    predicted = candidates * kernels[0] + regional_deposition
    predicted /= predicted.sum(axis=1, keepdims=True)
    objective = np.linalg.norm(
        np.log(predicted) - np.log(np.array([0.5, 0.5]) + 0.001), axis=1
    )
    np.testing.assert_allclose(
        result.local.cover["mean"].iloc[0],
        candidates[objective.argmin()],
        rtol=0,
        atol=1e-10,
    )
    np.testing.assert_allclose(result.local.auxiliary["K"], kernels, rtol=0, atol=1e-14)
    winner = objective.argmin()
    assert result.local.objective_values is not None
    np.testing.assert_allclose(
        result.local.objective_values.to_numpy(dtype=float)[0, 0],
        objective[winner],
        rtol=0,
        atol=1e-12,
    )
    assert result.local.pollen_percentages is not None
    np.testing.assert_allclose(
        result.local.pollen_percentages["mean"].iloc[0],
        np.round(100 * predicted[winner], 2),
        rtol=0,
        atol=1e-12,
    )
    support = result.manifest.parameters["effective_regional_extent"]
    assert support["love_background_cutoff_m"] == cutoff
    assert support["love_deposition_support"] == {
        "kind": "supplied-rings",
        "local_ring_count": 1,
        "rings": [
            {"inner_m": i, "outer_m": o}
            for i, o in zip(rings["inner"], rings["outer"], strict=True)
        ],
    }


@pytest.mark.parametrize("cutoff", [50_000, 100_000])
def test_coupled_source_optimizer_keeps_its_supported_ring_domain(
    cutoff: float,
) -> None:
    pollen, params, _ = _inputs()
    rings = pd.DataFrame(
        {
            "inner": [11.0, 100.0, 500.0, 1000.0],
            "outer": [100.0, 500.0, 1000.0, 4000.0],
            "mean": [55.5, 300.0, 750.0, 2500.0],
            "ring": [1.0] * 4,
            "terrestrial": [0.0, 1.0, 1.0, 1.0],
        }
    )
    config = _configuration(cutoff, method="optimized")
    config = replace(
        config,
        love=replace(
            config.love, max_ring=2, optimized_profile="disqover-0.9.14-source"
        ),
    )
    result = run_lra(
        pollen, pollen, params, rings, config, replay_candidates=np.array([[0.2, 0.8]])
    )
    assert result.local.cover["mean"].iloc[0].isna().all()
    np.testing.assert_allclose(result.local.cover["mean"].iloc[1], [0.2, 0.8])
    assert (
        result.manifest.parameters["effective_regional_extent"][
            "love_background_cutoff_m"
        ]
        == cutoff
    )
    assert (
        result.local.manifest.parameters["optimized_profile"]
        == "disqover-0.9.14-source"
    )
