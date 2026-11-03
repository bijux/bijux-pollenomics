"""Analytical losses and matched finite-ensemble score populations."""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer import (
    predictions,
    scoring,
)

from .test_predictions import bind, candidate


def complete_candidate() -> dict[str, Any]:
    """Add retained reference forecasts to the established four-draw source toy."""
    source = candidate()
    # The common factor preserves all three nominal interpolation weights.
    source["case"]["distances_km"] = [400.0, 200.0]
    bind(source)
    for reference in source["cached_fit"]["methods"].values():
        reference["pollen"] = [[0.75, 0.25], [0.6, 0.4], [0.3, 0.7], [None, None]]
        reference["direct_pollen"] = [[0.6, 0.4], [0.5, 0.5], [0.4, 0.6], [0.2, 0.8]]
    return source


def test_analytic_closed_composition_losses_and_count_units() -> None:
    assert scoring.loss([0.5, 0.5], {"Betula": 2, "Ulmus": 2}) == {
        "mae_fraction": 0.0,
        "total_variation": 0.0,
        "hellinger": 0.0,
        "count_conditioned_deviance": 0.0,
        "zero_probability_positive_count": False,
    }
    values = scoring.loss([0.75, 0.25], {"Betula": 1, "Ulmus": 3})
    assert values["mae_fraction"] == values["total_variation"] == 0.5
    assert values["hellinger"] == pytest.approx(
        math.sqrt(1 - math.sqrt(3) / 2), abs=1e-15
    )
    assert values["count_conditioned_deviance"] == pytest.approx(4 * math.log(3))
    doubled = scoring.loss([0.75, 0.25], {"Betula": 2, "Ulmus": 6})
    for metric in scoring.METRICS:
        assert doubled[metric] == values[metric]
    assert doubled["count_conditioned_deviance"] == pytest.approx(
        2 * values["count_conditioned_deviance"]
    )


def test_impossible_count_loss_keeps_bounded_metrics_and_explicit_infinity() -> None:
    values = scoring.loss([1.0, 0.0], {"Betula": 1, "Ulmus": 1})
    assert values["mae_fraction"] == values["total_variation"] == 0.5
    assert values["hellinger"] == pytest.approx(math.sqrt(1 - 1 / math.sqrt(2)))
    assert values["count_conditioned_deviance"] is None
    assert values["zero_probability_positive_count"] is True
    result = scoring._series(
        [[1.0, 0.0], [0.5, 0.5], [None, None]],
        [True, True, False],
        {"Betula": 1, "Ulmus": 1},
    )
    assert result["rows"][0]["status"] == "scored"
    assert result["bounded_metric_summary"]["defined_replicates"] == 2
    assert result["count_deviance"] == {
        "impossible_positive_count_replicate_ids": [0],
        "conditional_mean_on_defined_predictions": None,
        "status": "infinite_positive_count_loss",
        "unconditional_status": "refused_incomplete_scoring_population_or_infinite_loss",
    }


def test_real_predictions_match_all_reference_channels_on_identical_draw_ids() -> None:
    source = complete_candidate()
    prediction = predictions.predict_candidate(source, length_scale_km=100.0)
    result = scoring.score_candidate(source, prediction, {"Betula": 2, "Ulmus": 8})
    assert result["observed_total_count"] == 10
    assert result["ensemble"]["bounded_metric_summary"]["total_replicates"] == 4
    assert result["ensemble"]["bounded_metric_summary"]["defined_replicates"] == 3
    assert result["ensemble"]["scoring_population"] == "candidate_defined_predictions"
    assert result["ensemble"]["rows"][3] == {
        "replicate_id": 3,
        "status": "undefined_prediction",
    }
    assert (
        result["scope"]
        == "one_geographic_target_block_conditional_working_law_not_field_coverage"
    )
    assert result["vegetation_accuracy"] == "not_evaluated_no_measured_observation"
    assert len(result["comparisons"]) == 6
    for row in result["comparisons"]:
        assert row["common_defined_replicate_ids"] == [0, 1, 2]
        assert row["excluded_replicates"] == 1
        assert (
            row["reference_scores"]["bounded_metric_summary"]["defined_replicates"] == 3
        )
        assert (
            row["reference_scores"]["scoring_population"]
            == "common_defined_comparison_replicates"
        )
        field = "pollen" if row["reference_channel"] == "physical" else "direct_pollen"
        reference = source["cached_fit"]["methods"][row["reference_method"]][field]
        expected = (
            math.fsum(
                abs(prediction["ensemble"]["pollen"][i][0] - 0.2)
                - abs(reference[i][0] - 0.2)
                for i in range(3)
            )
            / 3
        )
        assert row["model_minus_reference"]["conditional"]["mean"][0] == pytest.approx(
            expected, abs=1e-12
        )
        assert (
            row["model_minus_reference"]["unconditional_status"]
            == "refused_undefined_mass"
        )


