"""Keep missingness and raw measurement types at the owned count ingress."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.essd_reproduction.common_cover import (
    conditional_adequacy,
    count_admission,
    sample_dependence_bounds,
    within_site_homogeneity,
)
from bijux_pollenomics_lra.models.errors import ValidationError


def _matrix(kind: str) -> object:
    values = [[1, 2], [2, 1]]
    if kind == "list":
        return values
    if kind == "float":
        return np.asarray(values, dtype=float)
    if kind == "object":
        return np.asarray(values, dtype=object)
    if kind == "unmasked":
        return np.ma.array(values, mask=False)
    row = [1, 2]
    return [row, row]


@pytest.mark.parametrize("kind", ("list", "float", "object", "unmasked", "shared_row"))
def test_existing_owned_matrix_receives_original_value_and_real_numeric_result(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """Observe the reused implementation without replacing any numeric result."""
    value = _matrix(kind)
    seen: list[object] = []
    original = count_admission.multisite_likelihood._input_matrix

    def observed(value: object, name: str, *, nonnegative: bool = False) -> np.ndarray:
        seen.append(value)
        return original(value, name, nonnegative=nonnegative)

    monkeypatch.setattr(count_admission.multisite_likelihood, "_input_matrix", observed)
    result = count_admission.matrix(value, "counts")
    assert len(seen) == 1 and seen[0] is value
    np.testing.assert_array_equal(result, np.asarray(value, dtype=float))


@pytest.mark.parametrize("field", ("counts", "responses"))
@pytest.mark.parametrize(
    "value",
    (
        True,
        np.bool_(True),
        complex(1, 0),
        complex(1, 2),
        np.complex64(1),
        np.complex128(1 + 2j),
    ),
)
def test_public_conditional_ingress_refuses_raw_flags_and_complex_measurements(
    field: str, value: object
) -> None:
    """Keep ordinary counts valid before damaging exactly one physical cell."""
    counts = np.asarray([[1, 2], [2, 1]], dtype=object)
    responses = np.ones((2, 2), dtype=object)
    mask = np.ones((2, 2), dtype=bool)
    assert (
        conditional_adequacy.conditional_test(
            counts, responses, taxon_measured=mask
        ).status
        == "computed"
    )
    (counts if field == "counts" else responses)[0, 0] = value
    with pytest.raises(ValidationError):
        conditional_adequacy.conditional_test(counts, responses, taxon_measured=mask)


def _masked(kind: str) -> object:
    masked = np.ma.array([1, 2], mask=[False, True])
    if kind == "top":
        return np.ma.array([[1, 2], [2, 1]], mask=[[False, True], [False, False]])
    if kind == "row":
        return [masked, [2, 1]]
    if kind == "tuple":
        return ((masked,),)
    if kind == "object":
        result = np.empty(1, dtype=object)
        result[0] = masked
        return result
    if kind == "scalar_object":
        scalar = np.empty((), dtype=object)
        scalar[()] = masked
        return scalar
    value: object = masked
    for _ in range(1500):
        value = [value]
    return value


@pytest.mark.parametrize(
    "kind", ("top", "row", "tuple", "object", "scalar_object", "deep")
)
def test_nested_masks_refuse_before_numeric_coercion(kind: str) -> None:
    """Do not let conversion erase a mask in any supported container boundary."""
    count_admission.require_unmasked([[1, 2], [2, 1]], "counts")
    with pytest.raises(ValidationError):
        count_admission.require_unmasked(_masked(kind), "counts")


@pytest.mark.parametrize("kind", ("shared_list", "shared_array", "unmasked_nested"))
def test_shared_acyclic_aliases_and_all_false_masks_remain_admitted(kind: str) -> None:
    """Active-path cycle checks allow shared data and explicit unmasked values."""
    count_admission.require_unmasked([[1, 2], [2, 1]], "counts")
    if kind == "shared_list":
        row = [1, 2]
        value: object = [row, row]
    elif kind == "shared_array":
        row_array = np.asarray([1, 2], dtype=object)
        value = [row_array, row_array]
    else:
        value = [np.ma.array([1, 2], mask=False), (np.ma.array(3, mask=False),)]
    count_admission.require_unmasked(value, "counts")


def _cycle(kind: str) -> object:
    if kind == "array":
        array = np.empty(1, dtype=object)
        array[0] = array
        return array
    value: list[object] = []
    value.append(value if kind == "list" else (value,))
    return value


@pytest.mark.parametrize("kind", ("list", "array", "list_tuple"))
def test_container_cycles_refuse_with_the_owned_typed_reason(kind: str) -> None:
    """Refuse a current active-path back edge without a Python recursion failure."""
    count_admission.require_unmasked([[1, 2], [2, 1]], "counts")
    with pytest.raises(ValidationError) as caught:
        count_admission.require_unmasked(_cycle(kind), "counts")
    assert caught.value.reason_code == "common_cover_cyclic_input"


def test_deep_finite_container_walk_does_not_use_python_recursion() -> None:
    """Inspect deep finite values without claiming they form a numeric matrix."""
    value: object = 1
    for _ in range(1500):
        value = [value]
    count_admission.require_unmasked(value, "counts")


def _public(name: str, counts: Any) -> object:
    if name == "conditional":
        return conditional_adequacy.conditional_test(
            counts,
            [[1.0, 1.0], [1.0, 1.0]],
            taxon_measured=[[True, True], [True, True]],
        )
    if name == "homogeneity":
        return within_site_homogeneity.prepare(counts)
    return sample_dependence_bounds.sample_unit_bounds(counts)


@pytest.mark.parametrize("name", ("conditional", "homogeneity", "bounds"))
@pytest.mark.parametrize("kind", ("top", "row"))
def test_all_public_ingresses_refuse_hidden_missing_counts(
    name: str, kind: str
) -> None:
    """Keep each actual owning entrypoint attached to its mask gate."""
    assert _public(name, [[1, 2], [2, 1]]) is not None
    with pytest.raises(ValidationError):
        _public(name, _masked(kind))


@pytest.mark.parametrize("name", ("conditional", "homogeneity", "bounds"))
def test_all_public_ingresses_refuse_unrepresentable_or_out_of_domain_counts(
    name: str,
) -> None:
    """Preserve fixed integer ceilings or the accepted typed float-conversion refusal."""
    assert _public(name, [[1, 2], [2, 1]]) is not None
    with pytest.raises(ValidationError):
        _public(name, [[10**2000, 1], [1, 1]])


@pytest.mark.parametrize("name", ("conditional", "homogeneity", "bounds"))
def test_all_public_ingresses_preserve_typed_cycle_refusal(name: str) -> None:
    """No wrapper may send a cyclic container into numerical array conversion."""
    assert _public(name, [[1, 2], [2, 1]]) is not None
    with pytest.raises(ValidationError) as caught:
        _public(name, _cycle("list"))
    assert caught.value.reason_code == "common_cover_cyclic_input"


@pytest.mark.parametrize("name", ("conditional", "homogeneity", "bounds"))
def test_public_ingresses_preserve_ordinary_and_all_false_mask_results(
    name: str,
) -> None:
    """Keep real numerical results exact when a declared mask has no missing cells."""
    expected = _public(name, [[1, 2], [2, 1]])
    actual = _public(name, np.ma.array([[1, 2], [2, 1]], mask=False))
    assert actual == expected
