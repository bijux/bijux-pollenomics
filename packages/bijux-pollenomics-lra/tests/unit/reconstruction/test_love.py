from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.models.configuration import LoveConfig
from bijux_pollenomics_lra.models.errors import NativeOptimizerWarning, ValidationError
from bijux_pollenomics_lra.models.regional_draw_source import RegionalCoverDrawSource
from bijux_pollenomics_lra.models.validation import (
    LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
    normalise_parameters,
)
from bijux_pollenomics_lra.optimization.solver import ReplayOptimizer
from bijux_pollenomics_lra.provenance.identity import sha256_object
from bijux_pollenomics_lra.reconstruction.analytical import LOVEr, lov
from bijux_pollenomics_lra.reconstruction.optimized import (
    LOVEoptim,
    calK,
    logeuclidean,
    love_pollen,
    tf,
)
from bijux_pollenomics_lra.resources.examples import load_love_example
from bijux_pollenomics_lra.workflows.local import (
    run_love,
    run_love_from_regional_draws,
)


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


def test_named_landclim_gpm_analytical_profile_keeps_source_fall_speed() -> None:
    local, regional, params, rings = _love_inputs()
    # These rings begin beyond the local basin diameter, so source GPM Kloc is
    # positive; earlier source-example rings can produce negative Kloc.
    supported_rings = rings.iloc[8:11].copy(deep=True)
    low = params.copy(deep=True)
    low.loc[low.index[0], "fallspeed"] = 0.006
    with pytest.raises(ValidationError, match="between 0.01 and 0.15"):
        normalise_parameters(low)
    config = LoveConfig(
        "analytical",
        "lake",
        300,
        12.9,
        3,
        distance_weighting="gpm neutral",
        fall_speed_profile=LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
        repeats=1,
        stochastic=False,
    )
    regional_draws = np.full((1, 10), 0.1)
    with pytest.raises(ValidationError, match="requires supplied regional_cover_draws"):
        run_love(local, regional, low, supported_rings, config)
    result = run_love(
        local,
        regional,
        low,
        supported_rings,
        config,
        regional_cover_draws=regional_draws,
    )
    reference = run_love(
        local,
        regional,
        params,
        supported_rings,
        config,
        regional_cover_draws=regional_draws,
    )
    assert result.manifest.parameters["fall_speed_profile"] == (
        LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE
    )
    assert result.manifest.parameters["distance_weighting"] == "gpm neutral"
    assert result.manifest.parameters["paired_regional_cover_draws"] is True
    assert np.isfinite(result.auxiliary["Kreg"].to_numpy()).all()
    assert (result.auxiliary["Kreg"].to_numpy() > 0).all()
    assert not np.array_equal(
        result.auxiliary["Kreg"]["Alnus"],
        reference.auxiliary["Kreg"]["Alnus"],
    )
    assert low.loc[low.index[0], "fallspeed"] == 0.006
    with pytest.raises(ValidationError, match="deposition must be finite and positive"):
        run_love(
            local,
            regional,
            low,
            rings,
            LoveConfig(
                "analytical",
                "lake",
                300,
                12.9,
                10,
                distance_weighting="gpm neutral",
                fall_speed_profile=LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
                repeats=1,
                stochastic=False,
            ),
            regional_cover_draws=regional_draws,
        )


def test_draw_only_love_preserves_numerics_without_placeholder_pollen() -> None:
    local, regional, params, rings = _love_inputs()
    supported_rings = rings.iloc[8:11].copy(deep=True)
    draws = np.full((2, 10), 0.1)
    source = RegionalCoverDrawSource(
        values=draws,
        taxon_ids=tuple(local.columns[1:]),
        bin_id="bin-50",
        younger_bp=1250,
        older_bp=1750,
        draw_ids=(0, 1),
        regional_site_ids=("site-a", "site-b"),
        eligible_site_ids=("site-a", "site-b"),
        parent_manifest_sha256="a" * 64,
        draw_member_sha256="b" * 64,
        selected_tensor_sha256=sha256_object(draws),
        diagnostic_prefix=True,
    )
    config = LoveConfig(
        "analytical",
        "lake",
        300,
        12.9,
        3,
        distance_weighting="gpm neutral",
        fall_speed_profile=LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
        repeats=2,
        stochastic=False,
        retain_samples=True,
    )
    historical = run_love(
        local,
        regional,
        params,
        supported_rings,
        config,
        regional_cover_draws=draws,
    )
    draw_only = run_love_from_regional_draws(
        local,
        source,
        params,
        supported_rings,
        config,
        local_site_id="site-a",
        local_sample_id="sample-a",
    )
    np.testing.assert_array_equal(
        draw_only.samples["cover"], historical.samples["cover"]
    )
    np.testing.assert_array_equal(
        draw_only.auxiliary["Kreg"].to_numpy(),
        historical.auxiliary["Kreg"].to_numpy(),
    )
    assert "regional_pollen" not in draw_only.manifest.inputs
    assert draw_only.manifest.inputs["regional_cover_draws"] == sha256_object(draws)
    assert (
        draw_only.manifest.parameters["regional_draw_source"]["draw_member_sha256"]
        == "b" * 64
    )
    assert draw_only.manifest.parameters["regional_cohort_overlap"] is True
    assert source.values.flags.writeable is False
    with pytest.raises(ValueError):
        source.values.flags.writeable = True
    draws[0, 0] = 0.9
    assert source.values[0, 0] == 0.1
    regional.iloc[0, 1:] = regional.iloc[0, 1:] + 1
    changed_placeholder = run_love(
        local,
        regional,
        params,
        supported_rings,
        config,
        regional_cover_draws=source.values,
    )
    np.testing.assert_array_equal(
        draw_only.samples["cover"], changed_placeholder.samples["cover"]
    )
    assert (
        historical.manifest.inputs["regional_pollen"]
        != changed_placeholder.manifest.inputs["regional_pollen"]
    )
    with pytest.raises(ValidationError, match="Regional pollen is required"):
        run_love(
            local, None, params, supported_rings, config, regional_cover_draws=draws
        )
    with pytest.raises(ValidationError, match="Draw-only LOVE requires"):
        run_love(
            local,
            None,
            params,
            supported_rings,
            config,
            regional_cover_draws=source.values,
            _draw_source=source,
        )
    with pytest.raises(ValidationError, match="Regional pollen is required"):
        LOVEr(
            local,
            None,
            {
                "ppes": params,
                "fall_speed_profile": LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
            },
            supported_rings,
            3,
            repeats=2,
            regional_cover_draws=source.values,
        )
    with pytest.raises(ValidationError, match="PPE rows"):
        run_love_from_regional_draws(
            local,
            source,
            params.iloc[::-1],
            supported_rings,
            config,
            local_site_id="site-a",
            local_sample_id="sample-a",
        )
    with pytest.raises(ValidationError, match="repeat count"):
        run_love_from_regional_draws(
            local,
            source,
            params,
            supported_rings,
            LoveConfig(
                "analytical",
                "lake",
                300,
                12.9,
                3,
                distance_weighting="gpm neutral",
                fall_speed_profile=LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
                repeats=3,
                stochastic=False,
            ),
            local_site_id="site-a",
            local_sample_id="sample-a",
        )


