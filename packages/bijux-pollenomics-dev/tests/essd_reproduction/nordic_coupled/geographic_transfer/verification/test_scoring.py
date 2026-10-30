"""Analytical bounded losses and retained impossible-count mass on cached IDs."""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer.verification import (
    audit_scoring,
)

from .test_projection import METHODS, miniature, summary

METRICS = ("mae_fraction", "total_variation", "hellinger")


def literal_loss(p: list[float], counts: dict[str, int]) -> dict[str, Any]:
    c = [counts["Betula"], counts["Ulmus"]]
    observed = [value / sum(c) for value in c]
    error = (
        sum(abs(first - second) for first, second in zip(p, observed, strict=True)) / 2
    )
    impossible = any(
        value > 0 and probability == 0 for value, probability in zip(c, p, strict=True)
    )
    return {
        "mae_fraction": error,
        "total_variation": error,
        "hellinger": math.sqrt(
            sum(
                (math.sqrt(first) - math.sqrt(second)) ** 2
                for first, second in zip(p, observed, strict=True)
            )
            / 2
        ),
        "count_conditioned_deviance": None
        if impossible
        else max(
            0.0,
            2
            * sum(
                value * math.log(value / (sum(c) * probability))
                for value, probability in zip(c, p, strict=True)
                if value > 0
            ),
        ),
        "zero_probability_positive_count": impossible,
    }


def literal_series(
    pollen: list[list[Any]],
    mask: list[bool],
    counts: dict[str, int],
    *,
    comparison: bool = False,
) -> dict[str, Any]:
    rows, bounded, impossible, finite = [], [], [], []
    for index, valid in enumerate(mask):
        if not valid:
            rows.append(
                {
                    "replicate_id": index,
                    "status": "excluded_from_common_comparison"
                    if comparison
                    else "undefined_prediction",
                }
            )
            bounded.append([None] * 3)
            continue
        loss = literal_loss(pollen[index], counts)
        rows.append({"replicate_id": index, "status": "scored", **loss})
        bounded.append([loss[name] for name in METRICS])
        if loss["zero_probability_positive_count"]:
            impossible.append(index)
        else:
            finite.append(loss["count_conditioned_deviance"])
    return {
        "rows": rows,
        "scoring_population": "common_defined_comparison_replicates"
        if comparison
        else "candidate_defined_predictions",
        "bounded_metric_axis": list(METRICS),
        "bounded_metric_summary": summary(bounded, mask),
        "count_deviance": {
            "impossible_positive_count_replicate_ids": impossible,
            "conditional_mean_on_defined_predictions": sum(finite) / len(finite)
            if finite and not impossible
            else None,
            "status": "infinite_positive_count_loss"
            if impossible
            else "finite_conditional_only"
            if finite
            else "unavailable_no_defined_predictions",
            "unconditional_status": "defined"
            if all(mask) and not impossible
            else "refused_incomplete_scoring_population_or_infinite_loss",
        },
    }


def scored_fixture(
    candidate: dict[str, Any], prediction: dict[str, Any], counts: dict[str, int]
) -> dict[str, Any]:
    mask, pollen = (
        prediction["ensemble"]["valid_mask"],
        prediction["ensemble"]["pollen"],
    )
    comparisons = []
    for method in METHODS:
        original = candidate["cached_fit"]["methods"][method]
        for channel in ("physical", "direct_pollen"):
            reference = (
                original["pollen"]
                if channel == "physical"
                else original["direct_pollen"]
            )
            reference_mask = (
                original["valid_mask"] if channel == "physical" else [True] * len(mask)
            )
            common = [
                first and second
                for first, second in zip(mask, reference_mask, strict=True)
            ]
            diffs = [
                [
                    literal_loss(first, counts)[metric]
                    - literal_loss(second, counts)[metric]
                    for metric in METRICS
                ]
                if keep
                else [None] * 3
                for first, second, keep in zip(pollen, reference, common, strict=True)
            ]
            comparisons.append(
                {
                    "reference_method": method,
                    "reference_channel": channel,
                    "common_defined_replicate_ids": [
                        index for index, keep in enumerate(common) if keep
                    ],
                    "excluded_replicates": len(mask) - sum(common),
                    "reference_scores": literal_series(
                        reference, common, counts, comparison=True
                    ),
                    "metric_axis": list(METRICS),
                    "model_minus_reference": summary(diffs, common),
                }
            )
    return {
        "case_id": prediction["case_id"],
        "target_id": prediction["target_id"],
        "length_scale_km": prediction["length_scale_km"],
        "observed_total_count": sum(counts.values()),
        "observed_counts": counts,
        "nominal": literal_loss(prediction["nominal"]["pollen"], counts)
        if prediction["nominal"]["status"] == "predicted"
        else {"status": "refused", "refusal": prediction["nominal"]["refusal"]},
        "ensemble": literal_series(pollen, mask, counts),
        "comparisons": comparisons,
        "vegetation_accuracy": "not_evaluated_no_measured_observation",
        "scope": "one_geographic_target_block_conditional_working_law_not_field_coverage",
    }


