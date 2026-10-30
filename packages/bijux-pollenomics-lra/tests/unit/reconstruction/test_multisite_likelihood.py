"""Independent scalar likelihood and heterogeneous known-truth contracts."""

from __future__ import annotations

from fractions import Fraction
from math import lcm
from typing import Any

import numpy as np
import pytest
from scipy.optimize import brentq

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.likelihood.multisite_likelihood import (
    fit_multisite_likelihood,
)


def fit(counts: Any, responses: Any, **kwargs: Any) -> Any:
    return fit_multisite_likelihood(
        counts,
        responses,
        taxon_measured=np.ones(np.shape(counts), dtype=bool),
        **kwargs,
    )


def scalar_oracle(counts: np.ndarray, responses: np.ndarray) -> float:
    observed = counts[:, 0].sum()
    if observed == 0:
        return 0.0
    if counts[:, 1].sum() == 0:
        return 1.0

    def score(v: float) -> float:
        p = responses[:, 0] * v / (responses[:, 0] * v + responses[:, 1] * (1 - v))
        return float(counts.sum(axis=1) @ p - observed)

    return float(brentq(score, 0, 1, xtol=5e-15, rtol=1e-14))


@pytest.mark.parametrize(
    "counts",
    [
        [[90, 10], [50, 50]],
        [[80, 20], [40, 60]],
        [[1, 99], [80, 20]],
        [[0, 10], [20, 0]],
        [[900, 100], [5, 5]],
    ],
)
@pytest.mark.parametrize(
    "responses", [[[9, 1], [1, 1]], [[0.1, 3], [2, 0.3]], [[2, 1], [20, 10]]]
)
def test_two_taxon_fit_matches_independent_scalar_root_and_actual_nll(
    counts: Any, responses: Any
) -> None:
    n, a = np.array(counts), np.array(responses)
    result = fit(n, a)
    assert result.converged
    expected = scalar_oracle(n, a)
    np.testing.assert_allclose(
        result.cover, [expected, 1 - expected], rtol=0, atol=2e-9
    )
    pollen = a * result.cover
    pollen /= pollen.sum(axis=1, keepdims=True)
    np.testing.assert_allclose(result.predicted, pollen, rtol=1e-13, atol=1e-15)
    independent_nll = (
        -sum(
            float(n[s, i]) * np.log(pollen[s, i])
            for s in range(2)
            for i in range(2)
            if n[s, i]
        )
        / n.sum()
    )
    assert result.mean_negative_log_likelihood == pytest.approx(
        independent_nll, abs=2e-14
    )
    assert result.score_residual <= result.score_tolerance
    assert result.relative_count_residual <= result.relative_count_tolerance
    assert result.profile == "heterogeneous-fixed-response-multinomial-likelihood-v1"


def test_distinct_common_cover_likelihood_preserves_effort_and_does_not_average_basins() -> (
    None
):
    counts = np.array([[90, 10], [50, 50]])
    responses = np.array([[9, 1], [1, 1]])
    result = fit(counts, responses)
    np.testing.assert_allclose(result.cover, [0.5, 0.5], rtol=0, atol=1e-12)
    pooled_average_response = counts.sum(axis=0) / responses.mean(axis=0)
    pooled_average_response /= pooled_average_response.sum()
    np.testing.assert_allclose(
        pooled_average_response, [7 / 22, 15 / 22], rtol=0, atol=1e-15
    )
    assert abs(result.cover[0] - pooled_average_response[0]) > 0.1
    noisy = np.array([[80, 20], [40, 60]])
    likelihood = fit(noisy, responses)
    corrected_pool = (noisy / responses).sum(axis=0)
    corrected_pool /= corrected_pool.sum()
    assert abs(likelihood.cover[0] - corrected_pool[0]) > 0.001
    effort_changed = noisy.copy()
    effort_changed[0] *= 10
    more_effort = fit(effort_changed, responses)
    assert (
        more_effort.converged and abs(more_effort.cover[0] - likelihood.cover[0]) > 0.01
    )


