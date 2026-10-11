"""Independent simplex, likelihood and numerical-domain counterexamples."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from scipy.optimize import minimize_scalar

from bijux_pollenomics_lra.api import (
    ValidationError,
    extension_descriptor,
    fit_homogeneous_likelihood,
    forward_deposition,
)
from bijux_pollenomics_lra.reconstruction.likelihood.homogeneous_likelihood import (
    homogeneous_cover_to_mixture,
    homogeneous_vertices,
)


def test_pure_taxon_columns_match_independent_forward_and_recover_cover() -> None:
    cover = np.array([0.1, 0.3, 0.6])
    kernels = np.array([[0.2, 0.5, 0.7], [0.4, 0.2, 0.6]])
    fraction = np.array([1.0, 0.5])
    ppe = np.array([1.0, 3.0, 5.0])
    background = np.array([0.2, 0.1, 0.15])
    a = ppe * (kernels * fraction[:, None]).sum(axis=0)
    y, _ = homogeneous_vertices(a, background)
    for index in range(3):
        expected = forward_deposition(
            np.eye(3)[index], background, kernels, fraction, ppe
        ).pollen_fraction
        np.testing.assert_allclose(y[:, index], expected, rtol=0, atol=1e-15)
    observed = forward_deposition(
        cover, background, kernels, fraction, ppe
    ).pollen_fraction
    fit = fit_homogeneous_likelihood(observed, a, background)
    np.testing.assert_allclose(fit.cover, cover, rtol=0, atol=1e-12)
    np.testing.assert_allclose(fit.predicted, observed, rtol=0, atol=1e-12)
    assert fit.exact_composition_fit and fit.converged
    assert fit.steps == 0
    assert fit.observed_mass == pytest.approx(1)
    assert fit.profile == "homogeneous-fixed-input-likelihood-v1"
    assert (
        "lra.love.homogeneous-fixed-input-likelihood"
        in extension_descriptor()["capabilities"]
    )
    assert np.array_equal(cover, [0.1, 0.3, 0.6])


def test_two_taxon_boundary_agrees_with_scalar_likelihood_oracle() -> None:
    counts = np.array([1.0, 99.0])
    a = np.array([1.0, 2.0])
    b = np.array([0.4, 0.1])

    def objective(v: float) -> float:
        total = a * [v, 1 - v] + b
        return float(-(counts / 100) @ np.log(total / total.sum()))

    oracle = minimize_scalar(objective, bounds=(0, 1), method="bounded")
    best = min((objective(0), 0), (objective(1), 1), (oracle.fun, oracle.x))
    fit = fit_homogeneous_likelihood(counts, a, b)
    assert fit.converged and not fit.exact_composition_fit
    assert fit.cover[0] == pytest.approx(best[1], abs=1e-7)
    assert fit.mean_negative_log_likelihood == pytest.approx(best[0], abs=1e-10)


def test_zero_observed_counts_need_no_pseudocount_and_infeasible_inverse_is_fitted() -> (
    None
):
    fit = fit_homogeneous_likelihood([0, 50, 50], [1, 2, 3], [0.2, 0.2, 0.2])
    assert fit.converged
    assert not fit.exact_composition_fit
    assert fit.cover[0] == 0
    assert fit.predicted[0] > 0
    expected = -0.5 * (np.log(fit.predicted[1]) + np.log(fit.predicted[2]))
    assert fit.mean_negative_log_likelihood == pytest.approx(expected)
    y, _ = homogeneous_vertices([1, 2, 3], [0.2, 0.2, 0.2])
    assert np.linalg.solve(y, [0, 0.5, 0.5]).min() < 0
    gradient = -(y[1:].T @ (np.array([0.5, 0.5]) / fit.predicted[1:]))
    gap = max(0, float(gradient @ fit.mixture - gradient.min()))
    assert fit.optimality_gap == pytest.approx(gap, abs=1e-15)
    # The convex inequality is tested against independent feasible alternatives.
    for cover in ([0.1, 0.3, 0.6], [0, 0.5, 0.5], [0.5, 0.2, 0.3]):
        p = np.asarray([1, 2, 3]) * cover + 0.2
        p /= p.sum()
        other_nll = -0.5 * (np.log(p[1]) + np.log(p[2]))
        assert other_nll >= fit.mean_negative_log_likelihood - gap - 1e-12


def test_exhausted_budget_returns_visible_nonconvergence() -> None:
    fit = fit_homogeneous_likelihood(
        [0, 50, 50], [1, 2, 3], [0.2, 0.2, 0.2], max_steps=0
    )
    assert not fit.converged
    assert fit.stop_reason == "step_limit"
    assert fit.steps == 0
    assert fit.optimality_gap > fit.gap_tolerance
    assert np.isfinite(fit.mean_negative_log_likelihood)


def test_small_active_mass_does_not_exhaust_line_precision() -> None:
    rng = np.random.default_rng(20261002)
    for taxa in (3, 10, 30):
        for case in range(20):
            kernels = rng.uniform(0.02, 1, (4, taxa))
            fraction = rng.uniform(0.3, 1, 4)
            ppe = rng.uniform(0.3, 8, taxa)
            background = rng.uniform(0.001, 0.4, taxa)
            cover = rng.dirichlet(np.ones(taxa) * 2)
            pollen = forward_deposition(
                cover, background, kernels, fraction, ppe
            ).pollen_fraction
            counts = rng.multinomial(500, pollen)
            if (taxa, case) == (30, 5):
                a = ppe * (kernels * fraction[:, None]).sum(axis=0)
                fit = fit_homogeneous_likelihood(counts, a, background)
                assert fit.converged
                assert fit.optimality_gap <= 1e-7
                assert fit.stop_reason == "gap_tolerance"
                assert fit.steps < 1000
                return
    pytest.fail("The declared fixed-seed regression case was absent")


@pytest.mark.parametrize("scale", [1e-200, 1e200])
def test_common_deposition_units_and_observation_scaling_preserve_point_fit(
    scale: float,
) -> None:
    n = np.array([0, 50, 50])
    a = np.array([1, 2, 3])
    b = np.array([0.2, 0.2, 0.2])
    first = fit_homogeneous_likelihood(n, a, b)
    second = fit_homogeneous_likelihood(n * 13, a * scale, b * scale)
    np.testing.assert_allclose(second.cover, first.cover, rtol=0, atol=1e-8)
    assert second.mean_negative_log_likelihood == pytest.approx(
        first.mean_negative_log_likelihood
    )
    assert second.observed_mass == 1300


@pytest.mark.parametrize(
    "weights,a,b",
    [
        ([1e308, 1e308, 1e308], [1, 2, 3], [0.2] * 3),
        ([0, 0], [1, 2], [0, 0]),
        ([-1, 2], [1, 2], [0, 0]),
        ([1, np.nan], [1, 2], [0, 0]),
        ([1, 2], [0, 2], [0, 0]),
        ([1, 2], [1, 2], [-0.1, 0]),
        ([1, 2, 3], [1, 2], [0, 0]),
        ([1, 2], [1, 2], [0]),
        ([1, 2], [1e-300, 1e300], [0, 0]),
        ([1e-300, 1e300], [1, 2], [0, 0]),
    ],
)
def test_invalid_mass_support_and_underflow_refuse(
    weights: object, a: object, b: object
) -> None:
    with pytest.raises(ValidationError):
        fit_homogeneous_likelihood(weights, a, b)


def test_dominant_background_is_an_explicit_conditioning_refusal() -> None:
    with pytest.raises(ValidationError) as caught:
        fit_homogeneous_likelihood([1, 2, 3], [1, 2, 3], [1e20] * 3)
    assert caught.value.reason_code == "homogeneous_likelihood_ill_conditioned"


@pytest.mark.parametrize("cover", [[0.5, 0.500005], [0.5, 0.5 + 2e-12]])
def test_absolute_cover_closure_does_not_use_default_relative_tolerance(
    cover: object,
) -> None:
    with pytest.raises(ValidationError, match="absolute"):
        homogeneous_cover_to_mixture(cover, [1, 2], [0, 0])


@pytest.mark.parametrize(
    "options",
    [
        {"gap_tolerance": 0},
        {"gap_tolerance": np.nan},
        {"max_steps": -1},
        {"max_steps": 1.5},
        {"max_steps": True},
        {"max_condition_number": 0.5},
        {"max_condition_number": np.inf},
    ],
)
def test_invalid_numerical_contract_refuses(options: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        fit_homogeneous_likelihood([1, 2], [1, 2], [0, 0], **options)


def test_no_background_observed_zeros_have_exact_zero_cover_and_owned_results() -> None:
    weights = np.array([0, 10, 0])
    fit = fit_homogeneous_likelihood(weights, [1, 2, 3], [0, 0, 0])
    assert fit.converged and fit.exact_composition_fit
    np.testing.assert_array_equal(fit.cover, [0, 1, 0])
    assert fit.mean_negative_log_likelihood == 0
    assert fit.optimality_gap == 0
    assert np.array_equal(weights, [0, 10, 0])
    for value in (fit.cover, fit.predicted, fit.mixture):
        with pytest.raises(ValueError):
            value[0] = 1