def test_analytic_losses_and_six_exact_common_id_comparisons() -> None:
    candidate, prediction = miniature()
    counts = {"Betula": 1, "Ulmus": 1}
    scored = scored_fixture(candidate, prediction, counts)
    facts = audit_scoring(candidate, prediction, scored, counts)
    assert facts["comparisons_verified"] == 6
    assert facts["common_replicate_counts"] == [3] * 6
    assert scored["nominal"]["mae_fraction"] == pytest.approx(1 / 3)
    assert scored["nominal"]["count_conditioned_deviance"] == pytest.approx(
        -2 * math.log(5 / 9)
    )
    assert all(
        scored["comparisons"][index]["model_minus_reference"]["conditional"]["mean"]
        == [0.0] * 3
        for index in (0, 2, 4)
    )


def test_impossible_counts_keep_all_bounded_scores_but_refuse_finite_deviance_mean() -> (
    None
):
    candidate, prediction = miniature()
    prediction["nominal"]["pollen"] = [1.0, 0.0]
    prediction["ensemble"]["pollen"] = [
        [1.0, 0.0] if keep else [None, None]
        for keep in prediction["ensemble"]["valid_mask"]
    ]
    counts = {"Betula": 0, "Ulmus": 5}
    scored = scored_fixture(candidate, prediction, counts)
    facts = audit_scoring(candidate, prediction, scored, counts)
    assert facts["impossible_positive_count_rows"] == 3
    assert scored["ensemble"]["bounded_metric_summary"]["defined_replicates"] == 3
    assert scored["ensemble"]["bounded_metric_summary"]["conditional"]["mean"] == [
        1.0,
        1.0,
        1.0,
    ]
    assert (
        scored["ensemble"]["count_deviance"]["conditional_mean_on_defined_predictions"]
        is None
    )
    assert (
        scored["ensemble"]["count_deviance"]["status"] == "infinite_positive_count_loss"
    )
    assert scored["ensemble"]["count_deviance"][
        "impossible_positive_count_replicate_ids"
    ] == [0, 2, 3]


def test_zero_observed_taxon_uses_no_pseudocount_or_log_zero() -> None:
    candidate, prediction = miniature()
    prediction["nominal"]["pollen"] = [0.0, 1.0]
    prediction["ensemble"]["pollen"] = [
        [0.0, 1.0] if keep else [None, None]
        for keep in prediction["ensemble"]["valid_mask"]
    ]
    counts = {"Betula": 0, "Ulmus": 5}
    scored = scored_fixture(candidate, prediction, counts)
    assert (
        audit_scoring(candidate, prediction, scored, counts)[
            "impossible_positive_count_rows"
        ]
        == 0
    )
    assert scored["nominal"]["count_conditioned_deviance"] == 0


@pytest.mark.parametrize(
    "defect",
    [
        "row_id",
        "missing_row",
        "rescued_row",
        "loss",
        "deviance",
        "count_N",
        "common_ids",
        "excluded",
        "reference_row",
        "difference",
        "covariance",
        "mcse",
    ],
)
def test_row_masks_denominators_and_matched_conditional_summaries_are_bound(
    defect: str,
) -> None:
    candidate, prediction = miniature()
    counts = {"Betula": 1, "Ulmus": 1}
    scored = scored_fixture(candidate, prediction, counts)
    if defect == "row_id":
        scored["ensemble"]["rows"][0]["replicate_id"] = 2
    elif defect == "missing_row":
        scored["ensemble"]["rows"].pop()
    elif defect == "rescued_row":
        scored["ensemble"]["rows"][1]["status"] = "scored"
    elif defect == "loss":
        scored["ensemble"]["rows"][0]["hellinger"] = 0.0
    elif defect == "deviance":
        scored["ensemble"]["count_deviance"][
            "conditional_mean_on_defined_predictions"
        ] = 0.0
    elif defect == "count_N":
        scored["observed_total_count"] = 3
    elif defect == "common_ids":
        scored["comparisons"][0]["common_defined_replicate_ids"] = [0, 1, 2, 3]
    elif defect == "excluded":
        scored["comparisons"][0]["excluded_replicates"] = 0
    elif defect == "reference_row":
        scored["comparisons"][0]["reference_scores"]["rows"][0]["replicate_id"] = 1
    elif defect == "difference":
        scored["comparisons"][1]["model_minus_reference"]["conditional"]["mean"] = [
            0.0
        ] * 3
    elif defect == "covariance":
        scored["ensemble"]["bounded_metric_summary"]["conditional"]["covariance"][0][
            0
        ] = 0.0
    else:
        scored["ensemble"]["bounded_metric_summary"]["conditional"]["mean_mcse"] = [
            0.0
        ] * 3
    with pytest.raises(ValueError):
        audit_scoring(candidate, prediction, scored, counts)


