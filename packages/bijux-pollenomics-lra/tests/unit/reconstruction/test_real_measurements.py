"""Public numerical consumers require real measurement inputs on every axis."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from bijux_pollenomics_lra.api import (
    ValidationError,
    fit_homogeneous_likelihood,
    forward_deposition,
)
from bijux_pollenomics_lra.reconstruction.likelihood.multisite_likelihood import (
    fit_multisite_likelihood,
)


def _complex(value: object, kind: str) -> np.ndarray:
    if kind == "native":
        result = np.array(value, dtype=np.complex128)
        result.flat[0] += 2j
        return result
    if kind == "extended_native":
        result = np.array(value, dtype=np.clongdouble)
        result.flat[0] += 2j
        return result
    result = np.array(value, dtype=object)
    scalar = {
        "object_python": complex,
        "object_numpy": np.complex128,
        "object_extended": np.clongdouble,
    }[kind]
    result.flat[0] = scalar(result.flat[0]) + scalar(2j)
    return result


@pytest.mark.parametrize(
    "kind",
    ["native", "extended_native", "object_python", "object_numpy", "object_extended"],
)
@pytest.mark.parametrize(
    "field",
    ["local_cover", "regional_deposition", "local_k", "terrestrial_fraction", "ppe"],
)
def test_forward_refuses_complex_measurements_on_each_input(
    field: str, kind: str
) -> None:
    inputs: dict[str, object] = {
        "local_cover": [0.25, 0.75],
        "regional_deposition": [0.5, 1.0],
        "local_k": [[2.0, 3.0], [4.0, 2.0]],
        "terrestrial_fraction": [1.0, 0.5],
        "ppe": [2.0, 1.0],
    }
    inputs[field] = _complex(inputs[field], kind)
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        with pytest.raises(ValidationError, match="complex measurements"):
            forward_deposition(**inputs)
    assert observed == []


@pytest.mark.parametrize(
    "kind",
    ["native", "extended_native", "object_python", "object_numpy", "object_extended"],
)
@pytest.mark.parametrize(
    "field", ["observed_weights", "local_coefficients", "regional_deposition"]
)
def test_homogeneous_fit_refuses_complex_measurements_on_each_input(
    field: str, kind: str
) -> None:
    inputs: dict[str, object] = {
        "observed_weights": [25, 75],
        "local_coefficients": [2.0, 3.0],
        "regional_deposition": [0.5, 1.0],
    }
    inputs[field] = _complex(inputs[field], kind)
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        with pytest.raises(ValidationError, match="complex measurements"):
            fit_homogeneous_likelihood(
                inputs["observed_weights"],
                inputs["local_coefficients"],
                inputs["regional_deposition"],
            )
    assert observed == []


@pytest.mark.parametrize("scalar", [np.complex128, np.clongdouble])
@pytest.mark.parametrize("control", ["score_tolerance", "relative_count_tolerance"])
def test_multisite_scalar_complex_guard_is_preserved(
    scalar: type, control: str
) -> None:
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        with pytest.raises(ValidationError, match="complex measurements"):
            fit_multisite_likelihood(
                [[25, 75]],
                [[2, 3]],
                taxon_measured=np.ones((1, 2), dtype=bool),
                **{control: scalar(1e-7 + 1j)},
            )
    assert observed == []
