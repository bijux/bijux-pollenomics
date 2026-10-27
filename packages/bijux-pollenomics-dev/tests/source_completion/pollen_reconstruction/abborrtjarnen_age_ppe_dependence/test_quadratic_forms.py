"""Distinguish common covariance across ages from a separate covariance per age."""

from __future__ import annotations

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe_dependence import (
    quadratic_forms as forms,
)


def test_two_age_counterexample_has_shared_variance_two_not_per_age_extrema() -> None:
    gradients = np.array([[1.0, 1.0], [1.0, -1.0]])
    q = gradients.T @ gradients / 2
    for correlation in (-1.0, -0.3, 0.0, 0.8, 1.0):
        r = np.array([[1.0, correlation], [correlation, 1.0]])
        assert np.sum(q * r.T) == 2
    assert (
        np.mean(np.maximum(0, np.abs(gradients[:, 0]) - np.abs(gradients[:, 1])) ** 2)
        == 0
    )
    assert np.mean(np.sum(np.abs(gradients), axis=1) ** 2) == 4
    assert np.mean(gradients, axis=0) @ np.mean(gradients, axis=0) == 1


def test_outer_moment_not_outer_mean_and_population_not_sample_denominator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second = np.zeros((50, 4)), np.zeros((50, 4))
    first[:, :2] = [1, 1]
    second[:, :2] = [1, -1]
    sequence = iter([first, second])
    monkeypatch.setattr(forms, "scaled_gradients", lambda *_: next(sequence))
    q, requested, complete = forms.accumulate([[], None, []], np.ones(5), np.ones(5))
    assert (requested, complete) == (3, 2)
    np.testing.assert_array_equal(q[0], np.diag([1, 1, 0, 0]))


def test_contrast_gradient_precedes_outer_product_and_poa_output_survives() -> None:
    covers = [0.2] * 20
    covers[5:10] = [0.3, 0.1, 0.2, 0.25, 0.15]
    ppe = np.array([2.0, 3.0, 4.0, 5.0, 1.0])
    sd = np.array([0.1, 0.2, 0.3, 0.4, 0.0])
    scaled = forms.scaled_gradients(covers, ppe, sd)
    expected = np.array(
        [
            (
                covers[5] * (covers[5 + j] - int(j == 0))
                - covers[0] * (covers[j] - int(j == 0))
            )
            / ppe[j]
            * sd[j]
            for j in range(4)
        ]
    )
    np.testing.assert_allclose(scaled[20], expected, atol=1e-16, rtol=0)
    assert scaled.shape == (50, 4) and np.all(scaled[4] > 0)
    q, requested, complete = forms.accumulate([covers], ppe, sd)
    np.testing.assert_allclose(
        q[20], np.outer(expected, expected), atol=1e-18, rtol=1e-11
    )
    assert np.trace(q[4]) > 0 and (requested, complete) == (1, 1)
    axes = forms.scalar_axes()
    assert (
        len(axes) == 50
        and axes[4]["taxon"] == "Poaceae"
        and axes[24]["taxon"] == "Poaceae"
    )


@pytest.mark.parametrize("corruption", ["empty", "nonfinite"])
def test_unavailable_form_is_not_projected_or_imputed(corruption: str) -> None:
    covers = [0.2] * 20
    covers[0] = float("nan")
    with pytest.raises(ValueError):
        forms.accumulate(
            [None] if corruption == "empty" else [covers], np.ones(5), np.ones(5)
        )