@pytest.mark.parametrize(
    "counts",
    [
        {"Betula": True, "Ulmus": 1},
        {"Betula": 0, "Ulmus": 0},
        {"Betula": 1.0, "Ulmus": 1},
        {"Betula": 1},
    ],
)
def test_invalid_count_axes_totals_and_native_integer_types_refuse(
    counts: dict[str, Any],
) -> None:
    candidate, prediction = miniature()
    with pytest.raises(ValueError):
        audit_scoring(candidate, prediction, {}, counts)


def test_all_1024_score_ids_and_164_undefined_rows_remain_visible() -> None:
    candidate, prediction = miniature(
        1024, mask=[index >= 164 for index in range(1024)]
    )
    counts = {"Betula": 1, "Ulmus": 1}
    scored = scored_fixture(candidate, prediction, counts)
    facts = audit_scoring(candidate, prediction, scored, counts)
    assert facts["score_rows_verified"] == 1024
    assert facts["defined_prediction_rows"] == 860
    assert facts["common_replicate_counts"] == [860] * 6
    assert scored["ensemble"]["scoring_population"] == "candidate_defined_predictions"
    assert all(
        row["status"] == "undefined_prediction"
        for row in scored["ensemble"]["rows"][:164]
    )
    for comparison in scored["comparisons"]:
        series = comparison["reference_scores"]
        assert series["scoring_population"] == "common_defined_comparison_replicates"
        assert all(
            row["status"] == "excluded_from_common_comparison"
            for row in series["rows"][:164]
        )
        assert series["bounded_metric_summary"]["defined_replicates"] == 860
        if comparison["reference_channel"] == "direct_pollen":
            original = candidate["cached_fit"]["methods"][
                comparison["reference_method"]
            ]["direct_pollen"]
            assert len(original) == 1024 and all(
                all(value is not None for value in row) for row in original
            )


def test_defined_direct_reference_exclusion_cannot_be_relabelled_prediction_failure() -> (
    None
):
    candidate, prediction = miniature()
    counts = {"Betula": 1, "Ulmus": 1}
    scored = scored_fixture(candidate, prediction, counts)
    direct = next(
        row
        for row in scored["comparisons"]
        if row["reference_channel"] == "direct_pollen"
    )
    assert candidate["cached_fit"]["methods"][METHODS[0]]["direct_pollen"][1] == [
        0.5,
        0.5,
    ]
    assert (
        direct["reference_scores"]["rows"][1]["status"]
        == "excluded_from_common_comparison"
    )
    direct["reference_scores"]["rows"][1]["status"] = "undefined_prediction"
    with pytest.raises(ValueError):
        audit_scoring(candidate, prediction, scored, counts)


def test_impossible_flag_and_infinite_mean_cannot_be_relabelled_finite() -> None:
    candidate, prediction = miniature(1, mask=[True])
    prediction["nominal"]["pollen"] = [1.0, 0.0]
    prediction["ensemble"]["pollen"] = [[1.0, 0.0]]
    counts = {"Betula": 0, "Ulmus": 1}
    scored = scored_fixture(candidate, prediction, counts)
    for defect in ("flag", "finite_mean"):
        broken = deepcopy(scored)
        if defect == "flag":
            broken["ensemble"]["rows"][0]["zero_probability_positive_count"] = False
        else:
            broken["ensemble"]["count_deviance"][
                "conditional_mean_on_defined_predictions"
            ] = 0.0
        with pytest.raises(ValueError):
            audit_scoring(candidate, prediction, broken, counts)
