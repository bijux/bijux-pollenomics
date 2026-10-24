"""Container traversal preserves unresolved source missingness before coercion."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import _reject_masked_values, matrix


@pytest.mark.parametrize("container", [list, tuple])
@pytest.mark.parametrize("unresolved", [True, False])
def test_nested_rows_preserve_mask_admission_and_numeric_matrix_contract(
    container: type[list[Any]] | type[tuple[Any, ...]], unresolved: bool
) -> None:
    original = np.array([[1, 2], [3, 4]])
    rows = container([original[0], np.ma.array(original[1], mask=[unresolved, False])])
    if unresolved:
        with pytest.raises(ValidationError, match="counts contains masked"):
            matrix(rows, "counts")
    else:
        expected, actual = matrix(original, "counts"), matrix(rows, "counts")
        np.testing.assert_array_equal(actual, expected)
        assert actual.tobytes() == expected.tobytes()


@pytest.mark.parametrize("unresolved", [True, False])
def test_object_array_nested_containers_are_inspected(unresolved: bool) -> None:
    values = np.empty(2, dtype=object)
    values[0] = (np.array([1.0, 2.0]),)
    values[1] = [np.ma.array([3.0, 4.0], mask=[unresolved, False])]
    if unresolved:
        with pytest.raises(ValidationError, match="values contains masked"):
            _reject_masked_values(values, "values")
    else:
        _reject_masked_values(values, "values")


def test_shared_and_cyclic_containers_terminate_without_admitting_invalid_shape() -> (
    None
):
    shared = [1.0, 2.0]
    _reject_masked_values([shared, shared], "shared")
    cyclic: list[object] = []
    cyclic.append(cyclic)
    _reject_masked_values(cyclic, "cyclic")
    with pytest.raises(ValidationError):
        matrix(cyclic, "cyclic")
    cyclic.append(np.ma.array([3], mask=True))
    with pytest.raises(ValidationError, match="cyclic contains masked"):
        _reject_masked_values(cyclic, "cyclic")
    array = np.empty(1, dtype=object)
    array[0] = array
    _reject_masked_values(array, "array")
    with pytest.raises(ValidationError):
        matrix(array, "array")


def test_guard_does_not_consume_arbitrary_iterators() -> None:
    consumed: list[bool] = []

    def untouched() -> Iterator[object]:
        consumed.append(True)
        yield None

    _reject_masked_values(untouched(), "iterator")
    assert consumed == []
