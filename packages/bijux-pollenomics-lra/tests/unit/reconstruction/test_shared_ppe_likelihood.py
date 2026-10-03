"""Bound a shared PPE vector across regional and local likelihood inputs."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import NotRequired, TypedDict

import numpy as np
import pytest

from bijux_pollenomics_lra.api import extension_descriptor, fit_shared_ppe_likelihood
from bijux_pollenomics_lra.dispersal.rounding import r_round
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.draws import rnorm_reveals
from bijux_pollenomics_lra.reconstruction.homogeneous_likelihood import (
    HomogeneousLikelihoodFit,
    fit_homogeneous_likelihood,
)
from bijux_pollenomics_lra.reconstruction.shared_ppe_likelihood import (
    SharedPpeLikelihoodResult,
)


class SharedPpeInputs(TypedDict):
    regional_counts: object
    local_counts: object
    ppe_mean: object
    ppe_sd: object
    ppe_covariance: object
    regional_kernel: object
    local_kernels: object
    terrestrial_fractions: object
    draws: int
    seed: int
    max_attempts: NotRequired[int]


def _invalid_fit(parameters: Mapping[str, object]) -> SharedPpeLikelihoodResult:
    runtime_call: Callable[..., SharedPpeLikelihoodResult] = fit_shared_ppe_likelihood
    return runtime_call(**parameters)


def _inputs() -> SharedPpeInputs:
    return {
        "regional_counts": [9, 6],
        "local_counts": [8, 7],
        "ppe_mean": [2.0, 3.0],
        "ppe_sd": [0.2, 0.0],
        "ppe_covariance": [[0.04, 0.0], [0.0, 0.0]],
        "regional_kernel": [0.4, 0.6],
        "local_kernels": [[0.8, 0.7], [0.0, 0.0], [0.2, 0.3]],
        "terrestrial_fractions": [1.0, 1.0, 1.0],
        "draws": 3,
        "seed": 20261002,
    }


def test_public_facade_declares_conditional_draw_capability() -> None:
    assert (
        "lra.love.homogeneous-shared-ppe-conditional-draws"
        in extension_descriptor()["capabilities"]
    )


def test_shared_ppe_draw_and_regional_local_coupling() -> None:
    parameters = _inputs()
    result = fit_shared_ppe_likelihood(**parameters)
    rng = np.random.default_rng(20261002)
    expected = np.array(
        [
            [2.0, 3.0],
            rnorm_reveals(2, [2.0, 3.0], [0.2, 0.0], rng=rng),
            rnorm_reveals(2, [2.0, 3.0], [0.2, 0.0], rng=rng),
        ]
    )
    np.testing.assert_array_equal(result.ppe_draws, expected)
    raw = np.array([9, 6])[None, :] / (expected * [0.4, 0.6])
    np.testing.assert_array_equal(
        result.regional_cover,
        r_round(100 * raw / raw.sum(axis=1)[:, None], 3) / 100,
    )
    assert len(result.fits) == 3
    assert all(fit.converged and fit.optimality_gap <= 1e-7 for fit in result.fits)
    assert np.max(result.forward_max_abs) <= 1e-12
    observed = np.array([8, 7], dtype=float) / 15
    for index, draw in enumerate(result.ppe_draws):
        local = result.local_cover[index]
        a = draw * [0.8, 0.7]
        b = draw * result.regional_cover[index] * [0.2, 0.3]
        predicted = (a * local + b) / (a @ local + b.sum())
        scale = max(a.max(), b.max())
        scaled_a, scaled_b = a / scale, b / scale
        denominators = scaled_a + scaled_b.sum()
        vertices = (np.diag(scaled_a) + scaled_b[:, None]) / denominators[None, :]
        mixture = local * denominators / (local @ denominators)
        gradient = -(vertices.T @ (observed / predicted))
        gap = max(0.0, float(gradient @ mixture - gradient.min()))
        fit = result.fits[index]
        np.testing.assert_allclose(fit.predicted, predicted, rtol=0, atol=1e-14)
        np.testing.assert_allclose(
            fit.mean_negative_log_likelihood,
            -observed @ np.log(predicted),
            rtol=0,
            atol=1e-14,
        )
        np.testing.assert_allclose(fit.optimality_gap, gap, rtol=0, atol=1e-12)


def test_regional_three_decimal_rounding_does_not_force_closure() -> None:
    parameters = _inputs()
    parameters["regional_counts"] = [1, 1, 1]
    parameters["local_counts"] = [1, 1, 1]
    parameters["ppe_mean"] = [1.0, 1.0, 1.0]
    parameters["ppe_sd"] = [0.0, 0.0, 0.0]
    parameters["ppe_covariance"] = np.zeros((3, 3))
    parameters["regional_kernel"] = [1.0, 1.0, 1.0]
    parameters["local_kernels"] = [[1.0, 1.0, 1.0], [0.0, 0.0, 0.0]]
    parameters["terrestrial_fractions"] = [1.0, 1.0]
    parameters["draws"] = 2
    result = fit_shared_ppe_likelihood(**parameters)
    np.testing.assert_allclose(
        result.regional_cover[0], [0.33333] * 3, rtol=0, atol=1e-15
    )
    assert result.regional_cover[0].sum() != 1.0
    np.testing.assert_array_equal(result.ppe_draws[0], result.ppe_draws[1])
    np.testing.assert_array_equal(result.local_cover[0], result.local_cover[1])


@pytest.mark.parametrize(
    ("field", "changed"),
    [
        ("ppe_covariance", [[0.04, 0.01], [0.01, 0.0]]),
        ("ppe_covariance", [[0.09, 0.0], [0.0, 0.0]]),
        ("ppe_covariance", [[0.04, 0.0], [0.0, 1e-13]]),
        ("ppe_mean", [0.0, 3.0]),
        ("ppe_sd", [-0.2, 0.0]),
        ("ppe_sd", [0.3, 0.0]),
        ("ppe_sd", [1e308, 0.0]),
        ("regional_counts", [1e308, 1e308]),
        ("regional_counts", [0, 0]),
        ("regional_counts", [9]),
        ("local_counts", [0, 0]),
        ("regional_kernel", [0.0, 0.6]),
        ("local_kernels", [[0.8, 0.7]]),
        ("terrestrial_fractions", [1.0, 1.0]),
        ("terrestrial_fractions", [1.0, 1.0, 1.1]),
        ("local_kernels", [[0.0, 0.7], [0.0, 0.0], [0.2, 0.3]]),
        ("local_kernels", [["bad", 0.7], [0.0, 0.0], [0.2, 0.3]]),
        ("ppe_mean", ["bad", 3.0]),
    ],
)
def test_invalid_ppe_or_deposition_refused(field: str, changed: object) -> None:
    parameters = dict(_inputs())
    parameters[field] = changed
    with pytest.raises(ValidationError):
        _invalid_fit(parameters)


@pytest.mark.parametrize(
    ("field", "changed"),
    [
        ("seed", -1),
        ("seed", True),
        ("draws", 1),
        ("draws", True),
        ("max_attempts", 0),
        ("max_attempts", True),
    ],
)
def test_sampling_bounds_refused_before_work(field: str, changed: object) -> None:
    parameters = dict(_inputs())
    parameters[field] = changed
    with pytest.raises(ValidationError, match="explicit integers"):
        _invalid_fit(parameters)


def test_whole_vector_positive_draw_exhaustion_refused() -> None:
    parameters = _inputs()
    parameters["ppe_mean"] = [1.0, 1.0]
    parameters["ppe_sd"] = [100.0, 100.0]
    parameters["ppe_covariance"] = [[10_000.0, 0.0], [0.0, 10_000.0]]
    parameters["seed"] = 0
    parameters["max_attempts"] = 1
    with pytest.raises(ValidationError, match="max_attempts"):
        fit_shared_ppe_likelihood(**parameters)


def test_nonconverged_fit_refuses_entire_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import bijux_pollenomics_lra.reconstruction.shared_ppe_likelihood as subject

    real_fit: Callable[..., HomogeneousLikelihoodFit] = fit_homogeneous_likelihood

    def fail_second(*args: object, **kwargs: object) -> HomogeneousLikelihoodFit:
        fit = real_fit(*args, **kwargs)
        if calls[0] == 1:
            from dataclasses import replace

            return replace(fit, converged=False)
        calls[0] += 1
        return fit

    calls = [0]
    monkeypatch.setattr(subject, "fit_homogeneous_likelihood", fail_second)
    with pytest.raises(ValidationError, match="draw 1 did not converge"):
        subject.fit_shared_ppe_likelihood(**_inputs())


def test_regional_rounding_retains_source_floating_point_tie() -> None:
    parameters = _inputs()
    parameters["regional_counts"] = [11, 199989]
    parameters["ppe_mean"] = [1.0, 1.0]
    parameters["ppe_sd"] = [0.0, 0.0]
    parameters["ppe_covariance"] = np.zeros((2, 2))
    parameters["regional_kernel"] = [1.0, 1.0]
    parameters["draws"] = 2
    result = fit_shared_ppe_likelihood(**parameters)
    assert np.round(100 * 11 / 200000, 3) == 0.006
    assert result.regional_cover[0, 0] == 0.005 / 100


def test_result_arrays_are_owned_read_only_and_independent_of_inputs() -> None:
    parameters = _inputs()
    means = np.array([2.0, 3.0])
    parameters["ppe_mean"] = means
    result = fit_shared_ppe_likelihood(**parameters)
    means[:] = 100.0
    np.testing.assert_array_equal(result.ppe_draws[0], [2.0, 3.0])
    for array in (
        result.ppe_draws,
        result.regional_cover,
        result.local_cover,
        result.forward_max_abs,
    ):
        assert array.flags.owndata
        assert not array.flags.writeable
        with pytest.raises(ValueError, match="read-only"):
            array.flat[0] = 0.0
