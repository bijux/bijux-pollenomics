from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.models.configuration import LoveConfig
from bijux_pollenomics_lra.models.errors import NativeOptimizerWarning, ValidationError
from bijux_pollenomics_lra.optimization.solver import ReplayOptimizer
from bijux_pollenomics_lra.reconstruction.analytical import LOVEr, lov
from bijux_pollenomics_lra.reconstruction.optimized import (
    LOVEoptim,
    calK,
    logeuclidean,
    love_pollen,
    tf,
)
from bijux_pollenomics_lra.resources.examples import load_love_example
from bijux_pollenomics_lra.workflows.local import run_love


def _love_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    local, regional, params, rings = load_love_example()
    return local, regional, params["ppes"], rings


def _source_params() -> tuple[
    pd.DataFrame, pd.DataFrame, dict[str, object], pd.DataFrame
]:
    local, regional, params, rings = load_love_example()
    params = dict(params)
    params["error"] = False
    return local, regional, params, rings


def test_lov_is_unbounded_and_matches_equation() -> None:
    params = {
        "ppes": pd.DataFrame(
            {
                "Taxon": ["A", "B"],
                "fallspeed": [0.02, 0.04],
                "ppe": [1.0, 2.0],
                "ppe.error": [0, 0],
            }
        ),
        "error": False,
    }
    sample = pd.DataFrame({"age": [1], "A": [10], "B": [90]})
    result = lov(sample, [2, 0], params, stochastic=False)
    np.testing.assert_allclose(result, [(10 / 55) * 3 - 2, (45 / 55) * 3])
    assert result[0] < 0


def test_forward_model_and_objective() -> None:
    local_k = np.array([[0.2, 0.3], [0.1, 0.4]])
    local_fraction = np.array([0.5, 1.0])
    cover = np.array([0.4, 0.6])
    regional = np.array([0.2, 0.2])
    ppe = np.array([1, 2])
    observed = np.array([0.3, 0.7])
    modeled = love_pollen(cover, regional, local_k, local_fraction, ppe)
    assert modeled.sum() == pytest.approx(1)
    expected = np.sqrt(np.sum((np.log(modeled) - np.log(observed + 0.001)) ** 2))
    assert tf(cover, regional, local_k, local_fraction, observed, ppe) == pytest.approx(
        expected
    )
    assert logeuclidean([1, 2], [2, 4]) == pytest.approx(np.sqrt(2 * np.log(2) ** 2))


def test_calk_shape_and_finiteness() -> None:
    _, _, params, rings = _source_params()
    matrix = calK(rings.head(10), params)
    assert matrix.shape == (10, 10)
    assert np.isfinite(matrix.to_numpy()).all()


def test_full_analytical_workflow() -> None:
    local, regional, params, rings = _source_params()
    result = LOVEr(
        local,
        regional,
        params,
        rings,
        10,
        repeats=2,
        stochastic=False,
        return_samples=True,
    )
    assert result["Mean"].shape == (10, 10)
    assert result["Mean"].iloc[:7].isna().all().all()
    np.testing.assert_allclose(result["Mean"].iloc[7:].sum(axis=1), 1, atol=1e-12)
    assert result["samples"].shape == (2, 10, 10)
    assert result["Kreg"].shape == result["Kloc"].shape == (10, 10)


def test_analytical_supplied_draw_shape_is_validated() -> None:
    local, regional, params, rings = _source_params()
    with pytest.raises(ValidationError):
        LOVEr(
            local,
            regional,
            params,
            rings,
            10,
            repeats=2,
            local_count_draws=np.ones((2, 9, 10)),
        )


def test_optimized_candidate_replay() -> None:
    local, regional, params, rings = _source_params()
    candidates = np.array([np.full(10, 0.5), np.linspace(0.1, 0.9, 10)])
    with pytest.warns(UserWarning, match="Terrestrial"):
        result = LOVEoptim(
            local,
            regional,
            params,
            rings,
            10,
            repeats=2,
            stochastic=False,
            optimizer=ReplayOptimizer(candidates),
            return_samples=True,
        )
    np.testing.assert_allclose(
        result["cover"]["mean"].dropna().sum(axis=1), 1, atol=1e-12
    )
    assert result["mBestValue"].dropna().shape[0] > 0
    assert len(result["optimizers"]) == int(
        result["mBestValue"].notna().to_numpy().sum()
    )
    assert result["cover_samples"].shape == (2, 10, 10)
    assert result["pollen_samples"].shape == (2, 10, 10)


@pytest.mark.slow
def test_native_optimizer_executes_with_small_budget() -> None:
    local, regional, params, rings = _source_params()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = LOVEoptim(
            local,
            regional,
            params,
            rings,
            9,
            repeats=1,
            stochastic=False,
            itermax=2,
            max_evaluations=60,
            rng=3,
        )
    assert np.isfinite(result["mBestValue"].dropna().to_numpy()).all()
    assert all(diagnostic.nfev <= 60 for diagnostic in result["optimizers"])
    assert not any(isinstance(item.message, NativeOptimizerWarning) for item in caught)


def test_typed_analytical_and_optimized_results(tmp_path) -> None:
    local, regional, params, rings = _love_inputs()
    analytical = run_love(
        local,
        regional,
        params,
        rings,
        LoveConfig(
            "analytical",
            "lake",
            300,
            12.9,
            10,
            repeats=2,
            stochastic=False,
            retain_samples=True,
        ),
    )
    assert analytical.method == "analytical"
    assert set(analytical.cover) == {"mean", "q10", "q90", "sd"}
    assert "cover" in analytical.samples
    analytical.write(tmp_path / "analytical")
    assert (tmp_path / "analytical" / "cover_mean.csv").is_file()

    candidates = np.array([np.full(10, 0.5), np.linspace(0.1, 0.9, 10)])
    with pytest.warns(UserWarning, match="Terrestrial"):
        optimized = run_love(
            local,
            regional,
            params,
            rings,
            LoveConfig(
                "optimized",
                "lake",
                300,
                12.9,
                10,
                repeats=2,
                stochastic=False,
                retain_samples=True,
            ),
            replay_candidates=candidates,
        )
    assert optimized.method == "optimized"
    assert set(optimized.pollen_percentages) == {"mean", "q10", "q90"}
    assert optimized.diagnostics
    optimized.write(tmp_path / "optimized")
    assert (tmp_path / "optimized" / "optimizer_diagnostics.json").is_file()


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "method": "unknown",
            "regional_basin_type": "lake",
            "regional_basin_diameter_m": 300,
            "local_basin_diameter_m": 10,
            "max_ring": 10,
        },
        {
            "method": "analytical",
            "regional_basin_type": "lake",
            "regional_basin_diameter_m": 300,
            "local_basin_diameter_m": 0,
            "max_ring": 10,
        },
        {
            "method": "analytical",
            "regional_basin_type": "lake",
            "regional_basin_diameter_m": 300,
            "local_basin_diameter_m": 10,
            "max_ring": 0,
        },
        {
            "method": "analytical",
            "regional_basin_type": "lake",
            "regional_basin_diameter_m": 300,
            "local_basin_diameter_m": 10,
            "max_ring": 10,
            "ppe_error": "yes",
        },
    ],
)
def test_love_config_validation(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        LoveConfig(**kwargs)  # type: ignore[arg-type]