def test_valid_direct_reference_draw_excluded_from_comparison_is_not_undefined() -> (
    None
):
    source = complete_candidate()
    counts = {"Betula": 2, "Ulmus": 8}
    prediction = predictions.predict_candidate(source, length_scale_km=100.0)
    result = scoring.score_candidate(source, prediction, counts)
    direct = [
        row
        for row in result["comparisons"]
        if row["reference_channel"] == "direct_pollen"
    ]
    assert len(direct) == 3
    for row in direct:
        reference = source["cached_fit"]["methods"][row["reference_method"]][
            "direct_pollen"
        ]
        assert len(reference) == 4 and all(
            all(isinstance(value, float) for value in vector) for vector in reference
        )
        assert scoring.loss(reference[3], counts)["count_conditioned_deviance"] == 0.0
        assert row["common_defined_replicate_ids"] == [0, 1, 2]
        assert row["reference_scores"]["rows"][3] == {
            "replicate_id": 3,
            "status": "excluded_from_common_comparison",
        }
        assert (
            row["reference_scores"]["scoring_population"]
            == "common_defined_comparison_replicates"
        )
        assert (
            row["reference_scores"]["count_deviance"]["unconditional_status"]
            == "refused_incomplete_scoring_population_or_infinite_loss"
        )
    assert result["ensemble"]["rows"][3]["status"] == "undefined_prediction"


def test_additional_forecast_refusal_narrows_every_paired_comparison() -> None:
    source = complete_candidate()
    prediction = predictions.predict_candidate(source, length_scale_km=100.0)
    prediction["ensemble"]["valid_mask"][1] = False
    prediction["ensemble"]["pollen"][1] = [None, None]
    result = scoring.score_candidate(source, prediction, {"Betula": 2, "Ulmus": 8})
    assert all(
        row["common_defined_replicate_ids"] == [0, 2]
        and row["excluded_replicates"] == 2
        for row in result["comparisons"]
    )
    assert result["ensemble"]["bounded_metric_summary"]["defined_replicates"] == 2


def test_held_label_changes_losses_without_changing_predictions_or_ancestry() -> None:
    source = complete_candidate()
    prediction = predictions.predict_candidate(source, length_scale_km=100.0)
    before = deepcopy(prediction)
    first = scoring.score_candidate(source, prediction, {"Betula": 2, "Ulmus": 8})
    second = scoring.score_candidate(source, prediction, {"Betula": 8, "Ulmus": 2})
    assert prediction == before
    assert first["nominal"] != second["nominal"]
    assert first["observed_total_count"] == second["observed_total_count"] == 10


def test_no_defined_prediction_retains_complete_unavailable_population() -> None:
    result = scoring._series(
        [[None, None], [None, None]], [False, False], {"Betula": 2, "Ulmus": 8}
    )
    assert [row["replicate_id"] for row in result["rows"]] == [0, 1]
    assert result["bounded_metric_summary"]["defined_replicates"] == 0
    assert result["count_deviance"]["status"] == "unavailable_no_defined_predictions"
    with pytest.raises(ValueError, match="Aligned score"):
        scoring._series([[0.5, 0.5]], cast(Any, [1]), {"Betula": 2, "Ulmus": 8})
