"""Independent bounded losses, impossible-count flags and common-row contrasts."""

from __future__ import annotations

import math
from typing import Any

from ...predictive_uncertainty.verification.summaries import ensemble_summary
from .projection import METHODS, _compare, _pair, _require

AXIS = ("Betula", "Ulmus")
METRICS = ("mae_fraction", "total_variation", "hellinger")


def _loss(pollen: list[float], counts: dict[str, int]) -> dict[str, Any]:
    _pair(pollen, closed=True)
    total = sum(counts.values())
    truth = [counts[taxon] / total for taxon in AXIS]
    absolute = math.fsum(
        abs(first - second) for first, second in zip(pollen, truth, strict=True)
    )
    differences = [
        (first - second) / (math.sqrt(first) + math.sqrt(second))
        if first or second
        else 0.0
        for first, second in zip(pollen, truth, strict=True)
    ]
    impossible = any(
        counts[taxon] > 0 and pollen[index] == 0 for index, taxon in enumerate(AXIS)
    )
    deviance = (
        None
        if impossible
        else max(
            0.0,
            2
            * math.fsum(
                counts[taxon]
                * (math.log(counts[taxon] / total) - math.log(pollen[index]))
                for index, taxon in enumerate(AXIS)
                if counts[taxon] > 0
            ),
        )
    )
    return {
        "mae_fraction": absolute / 2,
        "total_variation": absolute / 2,
        "hellinger": math.hypot(*differences) / math.sqrt(2),
        "count_conditioned_deviance": deviance,
        "zero_probability_positive_count": impossible,
    }


def _series(
    pollen: list[list[Any]],
    mask: list[bool],
    counts: dict[str, int],
    *,
    comparison: bool = False,
) -> dict[str, Any]:
    _require(
        len(pollen) == len(mask) and all(type(value) is bool for value in mask),
        "complete score row/mask axis",
    )
    rows, bounded, impossible, deviances = [], [], [], []
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
            bounded.append([None, None, None])
            continue
        score = _loss(pollen[index], counts)
        rows.append({"replicate_id": index, "status": "scored", **score})
        bounded.append([score[name] for name in METRICS])
        if score["zero_probability_positive_count"]:
            impossible.append(index)
        else:
            deviances.append(score["count_conditioned_deviance"])
    return {
        "rows": rows,
        "scoring_population": "common_defined_comparison_replicates"
        if comparison
        else "candidate_defined_predictions",
        "bounded_metric_axis": list(METRICS),
        "bounded_metric_summary": ensemble_summary(bounded, mask),
        "count_deviance": {
            "impossible_positive_count_replicate_ids": impossible,
            "conditional_mean_on_defined_predictions": math.fsum(deviances)
            / len(deviances)
            if deviances and not impossible
            else None,
            "status": "infinite_positive_count_loss"
            if impossible
            else "finite_conditional_only"
            if deviances
            else "unavailable_no_defined_predictions",
            "unconditional_status": "defined"
            if all(mask) and not impossible
            else "refused_incomplete_scoring_population_or_infinite_loss",
        },
    }


def audit_scoring(
    candidate: dict[str, Any],
    prediction: dict[str, Any],
    scored: dict[str, Any],
    counts: dict[str, int],
) -> dict[str, Any]:
    """Check all finite losses even when an impossible count makes deviance infinite."""
    _require(
        set(counts) == set(AXIS)
        and all(type(value) is int and value >= 0 for value in counts.values())
        and 0 < sum(counts.values()) <= 2**53,
        "literal source-bound positive count denominator",
    )
    case = candidate["case"]
    _require(
        prediction["case_id"] == case["case_id"]
        and prediction["target_id"] == case["target_id"],
        "score case/target source",
    )
    count = prediction["replicates"]
    mask = prediction["ensemble"]["valid_mask"]
    _require(
        type(count) is int
        and count > 0
        and len(mask) == count
        and all(type(value) is bool for value in mask),
        "complete score replicate population",
    )
    pollen = prediction["ensemble"]["pollen"]
    nominal = (
        _loss(prediction["nominal"]["pollen"], counts)
        if prediction["nominal"]["status"] == "predicted"
        else {"status": "refused", "refusal": prediction["nominal"]["refusal"]}
    )
    comparisons = []
    for method in METHODS:
        reference = candidate["cached_fit"]["methods"][method]
        for channel in ("physical", "direct_pollen"):
            reference_mask = (
                reference["valid_mask"] if channel == "physical" else [True] * count
            )
            values = (
                reference["pollen"]
                if channel == "physical"
                else reference["direct_pollen"]
            )
            _require(
                len(reference_mask) == len(values) == count
                and all(type(value) is bool for value in reference_mask),
                "complete reference source rows",
            )
            common = [
                bool(first and second)
                for first, second in zip(mask, reference_mask, strict=True)
            ]
            ids = [index for index, valid in enumerate(common) if valid]
            differences = []
            for index, valid in enumerate(common):
                if not valid:
                    differences.append([None, None, None])
                    continue
                first, second = (
                    _loss(pollen[index], counts),
                    _loss(values[index], counts),
                )
                differences.append(
                    [first[metric] - second[metric] for metric in METRICS]
                )
            comparisons.append(
                {
                    "reference_method": method,
                    "reference_channel": channel,
                    "common_defined_replicate_ids": ids,
                    "excluded_replicates": count - len(ids),
                    "reference_scores": _series(
                        values, common, counts, comparison=True
                    ),
                    "metric_axis": list(METRICS),
                    "model_minus_reference": ensemble_summary(differences, common),
                }
            )
    expected = {
        "case_id": case["case_id"],
        "target_id": case["target_id"],
        "length_scale_km": prediction["length_scale_km"],
        "observed_total_count": sum(counts.values()),
        "observed_counts": dict(counts),
        "nominal": nominal,
        "ensemble": _series(pollen, mask, counts),
        "comparisons": comparisons,
        "vegetation_accuracy": "not_evaluated_no_measured_observation",
        "scope": "one_geographic_target_block_conditional_working_law_not_field_coverage",
    }
    _compare(scored, expected)
    return {
        "status": "passed",
        "score_rows_verified": count,
        "defined_prediction_rows": sum(mask),
        "impossible_positive_count_rows": len(
            expected["ensemble"]["count_deviance"][
                "impossible_positive_count_replicate_ids"
            ]
        ),
        "comparisons_verified": len(comparisons),
        "common_replicate_counts": [
            len(row["common_defined_replicate_ids"]) for row in comparisons
        ],
        "scope": "One source-bound pooled observation and conditional training-draw law, not independent field replicates or calibrated predictive coverage",
    }
