"""Real numeric conversion refuses complex provenance before dropping information."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Any
import warnings

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.models.configuration import RevealsConfig
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import _float_array, matrix, vector


@pytest.mark.parametrize("scalar", [complex, np.complex128, np.clongdouble])
@pytest.mark.parametrize("imaginary", [0, 2])
@pytest.mark.parametrize("container", ["native", "object", "series", "frame"])
def test_complex_measurements_refuse_before_float_conversion(
    scalar: type, imaginary: int, container: str
) -> None:
    values = [scalar(1 + imaginary * 1j), scalar(2)]
    value: object = np.array(values, dtype=object if container == "object" else None)
    if container == "series":
        value = pd.Series(value)
    elif container == "frame":
        value = pd.DataFrame({"measurement": values})
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        with pytest.raises(ValidationError, match="complex measurements"):
            _float_array(value, "measurement")
    assert observed == []


@pytest.mark.parametrize(
    "values",
    [
        ["1.25", "2.5"],
        [Decimal("1.25"), Decimal("2.5")],
        [Fraction(5, 4), Fraction(5, 2)],
        np.array([1.25, 2.5], dtype=object),
        np.array([1.25, 2.5], dtype=np.float32),
    ],
)
def test_existing_real_numeric_coercion_is_preserved(values: object) -> None:
    np.testing.assert_array_equal(_float_array(values, "measurement"), [1.25, 2.5])


def test_readonly_real_view_and_unmasked_values_preserve_input_flags() -> None:
    original = np.array([1.25, 2.5])
    original.setflags(write=False)
    result = _float_array(original, "measurement")
    assert np.shares_memory(result, original)
    assert not result.flags.writeable and not original.flags.writeable
    unmasked = np.ma.array(original, mask=[False, False])
    np.testing.assert_array_equal(_float_array(unmasked, "measurement"), original)
    assert not unmasked.data.flags.writeable


@pytest.mark.parametrize(
    "value",
    [
        np.ma.array([1 + 2j, 2], mask=[True, False]),
        [np.ma.array([1 + 2j], mask=[True])],
    ],
)
def test_masked_missingness_is_refused_before_complex_conversion(value: object) -> None:
    with pytest.raises(ValidationError, match="masked"):
        _float_array(value, "measurement")


def test_existing_finite_sign_and_boolean_flags_stay_distinct() -> None:
    np.testing.assert_array_equal(
        vector([np.nan, np.inf, -1], "values", finite=False), [np.nan, np.inf, -1]
    )
    np.testing.assert_array_equal(matrix([[-1, 2]], "values", finite=False), [[-1, 2]])
    for value in ([True, 1], np.array([True], dtype=object)):
        with pytest.raises(ValidationError, match="booleans"):
            _float_array(value, "measurement")
    with pytest.raises(ValidationError, match="finite"):
        vector([np.inf], "values")
    with pytest.raises(ValidationError, match="negative"):
        vector([-1], "values", nonnegative=True)
    with pytest.raises(ValidationError, match="positive"):
        vector([0], "values", positive=True)


@pytest.mark.parametrize("scalar", [np.complex64, np.complex128, np.clongdouble])
@pytest.mark.parametrize("depth", [1, 3])
@pytest.mark.parametrize("imaginary", [0, 2])
def test_nested_complex_object_scalars_refuse_before_cast(
    scalar: type, depth: int, imaginary: int
) -> None:
    nested: object = scalar(0.25 + imaginary * 1j)
    for _ in range(depth):
        wrapper = np.empty((), dtype=object)
        wrapper[()] = nested
        nested = wrapper
    values = np.empty(2, dtype=object)
    values[0], values[1] = nested, 0.75
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        with pytest.raises(ValidationError, match="complex measurements"):
            vector(values, "measurement")
    assert observed == []


@pytest.mark.parametrize("scalar", [np.complex64, np.complex128, np.clongdouble])
@pytest.mark.parametrize("field", ["region_cutoff_m", "basin_diameter_m", "iterations"])
def test_complex_physical_configuration_refuses_before_scalar_cast(
    scalar: type, field: str
) -> None:
    arguments: dict[str, Any] = {
        "basin_diameter_m": 100,
        "region_cutoff_m": 100000,
        "iterations": 2,
    }
    arguments[field] = scalar(arguments[field] + 2j)
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        with pytest.raises(ValidationError, match="complex measurements"):
            RevealsConfig("peatland", **arguments)
    assert observed == []


def test_nested_real_object_scalars_preserve_coercion_and_input() -> None:
    inner = np.empty((), dtype=object)
    inner[()] = Decimal("0.25")
    values = np.empty(2, dtype=object)
    values[0], values[1] = inner, Fraction(3, 4)
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        np.testing.assert_array_equal(vector(values, "measurement"), [0.25, 0.75])
    assert observed == []
    assert values[0] is inner and inner[()] == Decimal("0.25")
