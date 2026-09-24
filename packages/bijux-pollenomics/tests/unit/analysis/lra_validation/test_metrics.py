"""Separate vegetation/pollen denominators, zeros and invalid analytical outputs."""

import json
from math import log, sqrt
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    ValidationRefusal,
    score_pollen,
    score_vegetation,
)
from bijux_pollenomics.analysis.lra_validation.metrics import hellinger_distance


def test_vegetation_fraction_metrics_have_explicit_taxon_denominator() -> None:
    score = score_vegetation({"tree": 0.8, "grass": 0.2}, {"tree": 0.6, "grass": 0.4})
    assert score.target == "vegetation_cover"
    assert score.status == "scored"
    assert score.mae_fraction == pytest.approx(0.2)
    assert score.rmse_fraction == pytest.approx(0.2)
    assert score.bias_fraction == pytest.approx(0)
    assert score.total_variation == pytest.approx(0.2)
    assert score.scored_taxon_count == 2


def test_missing_vegetation_never_becomes_zero_or_a_pollen_score() -> None:
    cover = {"tree": 1.0, "grass": 0.0}
    missing = score_vegetation(cover, {"tree": None, "grass": 0.0})
    zero = score_vegetation(cover, {"tree": 0.0, "grass": 1.0})
    pollen = score_pollen(cover, {"tree": 10, "grass": 0})
    assert missing.status == "missing_observation"
    assert missing.missing_observed_taxa == ("tree",)
    assert missing.mae_fraction is None and missing.scored_taxon_count == 0
    assert zero.mae_fraction == 1.0
    assert pollen.target == "pollen_composition" and pollen.mae_fraction == 0


@pytest.mark.parametrize(
    "predicted",
    [
        {"tree": -0.2, "grass": 1.2},
        {"tree": 0.2, "grass": 0.2},
        {"tree": float("nan"), "grass": 0.2},
        {"tree": True, "grass": 0},
    ],
)
def test_invalid_or_negative_analytical_love_is_not_clipped(
    predicted: dict[str, float],
) -> None:
    with pytest.raises(ValidationRefusal):
        score_vegetation(predicted, {"tree": 0.8, "grass": 0.2})


def test_absent_taxon_is_not_imputed_zero() -> None:
    with pytest.raises(ValidationRefusal) as error:
        score_vegetation({"tree": 1.0, "grass": 0}, {"tree": 1.0})
    assert error.value.reason_code == "taxon_denominator_mismatch"


def test_pollen_count_conditioned_deviance_uses_natural_log_no_pseudocounts() -> None:
    score = score_pollen({"tree": 0.25, "grass": 0.75}, {"tree": 5, "grass": 5})
    assert score.count_conditioned_deviance == pytest.approx(
        2 * (5 * log(2) + 5 * log(2 / 3))
    )
    assert score.observed_total_count == 10
    assert score.mae_fraction == 0.25


def test_impossible_pollen_prediction_has_explicit_json_safe_failure() -> None:
    score = score_pollen({"tree": 1.0, "grass": 0.0}, {"tree": 9, "grass": 1})
    assert score.zero_probability_positive_count
    assert score.count_conditioned_deviance is None
    json.dumps(score.as_dict(), allow_nan=False)


def test_zero_count_is_not_missing_and_zero_total_is_unscorable() -> None:
    prediction = {"tree": 1.0, "grass": 0.0}
    assert (
        score_pollen(prediction, {"tree": 10, "grass": 0}).count_conditioned_deviance
        == 0
    )
    empty = score_pollen(prediction, {"tree": 0, "grass": 0})
    assert empty.status == "zero_total_count" and empty.observed_total_count == 0
    assert (
        score_pollen(prediction, {"tree": 10, "grass": None}).status
        == "missing_observation"
    )


@pytest.mark.parametrize("count", [-1, True, 0.5, float("inf")])
def test_non_count_units_are_refused(count: Any) -> None:
    with pytest.raises(ValidationRefusal):
        score_pollen({"tree": 1.0}, {"tree": count})


def test_extremely_small_positive_probability_has_finite_deviance() -> None:
    score = score_pollen({"tree": 5e-324, "grass": 1.0}, {"tree": 1, "grass": 0})
    assert score.count_conditioned_deviance == pytest.approx(-2 * log(5e-324))
    assert not score.zero_probability_positive_count
    json.dumps(score.as_dict(), allow_nan=False)


def test_imprecise_count_total_and_unrepresentable_fractions_refuse() -> None:
    with pytest.raises(ValidationRefusal, match="exact binary64 integer"):
        score_pollen({"tree": 1.0}, {"tree": 2**53 + 1})
    with pytest.raises(ValidationRefusal, match="binary64 range"):
        score_vegetation({"tree": 10**1000}, {"tree": 1.0})


def test_signed_errors_remain_available_by_taxon_for_cohort_bias() -> None:
    score = score_vegetation({"tree": 0.8, "grass": 0.2}, {"tree": 0.6, "grass": 0.4})
    assert dict(score.signed_error_by_taxon) == pytest.approx(
        {"tree": 0.2, "grass": -0.2}
    )


def test_hellinger_distance_has_closed_composition_endpoints() -> None:
    assert hellinger_distance({"tree": 1, "grass": 0}, {"tree": 1, "grass": 0}) == 0
    assert hellinger_distance({"tree": 1, "grass": 0}, {"tree": 0, "grass": 1}) == 1
    assert hellinger_distance(
        {"tree": 1, "grass": 0}, {"tree": 0.5, "grass": 0.5}
    ) == pytest.approx(sqrt(1 - 1 / sqrt(2)))
    with pytest.raises(ValidationRefusal, match="taxon keys must match"):
        hellinger_distance({"tree": 1}, {"grass": 1})