def test_proportional_response_rows_reduce_to_analytic_count_correction() -> None:
    counts = np.array([[9, 5, 8], [4, 15, 3], [1, 8, 6]])
    response = np.array([0.2, 5.0, 1.5])
    result = fit(counts, np.array([1.0, 7.0, 0.01])[:, None] * response)
    expected = counts.sum(axis=0) / response
    expected /= expected.sum()
    assert result.converged
    np.testing.assert_allclose(result.cover, expected, rtol=1e-12, atol=1e-14)


def known_truth() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    cover = (Fraction(1, 2), Fraction(1, 3), Fraction(1, 6))
    responses = [[1, 2, 3], [3, 2, 1], [2, 3, 1]]
    counts = []
    for effort, row in zip((13, 7, 29), responses, strict=True):
        raw = [a * v for a, v in zip(row, cover, strict=True)]
        fractions = [v / sum(raw) for v in raw]
        total = lcm(*(v.denominator for v in fractions)) * effort
        counts.append([int(v * total) for v in fractions])
    return (
        np.array(counts),
        np.array(responses, dtype=float),
        np.array(cover, dtype=float),
    )


def test_exact_integer_forward_populations_recover_heterogeneous_common_cover() -> None:
    counts, responses, truth = known_truth()
    original = counts.copy(), responses.copy()
    result = fit(counts, responses)
    assert result.converged
    np.testing.assert_allclose(result.cover, truth, rtol=0, atol=2e-10)
    expected_pollen = responses * truth
    expected_pollen /= expected_pollen.sum(axis=1, keepdims=True)
    np.testing.assert_allclose(result.predicted, expected_pollen, rtol=0, atol=2e-10)
    assert np.array_equal(counts, original[0]) and np.array_equal(
        responses, original[1]
    )
    for value in (
        result.cover,
        result.predicted,
        result.site_totals,
        result.observed_taxon_totals,
        result.site_used,
        result.active_taxa,
    ):
        assert not value.flags.writeable


@pytest.mark.parametrize("scale", [1e-250, 1e250])
def test_positive_response_unit_scales_and_permutations_preserve_fit(
    scale: float,
) -> None:
    counts, responses, _ = known_truth()
    baseline = fit(counts, responses)
    changed = fit(
        counts[::-1, ::-1], responses[::-1, ::-1] * scale * np.array([2, 5, 3])[:, None]
    )
    assert changed.converged
    np.testing.assert_allclose(changed.cover, baseline.cover[::-1], rtol=0, atol=3e-10)
    np.testing.assert_allclose(
        changed.predicted, baseline.predicted[::-1, ::-1], rtol=0, atol=3e-10
    )
    assert changed.mean_negative_log_likelihood == pytest.approx(
        baseline.mean_negative_log_likelihood, abs=1e-13
    )


def test_zero_observed_taxon_is_exact_boundary_and_no_effort_site_is_accounted() -> (
    None
):
    counts = [[0, 10, 20], [0, 0, 0], [0, 15, 8]]
    responses = [[9, 1, 2], [7, 2, 1], [1, 3, 2]]
    result = fit(counts, responses)
    assert result.converged and result.cover[0] == 0
    assert np.array_equal(result.predicted[:, 0], [0, 0, 0])
    assert result.excluded_zero_total_site_indices == (1,)
    assert np.array_equal(result.site_used, [True, False, True])
    assert np.array_equal(result.site_totals, [30, 0, 23])
    assert result.predicted.shape == (3, 3)
    reduced = fit(np.array(counts)[[0, 2]], np.array(responses)[[0, 2]])
    np.testing.assert_allclose(reduced.cover, result.cover, rtol=0, atol=1e-12)


def test_single_active_taxon_has_exact_degenerate_solution_without_iterations() -> None:
    result = fit([[0, 8, 0], [0, 0, 0]], [[1, 3, 8], [9, 2, 3]], max_steps=0)
    assert result.converged and result.stop_reason == "single_active_taxon"
    assert result.steps == 0 and result.mean_negative_log_likelihood == 0
    assert np.array_equal(result.cover, [0, 1, 0])
    assert np.array_equal(result.predicted, [[0, 1, 0], [0, 1, 0]])