def test_regional_draw_source_refuses_invalid_counts_axes_and_digests() -> None:
    draws = np.full((2, 2), 0.5)
    values = dict(
        values=draws,
        taxon_ids=("A", "B"),
        bin_id="bin-50",
        younger_bp=1250,
        older_bp=1750,
        draw_ids=(0, 1),
        regional_site_ids=("one", "two"),
        eligible_site_ids=("one", "two"),
        parent_manifest_sha256="a" * 64,
        draw_member_sha256="b" * 64,
        selected_tensor_sha256=sha256_object(draws),
        diagnostic_prefix=True,
    )
    for change in (
        {"draw_ids": (1, 0)},
        {"draw_ids": (False, True)},
        {"younger_bp": False},
        {"younger_bp": "invalid"},
        {"taxon_ids": ("A", "A")},
        {"eligible_site_ids": ("two", "one")},
        {"selected_tensor_sha256": "0" * 64},
        {"draw_member_sha256": "invalid"},
        {"values": np.full((2, 2), 0.25)},
        {"values": np.array([[0.5, np.nan], [0.5, 0.5]])},
        {"diagnostic_prefix": False},
    ):
        with pytest.raises(ValidationError):
            RegionalCoverDrawSource(**(values | change))


def test_draw_only_publication_profile_uses_all_1000_draws(tmp_path) -> None:
    local, _, params, rings = _love_inputs()
    draws = np.full((1000, 10), 0.1)
    common = dict(
        values=draws,
        taxon_ids=tuple(local.columns[1:]),
        bin_id="bin-50",
        younger_bp=1250,
        older_bp=1750,
        draw_ids=tuple(range(1000)),
        regional_site_ids=("site-a", "site-b"),
        eligible_site_ids=("site-a", "site-b"),
        parent_manifest_sha256="a" * 64,
        draw_member_sha256="b" * 64,
        selected_tensor_sha256=sha256_object(draws),
    )
    with pytest.raises(ValidationError, match="exactly 1000"):
        RegionalCoverDrawSource(
            **(common | {"values": draws[:-1], "draw_ids": tuple(range(999))})
        )
    source = RegionalCoverDrawSource(**common)
    config = LoveConfig(
        "analytical",
        "lake",
        300,
        12.9,
        3,
        distance_weighting="gpm neutral",
        fall_speed_profile=LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
        repeats=1000,
        stochastic=False,
        retain_samples=True,
    )
    result = run_love_from_regional_draws(
        local,
        source,
        params,
        rings.iloc[8:11],
        config,
        local_site_id="local-site",
        local_sample_id="local-sample",
    )
    assert result.samples["cover"].shape == (1000, 3, 10)
    assert (
        result.manifest.parameters["regional_draw_source"]["diagnostic_prefix"] is False
    )
    assert "regional_pollen" not in result.manifest.inputs
    bundle = result.write(tmp_path / "draw-only")
    assert (bundle / "run_manifest.json").is_file()


def test_named_landclim_profile_refuses_outside_range_or_wrong_method() -> None:
    profile = LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE
    local, regional, params, rings = _love_inputs()
    for method, weighting in (
        ("optimized", "gpm neutral"),
        ("analytical", "lsm unstable"),
        ("analytical", "gpm unstable"),
    ):
        with pytest.raises(ValidationError, match="LandClim II"):
            LoveConfig(
                method,
                "lake",
                300,
                12.9,
                10,
                distance_weighting=weighting,
                fall_speed_profile=profile,
            )
    for fall_speed in (0.005999, 0.150001):
        invalid = params.copy(deep=True)
        invalid.loc[invalid.index[0], "fallspeed"] = fall_speed
        config = LoveConfig(
            "analytical",
            "lake",
            300,
            12.9,
            10,
            distance_weighting="gpm neutral",
            fall_speed_profile=profile,
            repeats=1,
            stochastic=False,
        )
        with pytest.raises(ValidationError, match="between 0.006 and 0.15"):
            run_love(local, regional, invalid, rings, config)


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
