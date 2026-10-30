"""Analytic controls for population covariance and shared age/PPE interaction."""

from __future__ import annotations

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe.moments import (
    PopulationMoments,
    joint_window_moments,
    window_moments,
)


def test_two_age_control_requires_mean_quadratic_not_quadratic_mean() -> None:
    accumulator = PopulationMoments(np.eye(5))
    q = np.full(20, 0.2)
    for sign in (1.0, -1.0):
        gradient = np.zeros((20, 5))
        gradient[0, :2] = [1.0, sign]
        gradient[1, :2] = [-1.0, -sign]
        accumulator.add(q, np.zeros((20, 20)), gradient)
    result = accumulator.result()
    parts = result["covariance_components"]
    assert parts["shared_ppe"][0][0] == 2.0
    assert parts["mean_gradient_ppe"][0][0] == parts["age_ppe_interaction"][0][0] == 1.0
    assert len(result["contrasts"]) == 30


def test_population_denominator_and_zero_sd_isolate_age_count() -> None:
    accumulator = PopulationMoments(np.zeros((5, 5)))
    first = np.full(20, 0.2)
    second = first.copy()
    second[0:2] = [0.3, 0.1]
    count = np.zeros((20, 20))
    count[:2, :2] = [[0.01, -0.01], [-0.01, 0.01]]
    for q in (first, second):
        accumulator.add(q, count, np.zeros((20, 5)))
    result = accumulator.result()
    parts = result["covariance_components"]
    assert parts["age"][0][0] == pytest.approx(0.0025)
    assert parts["count"][0][0] == 0.01 and parts["total"][0][0] == pytest.approx(
        0.0125
    )
    assert np.count_nonzero(parts["shared_ppe"]) == 0


def test_single_age_matches_existing_conditional_physical_moments() -> None:
    covariance = np.diag([0.1, 0.2, 0.3, 0.4, 0.0]) ** 2
    ppe = np.array([2.0, 1.0, 3.0, 4.0, 1.0])
    deposition = np.array([0.2, 0.3, 0.4, 0.5, 0.6])
    window = window_moments((10, 20, 30, 40, 50), deposition, ppe, covariance)
    q, count, gradient = joint_window_moments([window] * 4)
    accumulator = PopulationMoments(covariance)
    accumulator.add(q, count, gradient)
    result = accumulator.result()
    parts = result["covariance_components"]
    np.testing.assert_allclose(
        parts["shared_ppe"], gradient @ covariance @ gradient.T, atol=1e-12, rtol=0
    )
    assert np.count_nonzero(parts["age"]) == 0
    assert np.max(np.abs(parts["age_ppe_interaction"])) <= 1e-12


def test_empty_complete_event_has_no_invented_moments() -> None:
    result = PopulationMoments(np.zeros((5, 5))).result()
    assert result["status"] == "refused_no_complete_draws" and result["mean"] is None
    assert len(result["contrasts"]) == 30 and all(
        r["status"] == "refused_no_complete_draws" for r in result["contrasts"]
    )
