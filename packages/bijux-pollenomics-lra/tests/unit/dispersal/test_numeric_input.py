"""Real-valued dispersal inputs must not lose unresolved source information."""

from collections.abc import Callable
from typing import Any, cast

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.dispersal.kernels import (
    DispersalFactorK,
    dispersal_factor,
    gpm_values,
)
from bijux_pollenomics_lra.models.errors import ValidationError


@pytest.mark.parametrize(
    "value",
    [
        np.ma.array([100.0], mask=[True]),
        np.array([100.0 + 7j]),
        np.array([100.0 + 7j], dtype=object),
        pd.Series([100.0 + 7j]),
        [100.0 + 7j],
        [100.0, True],
    ],
)
def test_gpm_rejects_unresolved_or_nonreal_distances(value: object) -> None:
    with pytest.raises(ValidationError):
        gpm_values(value, 0.03, 0.12, 0.25, 3)


@pytest.mark.parametrize(
    "value",
    [
        np.ma.array([100.0], mask=[True]),
        np.array([100.0 + 7j]),
        np.array([100.0 + 7j], dtype=object),
        pd.Series([100.0 + 7j]),
        [100.0 + 7j],
        [100.0, True],
    ],
)
@pytest.mark.parametrize("function", [dispersal_factor, DispersalFactorK])
def test_dispersal_rejects_unresolved_or_nonreal_basin_diameters(
    value: object, function: Callable[..., Any]
) -> None:
    with pytest.raises(ValidationError):
        function(0.03, "peatland", value, "gpm neutral", 100_000)


def test_valid_distance_shapes_and_basin_alias_remain_equal() -> None:
    distances = np.array([[0.0, 100.0], [200.0, 300.0]])
    result = gpm_values(distances, 0.03, 0.12, 0.25, 3)
    assert isinstance(result, np.ndarray) and result.shape == distances.shape
    np.testing.assert_array_equal(
        result, gpm_values(distances.tolist(), 0.03, 0.12, 0.25, 3)
    )
    assert isinstance(gpm_values(100.0, 0.03, 0.12, 0.25, 3), float)
    diameters = [[100.0, 200.0], [300.0, 400.0]]
    normal = dispersal_factor(
        0.03, "peatland", cast(Any, diameters), "gpm neutral", 100_000
    )
    alias = DispersalFactorK(
        0.03, "peatland", np.array(diameters), "gpm neutral", 100_000
    )
    assert isinstance(normal, np.ndarray) and normal.shape == (2, 2)
    np.testing.assert_array_equal(normal, alias)
    assert isinstance(
        dispersal_factor(0.03, "peatland", 100.0, "gpm neutral", 100_000), float
    )


@pytest.mark.parametrize("value", [-1.0, np.nan, np.inf])
def test_invalid_real_distances_and_diameters_still_refuse(value: float) -> None:
    with pytest.raises(ValidationError):
        gpm_values(value, 0.03, 0.12, 0.25, 3)
    with pytest.raises(ValidationError):
        dispersal_factor(0.03, "peatland", value, "gpm neutral", 100_000)


def test_fully_unmasked_values_remain_supported() -> None:
    values = np.ma.array([100.0, 200.0], mask=[False, False])
    np.testing.assert_array_equal(
        gpm_values(values, 0.03, 0.12, 0.25, 3),
        gpm_values([100.0, 200.0], 0.03, 0.12, 0.25, 3),
    )
    np.testing.assert_array_equal(
        dispersal_factor(0.03, "peatland", values, "gpm neutral", 100_000),
        dispersal_factor(
            0.03, "peatland", cast(Any, [100.0, 200.0]), "gpm neutral", 100_000
        ),
    )


@pytest.mark.parametrize("position", range(4))
@pytest.mark.parametrize("value", [np.complex128(0.03 + 1j), True, np.ma.masked])
def test_gpm_rejects_nonreal_masked_or_boolean_parameters(
    position: int, value: object
) -> None:
    parameters: list[Any] = [0.03, 0.12, 0.25, 3.0]
    parameters[position] = value
    with pytest.raises(ValidationError):
        gpm_values(100.0, *parameters)


@pytest.mark.parametrize("position", range(4))
@pytest.mark.parametrize("value", [0.0, -1.0, np.nan, np.inf])
def test_gpm_parameters_remain_positive_and_finite(position: int, value: float) -> None:
    parameters: list[Any] = [0.03, 0.12, 0.25, 3.0]
    parameters[position] = value
    with pytest.raises(ValidationError):
        gpm_values(100.0, *parameters)


def test_gpm_accepts_numpy_real_parameters() -> None:
    parameters = [np.float64(0.03), np.float64(0.12), np.float64(0.25), np.float64(3)]
    np.testing.assert_array_equal(
        gpm_values([0.0, 100.0], *parameters),
        gpm_values([0.0, 100.0], *(float(p) for p in parameters)),
    )


def test_gpm_scalar_parameter_normalization_is_explicit() -> None:
    expected = gpm_values(100.0, 0.03, 0.12, 0.25, 3.0)
    singleton = gpm_values(100.0, cast(Any, np.array([0.03])), 0.12, 0.25, 3.0)
    numeric_text = gpm_values(100.0, cast(Any, "0.03"), 0.12, 0.25, 3.0)
    assert isinstance(singleton, float)
    assert singleton == expected == numeric_text
