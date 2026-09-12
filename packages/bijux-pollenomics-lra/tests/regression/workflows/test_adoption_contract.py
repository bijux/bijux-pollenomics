"""Counterexamples found while adopting the supplied reference implementation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.api import (
    LoveConfig,
    LRAConfig,
    RevealsConfig,
    ValidationError,
    run_love,
    run_lra_series,
    run_reveals,
)
from bijux_pollenomics_lra.models.validation import normalise_parameters
from bijux_pollenomics_lra.provenance.identity import sha256_object
from bijux_pollenomics_lra.resources.examples import load_love_example


def _config() -> LRAConfig:
    return LRAConfig(
        RevealsConfig("lake", 300, iterations=2, stochastic=False),
        LoveConfig("analytical", "lake", 300, 12.9, 10, repeats=2, stochastic=False),
        seed=9,
    )


def test_series_preserves_adjacent_float_keys_and_duplicate_frame_indexes() -> None:
    local, regional, params, rings = load_love_example()
    coordinates = np.array([100.0, np.nextafter(100.0, np.inf)])
    local = pd.concat([local, local])
    regional = pd.concat([regional, regional])
    local.iloc[:, 0] = coordinates
    regional.iloc[:, 0] = coordinates[::-1]
    result = run_lra_series(local, regional, params["ppes"], rings, _config())
    assert len(result.runs) == 2
    assert [float(key) for key in result.runs] == coordinates.tolist()


@pytest.mark.parametrize(
    "coordinates",
    [[2**53, 2**53 + 1], [2**53 + 1], [-(2**53 + 1)]],
)
def test_series_refuses_integer_identity_loss_before_reconstruction(
    coordinates: list[int], monkeypatch: pytest.MonkeyPatch
) -> None:
    local, regional, params, rings = load_love_example()
    local = pd.concat([local] * len(coordinates), ignore_index=True)
    regional = pd.concat([regional] * len(coordinates), ignore_index=True)
    local[local.columns[0]] = coordinates
    regional[regional.columns[0]] = coordinates[::-1]
    original_local = local.copy(deep=True)
    original_regional = regional.copy(deep=True)

    def unexpected_reconstruction(*args: object, **kwargs: object) -> None:
        pytest.fail("Precision loss must be refused before model execution")

    monkeypatch.setattr(
        "bijux_pollenomics_lra.workflows.series.run_lra", unexpected_reconstruction
    )
    with pytest.raises(ValidationError) as caught:
        run_lra_series(local, regional, params["ppes"], rings, _config())
    assert caught.value.reason_code == "coordinate_precision_loss"
    pd.testing.assert_frame_equal(local, original_local)
    pd.testing.assert_frame_equal(regional, original_regional)


@pytest.mark.parametrize(
    "coordinates,reason",
    [
        ([2**53 + 1, 1.5], "coordinate_precision_loss"),
        ([1.5, -(2**53 + 1)], "coordinate_precision_loss"),
        (["100", "200"], "invalid_coordinate_type"),
        ([True, 1.5], "invalid_coordinate_type"),
    ],
)
def test_series_validates_original_object_scalars_before_coercion(
    coordinates: list[object], reason: str
) -> None:
    local, regional, params, rings = load_love_example()
    local = pd.concat([local, local], ignore_index=True)
    regional = pd.concat([regional, regional], ignore_index=True)
    local[local.columns[0]] = pd.Series(coordinates, dtype=object)
    regional[regional.columns[0]] = pd.Series(coordinates[::-1], dtype=object)
    with pytest.raises(ValidationError) as caught:
        run_lra_series(local, regional, params["ppes"], rings, _config())
    assert caught.value.reason_code == reason


def test_series_retains_exact_large_integer_coordinates() -> None:
    local, regional, params, rings = load_love_example()
    coordinates = [2**53, 2**53 + 2]
    local = pd.concat([local, local], ignore_index=True)
    regional = pd.concat([regional, regional], ignore_index=True)
    local[local.columns[0]] = coordinates
    regional[regional.columns[0]] = coordinates[::-1]
    result = run_lra_series(local, regional, params["ppes"], rings, _config())
    assert len(result.runs) == 2
    assert [int(key) for key in result.runs] == coordinates


@pytest.mark.parametrize("invalid", [np.nan, np.inf, -np.inf])
def test_series_rejects_nonfinite_pairing_coordinates(invalid: float) -> None:
    local, regional, params, rings = load_love_example()
    local.iloc[0, 0] = invalid
    regional.iloc[0, 0] = invalid
    with pytest.raises(ValidationError, match="finite"):
        run_lra_series(local, regional, params["ppes"], rings, _config())


def test_supplied_reveals_draws_are_part_of_provenance() -> None:
    _, regional, params, _ = load_love_example()
    draws = np.tile(params["ppes"]["ppe"].to_numpy(dtype=float), (1, 2, 1))
    result = run_reveals(regional, params["ppes"], _config().reveals, ppe_draws=draws)
    assert result.manifest.inputs["ppe_draws"] == sha256_object(draws)
    assert result.manifest.runtime["numerical_backend"] == "python-numpy-scipy"


def test_optimized_love_refuses_unused_supplied_ppe_draws() -> None:
    local, regional, params, rings = load_love_example()
    config = LoveConfig("optimized", "lake", 300, 12.9, 10, repeats=2, stochastic=False)
    with pytest.raises(ValidationError, match="does not consume local_ppe_draws"):
        run_love(
            local,
            regional,
            params["ppes"],
            rings,
            config,
            local_ppe_draws=np.ones((2, 10)),
        )


def test_parameter_normalization_cannot_create_ambiguous_columns() -> None:
    _, _, params, _ = load_love_example()
    table = params["ppes"].copy()
    table[" ppe "] = table["ppe"]
    with pytest.raises(ValidationError, match="duplicate normalized"):
        normalise_parameters(table)


def test_parent_identity_is_stable_across_execution_timestamps() -> None:
    from bijux_pollenomics_lra.api import run_lra

    local, regional, params, rings = load_love_example()
    first = run_lra(local, regional, params["ppes"], rings, _config())
    second = run_lra(local, regional, params["ppes"], rings, _config())
    assert first.manifest.generated_at_utc != second.manifest.generated_at_utc
    assert first.manifest.scientific_identity() == second.manifest.scientific_identity()


def test_failed_optimizer_is_refused_with_diagnostics() -> None:
    from bijux_pollenomics_lra.api import ConvergenceError

    local, regional, params, rings = load_love_example()
    config = LoveConfig(
        "optimized",
        "lake",
        300,
        12.9,
        10,
        repeats=1,
        stochastic=False,
        optimizer_max_evaluations=1,
    )
    with pytest.raises(ConvergenceError) as error:
        run_love(local, regional, params["ppes"], rings, config)
    assert error.value.reason_code == "optimizer_nonconvergence"
    assert error.value.diagnostics
    assert all(not result["success"] for result in error.value.diagnostics)


def test_public_love_does_not_guess_percentage_draw_units() -> None:
    local, regional, params, rings = load_love_example()
    with pytest.raises(ValidationError, match="fractions, not percentages"):
        run_love(
            local,
            regional,
            params["ppes"],
            rings,
            _config().love,
            regional_cover_draws=np.full((2, 10), 10.0),
        )


@pytest.mark.parametrize("method", ["analytical", "optimized"])
def test_wholly_unsupported_local_geometry_is_refused(method: str) -> None:
    local, regional, params, rings = load_love_example()
    config = LoveConfig(method, "lake", 300, 12.9, 2, repeats=1, stochastic=False)
    with pytest.raises(ValidationError) as error:
        run_love(local, regional, params["ppes"], rings, config)
    assert error.value.reason_code == "no_valid_local_rings"


@pytest.mark.parametrize(
    "column,value,reason",
    [
        ("inner", 0.5, "overlapping_rings"),
        ("mean", 5.0, "invalid_ring_mean"),
    ],
)
def test_invalid_ring_support_cannot_double_count_or_mislabel_geometry(
    column: str,
    value: float,
    reason: str,
) -> None:
    local, regional, params, rings = load_love_example()
    rings.iloc[1, rings.columns.get_loc(column)] = value
    with pytest.raises(ValidationError) as error:
        run_love(local, regional, params["ppes"], rings, _config().love)
    assert error.value.reason_code == reason


def test_fractional_regional_diameter_is_rejected_not_truncated() -> None:
    with pytest.raises(ValidationError, match="integer"):
        LoveConfig("analytical", "lake", 300.5, 12.9, 10)
