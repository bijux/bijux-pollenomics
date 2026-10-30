"""Keep common-cover input refusal local to its new numerical methods."""

from __future__ import annotations

from typing import Any, NoReturn

import numpy as np
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import matrix
from bijux_pollenomics_lra.reconstruction.likelihood import multisite_likelihood


@pytest.mark.parametrize(
    "value",
    [
        [[1, 2]],
        ((1.0, 2.0),),
        np.array([[1, 2]], dtype=np.int64),
        np.array([[1, 2]], dtype=np.float64),
        np.array([[1, 2]], dtype=object),
        np.ma.array([[1, 2]], mask=False),
    ],
)
def test_numeric_matrix_keeps_existing_conversion_and_bounds(value: Any) -> None:
    expected = matrix(value, "counts", nonnegative=True)
    actual = multisite_likelihood._input_matrix(value, "counts", nonnegative=True)
    np.testing.assert_array_equal(actual, expected)
    assert actual.dtype == expected.dtype
    assert actual.shape == expected.shape


@pytest.mark.parametrize(
    "value",
    [
        [[True, 2]],
        [[1, False]],
        ((np.bool_(True), 2),),
        np.array([[True, False]]),
        np.array([[1, True]], dtype=object),
    ],
)
def test_boolean_measurements_refuse_before_shared_conversion(
    value: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    np.testing.assert_array_equal(
        multisite_likelihood._input_matrix([[1, 2]], "counts"), [[1.0, 2.0]]
    )

    def unexpected_conversion(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Boolean measurement reached numeric conversion")

    monkeypatch.setattr(multisite_likelihood, "matrix", unexpected_conversion)
    with pytest.raises(ValidationError, match="Boolean"):
        multisite_likelihood._input_matrix(value, "counts")


@pytest.mark.parametrize(
    "value",
    [
        np.ma.array([[1, 2]], mask=[[True, False]]),
        np.ma.array([[1, 2]], mask=True),
        np.ma.masked,
    ],
)
def test_unresolved_matrix_masks_refuse_before_shared_conversion(
    value: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    np.testing.assert_array_equal(
        multisite_likelihood._input_matrix([[1, 2]], "responses"), [[1.0, 2.0]]
    )

    def unexpected_conversion(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Masked measurement reached numeric conversion")

    monkeypatch.setattr(multisite_likelihood, "matrix", unexpected_conversion)
    with pytest.raises(ValidationError, match="masked"):
        multisite_likelihood._input_matrix(value, "responses")


@pytest.mark.parametrize(
    "value", [0.95, np.float64(0.95), np.ma.array(0.95, mask=False)]
)
def test_resolved_confidence_metadata_is_not_numerically_rewritten(value: Any) -> None:
    assert multisite_likelihood._require_unmasked(value, "confidence_level") is None


@pytest.mark.parametrize("value", [np.ma.masked, np.ma.array(0.95, mask=True)])
def test_unresolved_confidence_mask_refuses(value: Any) -> None:
    with pytest.raises(ValidationError, match="masked"):
        multisite_likelihood._require_unmasked(value, "confidence_level")


@pytest.mark.parametrize(
    "value", [[[10**500, 1]], [["not a number", 1]], [[1], [2, 3]]]
)
def test_nonrepresentable_or_malformed_matrices_have_public_refusal(value: Any) -> None:
    with pytest.raises(ValidationError):
        multisite_likelihood._input_matrix(value, "counts")


@pytest.mark.parametrize(
    "value", [[[-1, 2]], [[float("nan"), 2]], [[float("inf"), 2]], [1, 2]]
)
def test_existing_matrix_refusal_messages_and_bounds_remain_authoritative(
    value: Any,
) -> None:
    with pytest.raises(ValidationError) as expected:
        matrix(value, "counts", nonnegative=True)
    with pytest.raises(ValidationError) as actual:
        multisite_likelihood._input_matrix(value, "counts", nonnegative=True)
    assert actual.value.args == expected.value.args


@pytest.mark.parametrize("name", ["score_tolerance", "relative_count_tolerance"])
@pytest.mark.parametrize(
    "value", [True, np.bool_(True), [True], np.array([True], dtype=object)]
)
def test_boolean_tolerances_refuse_before_existing_scalar_parser(
    name: str, value: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = multisite_likelihood.fit_multisite_likelihood(
        [[1, 2]], [[1, 2]], taxon_measured=[[True, True]]
    )
    assert baseline.converged

    def unexpected_scalar(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Boolean tolerance reached the existing scalar parser")

    monkeypatch.setattr(multisite_likelihood, "finite_number", unexpected_scalar)
    kwargs: dict[str, Any] = {name: value}
    with pytest.raises(ValidationError, match="Boolean"):
        multisite_likelihood.fit_multisite_likelihood(
            [[1, 2]], [[1, 2]], taxon_measured=[[True, True]], **kwargs
        )


@pytest.mark.parametrize(
    "name", ["score_tolerance", "relative_count_tolerance", "max_steps"]
)
def test_unresolved_scalar_masks_refuse_before_existing_scalar_parser(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = multisite_likelihood.fit_multisite_likelihood(
        [[1, 2]], [[1, 2]], taxon_measured=[[True, True]]
    )
    assert baseline.converged

    def unexpected_scalar(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Masked control reached the existing scalar parser")

    monkeypatch.setattr(multisite_likelihood, "finite_number", unexpected_scalar)
    kwargs: dict[str, Any] = {name: np.ma.masked}
    with pytest.raises(ValidationError, match="masked"):
        multisite_likelihood.fit_multisite_likelihood(
            [[1, 2]], [[1, 2]], taxon_measured=[[True, True]], **kwargs
        )


@pytest.mark.parametrize("name", ["counts", "responses"])
@pytest.mark.parametrize(
    "value",
    [
        [[1 + 1j, 2]],
        np.array([[1 + 1j, 2]], dtype=np.complex128),
        np.array([[1 + 0j, 2]], dtype=np.complex64),
        np.array([[complex(1, 1), 2]], dtype=object),
        np.array([[np.complex128(1 + 1j), 2]], dtype=object),
    ],
)
def test_complex_measurements_refuse_before_any_lossy_shared_conversion(
    name: str, value: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = multisite_likelihood.fit_multisite_likelihood(
        [[1, 2]], [[1, 2]], taxon_measured=[[True, True]]
    )
    assert baseline.converged
    converted: list[str] = []

    def observed_matrix(
        original: object, field: str, *, nonnegative: bool = False
    ) -> np.ndarray:
        converted.append(field)
        return matrix(original, field, nonnegative=nonnegative)

    monkeypatch.setattr(multisite_likelihood, "matrix", observed_matrix)
    counts, responses = (value, [[1, 2]]) if name == "counts" else ([[1, 2]], value)
    with pytest.raises(ValidationError, match="complex"):
        multisite_likelihood.fit_multisite_likelihood(
            counts, responses, taxon_measured=[[True, True]]
        )
    assert converted == ([] if name == "counts" else ["counts"])
