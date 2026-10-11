"""Independent discrete probability, joint dependence and rejection cases."""

from __future__ import annotations

from math import comb
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_lra import ValidationError, sample_pollen_observations


def run(**changes: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "effort": 4,
        "repeats": 100,
        "seed": 8,
        "coverage": 0.5,
        "prediction_sha256": "a" * 64,
        "effort_evidence_sha256": "b" * 64,
    }
    kwargs.update(changes)
    return sample_pollen_observations({"a": 0.5, "b": 0.5}, **kwargs).as_dict()


def test_exact_discrete_bounds_agree_with_enumerated_binomial() -> None:
    result = run()
    intervals = result["marginal_predictive_intervals"]
    # With n=4, p=.5, CDF(0)=1/16 and CDF(1)=5/16.
    assert intervals["a"] == {
        "lower_count": 1,
        "upper_count": 3,
        "lower_fraction": 0.25,
        "upper_fraction": 0.75,
    }
    coverage = sum(comb(4, k) / 16 for k in range(1, 4))
    assert coverage == 0.875 and coverage >= result["declaration"]["coverage"]
    assert result["interval_kind"] == "conditional_predictive_observation"
    assert result["propagated_sources"] == ["observation_process"]
    assert not result["simultaneous_coverage_claimed"]
    assert not result["empirical_coverage_verified"]
    assert "PPE" in result["not_propagated"]


def test_joint_rows_preserve_effort_and_negative_taxon_covariance() -> None:
    result = run(effort=20, repeats=10000)
    draws = np.asarray(result["counts"])
    assert np.all(draws.sum(axis=1) == 20)
    # Analytic Var(X)=np(1-p)=5 and Cov(X,Y)=-5; 10000 draws, generous fixed bound.
    covariance = np.cov(draws.T, ddof=1)
    assert abs(covariance[0, 0] - 5) < 0.3
    assert abs(covariance[0, 1] + 5) < 0.3
    assert abs(draws[:, 0].mean() - 10) < 0.15
    assert len(set(result["draw_ids"])) == 10000


def test_degenerate_probability_has_exact_count_and_interval() -> None:
    result = sample_pollen_observations(
        {"zero": 0.0, "certain": 1.0},
        effort=7,
        repeats=2,
        seed=0,
        coverage=0.95,
        prediction_sha256="a" * 64,
        effort_evidence_sha256="b" * 64,
    ).as_dict()
    assert result["counts"] == [[7, 0], [7, 0]]
    assert result["marginal_predictive_intervals"]["zero"]["upper_count"] == 0
    assert result["marginal_predictive_intervals"]["certain"]["lower_count"] == 7


def test_repeatability_input_permutation_and_no_mutation() -> None:
    kwargs: dict[str, Any] = {
        "effort": 100,
        "repeats": 10,
        "seed": 42,
        "coverage": 0.9,
        "prediction_sha256": "a" * 64,
        "effort_evidence_sha256": "b" * 64,
    }
    values = {"b": 0.3, "a": 0.2, "c": 0.5}
    original = dict(values)
    one = sample_pollen_observations(values, **kwargs)
    two = sample_pollen_observations(dict(reversed(list(values.items()))), **kwargs)
    assert one == two and values == original
    assert one.as_dict()["declaration"]["effective_pollen_fraction"] == {
        "a": 0.2,
        "b": 0.3,
        "c": 0.5,
    }


def test_roundoff_closure_is_explicit_and_preserves_input() -> None:
    values = {"a": 0.4, "b": 0.6000000000005}
    result = sample_pollen_observations(
        values,
        effort=10,
        repeats=2,
        seed=0,
        coverage=0.9,
        prediction_sha256="a" * 64,
        effort_evidence_sha256="b" * 64,
    ).as_dict()
    declaration = result["declaration"]
    assert declaration["input_pollen_fraction"] == values
    assert declaration["effective_pollen_fraction"] != values
    assert declaration["closure_profile"] == "binary64-normalize-largest-residual-v1"


@pytest.mark.parametrize(
    "changes",
    [
        {"effort": True},
        {"effort": "4"},
        {"effort": 4.0},
        {"effort": 0},
        {"effort": 2**31},
        {"repeats": 1},
        {"repeats": 10001},
        {"seed": -1},
        {"seed": True},
        {"coverage": True},
        {"coverage": float("nan")},
        {"coverage": 0},
        {"coverage": 1},
        {"prediction_sha256": "unknown"},
        {"effort_evidence_sha256": "a" * 63},
    ],
)
def test_malformed_configuration_refuses(changes: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        run(**changes)


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"a": True, "b": 0.0},
        {"a": ".5", "b": 0.5},
        {"a": -0.1, "b": 1.1},
        {"a": 50.0, "b": 50.0},
        {"a": float("inf")},
        {" a": 1.0},
        {"a": 0.1, "b": 0.8},
        {1: 1.0},
    ],
)
def test_incompatible_probabilities_refuse(values: Any) -> None:
    with pytest.raises(ValidationError):
        sample_pollen_observations(
            values,
            effort=10,
            repeats=2,
            seed=0,
            coverage=0.9,
            prediction_sha256="a" * 64,
            effort_evidence_sha256="b" * 64,
        )


def test_effort_and_prediction_identity_change_draw_parent_identity() -> None:
    base = run()
    other = run(effort_evidence_sha256="c" * 64)
    assert base["counts"] == other["counts"]
    assert base["draw_ids"] != other["draw_ids"]
    assert (
        base["declaration_sha256"]
        != run(prediction_sha256="d" * 64)["declaration_sha256"]
    )


@pytest.mark.parametrize(
    "effort,p,coverage,lower", [(2, 0.75, 0.125, 1), (9, 0.875, 0.8162185549736023, 6)]
)
def test_exact_probability_ties_do_not_shift_count_quantile(
    effort: int, p: float, coverage: float, lower: int
) -> None:
    result = sample_pollen_observations(
        {"a": p, "b": 1 - p},
        effort=effort,
        repeats=2,
        seed=0,
        coverage=coverage,
        prediction_sha256="a" * 64,
        effort_evidence_sha256="b" * 64,
    ).as_dict()
    assert result["marginal_predictive_intervals"]["a"]["lower_count"] == lower
    assert result["interval_numeric_profile"] == "exact-rational-boundary-v1"


def test_huge_numeric_inputs_refuse_without_overflow_exception() -> None:
    with pytest.raises(ValidationError):
        run(coverage=10**1000)
    with pytest.raises(ValidationError):
        sample_pollen_observations(
            {"a": 10**1000},
            effort=10,
            repeats=2,
            seed=0,
            coverage=0.9,
            prediction_sha256="a" * 64,
            effort_evidence_sha256="b" * 64,
        )


def test_large_support_with_separated_probability_boundaries() -> None:
    result = run(effort=1000, repeats=2, coverage=0.9)
    assert result["interval_numeric_profile"] == "scipy-cdf-separated-boundary-v1"
