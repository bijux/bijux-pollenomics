"""Target-specific geometry and outcome-free preparation boundaries."""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.api import (
    ForwardConfig,
    ValidationError,
    forward_deposition,
    prepare_forward_inputs,
)


def _inputs(radius: float = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    params = pd.DataFrame(
        {
            "Taxon": ["Alnus", "Betula", "Pinus"],
            "fallspeed": [0.024, 0.035, 0.06],
            "ppe": [0.7, 2.2, 5.5],
            "ppe.error": [0.0, 0.0, 0.0],
        }
    )
    edges = np.array([radius, 3 * radius, 10 * radius, 50 * radius, 100000.0])
    area = np.pi * np.diff(edges**2)
    return params, pd.DataFrame(
        {
            "inner": edges[:-1],
            "outer": edges[1:],
            "mean": (edges[:-1] + edges[1:]) / 2,
            "ring": area,
            "terrestrial": area * np.array([1.0, 0.7, 0.9, 0.6]),
        }
    )


@pytest.mark.parametrize("count", [1, 2, 3])
def test_target_geometry_and_single_ring_axes(count: int) -> None:
    predictions = []
    for radius in [10.0, 40.0]:
        prepared = prepare_forward_inputs(
            *_inputs(radius), [0.6, 0.1, 0.3], ForwardConfig(count, 2 * radius)
        )
        result = forward_deposition(
            [0.2, 0.5, 0.3],
            prepared.regional_deposition,
            prepared.local_k,
            prepared.terrestrial_fraction,
            prepared.ppe,
        )
        assert prepared.local_k.shape == (count, 3)
        assert prepared.regional_deposition.shape == (3,)
        assert prepared.taxa == ("Alnus", "Betula", "Pinus")
        assert result.pollen_fraction.sum() == pytest.approx(1.0)
        assert prepared.method_profile == result.method_profile
        assert (
            prepared.preparation_profile
            == "disqover-0.9.14-corrected-matrix-homogeneous-v1"
        )
        predictions.append(result.pollen_fraction)
    assert not np.allclose(predictions[0], predictions[1])
    assert set(inspect.signature(prepare_forward_inputs).parameters) == {
        "params",
        "rings",
        "regional_cover",
        "config",
    }


def test_independent_immutable_arrays_and_no_random_state_use() -> None:
    params, rings = _inputs()
    cover = np.array([0.6, 0.1, 0.3])
    np.random.seed(17)
    expected = np.random.random(3)
    np.random.seed(17)
    prepared = prepare_forward_inputs(params, rings, cover, ForwardConfig(2, 20))
    np.testing.assert_array_equal(np.random.random(3), expected)
    before = prepared.ppe.copy()
    params.loc[:, "ppe"] = 100
    rings.loc[:, "terrestrial"] = 0
    cover[:] = 0
    np.testing.assert_array_equal(prepared.ppe, before)
    np.testing.assert_array_equal(prepared.regional_cover, [0.6, 0.1, 0.3])
    for array in [
        prepared.local_k,
        prepared.ppe,
        prepared.regional_cover,
        prepared.regional_deposition,
    ]:
        with pytest.raises(ValueError):
            array.setflags(write=True)


def test_rounded_regional_fractions_are_explicit_and_not_normalized() -> None:
    cover = np.array([0.33333, 0.33333, 0.33333])
    with pytest.raises(ValidationError):
        prepare_forward_inputs(*_inputs(), cover, ForwardConfig(2, 20))
    prepared = prepare_forward_inputs(
        *_inputs(),
        cover,
        ForwardConfig(2, 20, regional_cover_profile="disqover-rounded-fractions"),
    )
    np.testing.assert_array_equal(prepared.regional_cover, cover)
    assert prepared.regional_cover.sum() != 1.0


@pytest.mark.parametrize(
    "failure",
    [
        "overlap",
        "gap",
        "shore",
        "mean",
        "area",
        "land",
        "zero_local",
        "regional_absent",
        "cutoff",
        "nonfinite",
    ],
)
def test_invalid_geometry_refused(failure: str) -> None:
    params, rings = _inputs()
    config = ForwardConfig(2, 20)
    if failure == "overlap":
        rings.loc[1, "inner"] = 20
    elif failure == "gap":
        rings.loc[1, "inner"] = 40
    elif failure == "shore":
        config = ForwardConfig(2, 80)
    elif failure == "mean":
        rings.loc[0, "mean"] = 200
    elif failure == "area":
        rings.loc[0, "ring"] = 1
    elif failure == "land":
        rings.loc[0, "terrestrial"] = 2 * rings["ring"].to_numpy(dtype=float)[0]
    elif failure == "zero_local":
        rings.loc[:1, "terrestrial"] = 0
    elif failure == "regional_absent":
        config = ForwardConfig(4, 20)
    elif failure == "cutoff":
        rings.loc[3, "outer"] = 100001
    elif failure == "nonfinite":
        rings.loc[0, "inner"] = np.nan
    with pytest.raises(ValidationError):
        prepare_forward_inputs(params, rings, [0.6, 0.1, 0.3], config)


@pytest.mark.parametrize(
    "failure", ["duplicate", "blank", "zero_ppe", "speed", "sd", "boolean", "string"]
)
def test_invalid_parameters_refused(failure: str) -> None:
    params, rings = _inputs()
    if failure == "duplicate":
        params.loc[1, "Taxon"] = "Alnus"
    elif failure == "blank":
        params.loc[0, "Taxon"] = " "
    elif failure == "zero_ppe":
        params.loc[0, "ppe"] = 0
    elif failure == "speed":
        params.loc[0, "fallspeed"] = 0.5
    elif failure == "sd":
        params.loc[0, "ppe.error"] = -1
    else:
        params["ppe"] = params["ppe"].astype(object)
        params.loc[0, "ppe"] = True if failure == "boolean" else "0.7"
    with pytest.raises(ValidationError):
        prepare_forward_inputs(params, rings, [0.6, 0.1, 0.3], ForwardConfig(2, 20))


@pytest.mark.parametrize(
    "cover",
    [
        [60, 10, 30],
        [0.5, 0.5],
        [0.6, 0.1, -0.3],
        [0.6, np.nan, 0.3],
        [True, 0, 0],
        ["0.6", "0.1", "0.3"],
    ],
)
def test_regional_units_and_scalar_types_are_not_inferred(cover: object) -> None:
    with pytest.raises(ValidationError):
        prepare_forward_inputs(*_inputs(), cover, ForwardConfig(2, 20))


@pytest.mark.parametrize("method", ["gpm neutral", "gpm unstable"])
def test_narrow_gpm_negative_kernel_refused(method: str) -> None:
    params, _ = _inputs()
    edges = np.array([10.0, 15.0, 25.0, 100.0, 100000.0])
    area = np.pi * np.diff(edges**2)
    rings = pd.DataFrame(
        {
            "inner": edges[:-1],
            "outer": edges[1:],
            "mean": (edges[:-1] + edges[1:]) / 2,
            "ring": area,
            "terrestrial": area,
        }
    )
    with pytest.raises(ValidationError) as raised:
        prepare_forward_inputs(
            params,
            rings,
            [0.6, 0.1, 0.3],
            ForwardConfig(2, 20, distance_weighting=method),
        )
    assert raised.value.reason_code == "unsupported_forward_kernel_geometry"


def test_explicit_zero_regional_support() -> None:
    params, rings = _inputs()
    rings.loc[2:, "terrestrial"] = 0
    result = prepare_forward_inputs(
        params, rings, [0.6, 0.1, 0.3], ForwardConfig(2, 20)
    )
    np.testing.assert_array_equal(result.regional_deposition, np.zeros(3))