def test_exhaustion_and_rare_taxon_imbalance_cannot_be_reported_as_converged() -> None:
    counts = [[2**52 - 1, 1], [2**52 - 1, 0]]
    responses = [[1, 1], [1, 1e8]]
    initial = fit(counts, responses, max_steps=0)
    assert initial.score_residual < initial.score_tolerance
    assert initial.relative_count_residual > 1000
    assert not initial.converged and initial.stop_reason == "step_limit"
    result = fit(counts, responses)
    assert result.converged
    assert result.relative_count_residual <= result.relative_count_tolerance
    assert result.cover[1] > 0
    assert result.hessian_condition_number == 1
    assert result.minimum_relative_information > result.information_resolution_floor


def test_statistically_identifiable_saturated_design_is_numerically_unresolved() -> (
    None
):
    # With R=1e200 and t=v0/v1, the exact optimum solves R*t²-t-2R=0.
    # Its representable limit is sqrt(2)/(1+sqrt(2)), not the tiny initializer.
    expected = np.sqrt(2.0) / (1 + np.sqrt(2.0))
    result = fit([[2, 0], [0, 1]], [[1e100, 1e-100], [1e-100, 1e100]])
    assert not result.converged
    assert result.stop_reason == "floating_information_unresolved"
    assert result.score_residual == result.relative_count_residual == 0
    assert result.hessian_condition_number == 1
    assert (
        0 < result.minimum_relative_information <= result.information_resolution_floor
    )
    assert abs(result.cover[0] - expected) > 0.5


def test_unrepresentable_active_cover_refuses_instead_of_becoming_observed_zero() -> (
    None
):
    with pytest.raises(ValidationError, match="active cover"):
        fit([[1, 1]], [[np.nextafter(0.0, 1.0), np.finfo(float).max]])


@pytest.mark.parametrize("second_counts", [[0, 0], [0, 10]])
def test_unobserved_active_prediction_underflow_refuses_even_without_site_effort(
    second_counts: list[int],
) -> None:
    with pytest.raises(ValidationError, match="Active predicted probability"):
        fit(
            [[1000, 1000], second_counts],
            [[1, 1], [np.nextafter(0.0, 1.0), np.finfo(float).max]],
        )


@pytest.mark.parametrize(
    "counts",
    [
        [[0, 0]],
        [[True, 1]],
        [[-1, 2]],
        [[1.5, 2]],
        [[float("nan"), 2]],
        [[float("inf"), 2]],
        [[2**53, 1]],
        [[2**52, 2**52]],
        [1, 2],
        [],
    ],
)
def test_invalid_counts_are_not_missing_pseudocounts_or_sampling_weights(
    counts: Any,
) -> None:
    with pytest.raises(ValidationError):
        fit(counts, np.ones(np.shape(counts)))


@pytest.mark.parametrize(
    "responses",
    [
        [[0, 1]],
        [[-1, 1]],
        [[True, 1]],
        [[float("nan"), 1]],
        [[float("inf"), 1]],
        [[1, 2, 3]],
        [1, 2],
    ],
)
def test_invalid_response_or_axis_refuses(responses: Any) -> None:
    with pytest.raises(ValidationError):
        fit([[1, 2]], responses)


@pytest.mark.parametrize(
    "measured",
    [
        [[False, True]],
        [[1, 1]],
        [True, True],
        np.ma.array([[True, True]], mask=[[True, False]]),
    ],
)
def test_unmeasured_or_masked_taxa_are_not_structural_zeros(measured: Any) -> None:
    with pytest.raises(ValidationError):
        fit_multisite_likelihood([[0, 2]], [[1, 2]], taxon_measured=measured)


def test_masked_counts_and_response_values_refuse_before_numpy_discards_masks() -> None:
    for counts, responses in (
        (np.ma.array([[0, 2]], mask=[[True, False]]), [[1, 2]]),
        ([[1, 2]], np.ma.array([[1, 2]], mask=[[True, False]])),
    ):
        with pytest.raises(ValidationError, match="masked"):
            fit(counts, responses)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_steps": True},
        {"max_steps": -1},
        {"score_tolerance": 0},
        {"score_tolerance": float("nan")},
        {"relative_count_tolerance": False},
        {"relative_count_tolerance": 0},
    ],
)
def test_invalid_convergence_controls_refuse(kwargs: Any) -> None:
    with pytest.raises(ValidationError):
        fit([[1, 2]], [[1, 2]], **kwargs)
