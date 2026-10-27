"""Scalar finite-ensemble moments and explicitly conditional MC error."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
from typing import Any

from .algebra import finite, require

MCSE_SCOPE = "IID conditional working-law expectation, not exact finite-ensemble mean error or field uncertainty"


def linear_quantile(values: Sequence[float], probability: float) -> float:
    require(bool(values) and 0 <= probability <= 1, "quantile population/domain")
    ordered = sorted(values)
    location = (len(ordered) - 1) * probability
    lower, upper = math.floor(location), math.ceil(location)
    return ordered[lower] + (location - lower) * (ordered[upper] - ordered[lower])


def ensemble_summary(
    samples: Sequence[Sequence[object]], valid_mask: Sequence[bool]
) -> dict[str, Any]:
    """Use the named complete-case event, retaining its empirical mass."""
    require(bool(samples) and len(samples) == len(valid_mask), "nonempty ensemble/mask")
    require(all(type(value) is bool for value in valid_mask), "strict validity mask")
    dimension = len(samples[0])
    require(
        dimension > 0 and all(len(row) == dimension for row in samples),
        "ensemble dimensions",
    )
    valid = [
        [finite(value) for value in row]
        for row, keep in zip(samples, valid_mask, strict=True)
        if keep
    ]
    count, total = len(valid), len(samples)
    if count:
        mean = [
            math.fsum(row[index] for row in valid) / count for index in range(dimension)
        ]
        sums = [
            [
                math.fsum(
                    (row[first] - mean[first]) * (row[second] - mean[second])
                    for row in valid
                )
                for second in range(dimension)
            ]
            for first in range(dimension)
        ]
        covariance = [[value / count for value in row] for row in sums]
        conditional: dict[str, Any] = {
            "status": "defined",
            "mean": mean,
            "covariance": covariance,
            "sd": [
                math.sqrt(max(0, covariance[index][index]))
                for index in range(dimension)
            ],
            "empirical_quantiles": {
                str(probability): [
                    linear_quantile([row[index] for row in valid], probability)
                    for index in range(dimension)
                ]
                for probability in (0.025, 0.5, 0.975)
            },
            "mean_mcse": [
                math.sqrt(max(0, sums[index][index] / (count * (count - 1))))
                for index in range(dimension)
            ]
            if count >= 2
            else None,
            "mean_mcse_status": "estimated_iid_conditional_expectation"
            if count >= 2
            else "unavailable_fewer_than_two_defined",
        }
    else:
        conditional = {
            "status": "unavailable_no_defined_replicates",
            "mean": None,
            "covariance": None,
            "sd": None,
            "empirical_quantiles": None,
            "mean_mcse": None,
            "mean_mcse_status": "unavailable_fewer_than_two_defined",
        }
    return {
        "total_replicates": total,
        "defined_replicates": count,
        "undefined_replicates": total - count,
        "undefined_mass": (total - count) / total,
        "unconditional_status": "defined"
        if count == total
        else "refused_undefined_mass",
        "conditional": conditional,
        "covariance_divisor": "defined_replicates",
        "quantile_method": "linear",
        "mcse_scope": MCSE_SCOPE,
    }


def losses(prediction: Sequence[object], observed: Sequence[object]) -> list[float]:
    p, o = (
        [finite(value) for value in prediction],
        [finite(value) for value in observed],
    )
    require(len(p) == len(o) == 2 and min(p + o) >= 0, "score composition axis/domain")
    error = math.fsum(abs(p[index] - o[index]) for index in range(2)) / 2
    hellinger = math.sqrt(
        math.fsum(
            (math.sqrt(p[index]) - math.sqrt(o[index])) ** 2 for index in range(2)
        )
        / 2
    )
    return [error, error, hellinger]


def matched_summaries(
    physical: Sequence[Sequence[object]],
    direct: Sequence[Sequence[object]],
    mask: Sequence[bool],
    *,
    include_all_direct: bool,
) -> dict[str, Any]:
    require(len(physical) == len(direct) == len(mask), "matched replicate membership")
    differences = [
        [finite(p) - finite(d) for p, d in zip(first, second, strict=True)]
        if keep
        else [None] * len(first)
        for first, second, keep in zip(physical, direct, mask, strict=True)
    ]
    result = {
        "physical": ensemble_summary(physical, mask),
        "direct_on_physical_defined": ensemble_summary(direct, mask),
        "physical_minus_direct": ensemble_summary(differences, mask),
    }
    if include_all_direct:
        result["direct_all_replicates"] = ensemble_summary(direct, [True] * len(mask))
    return result


def reference_summaries(
    predictions: Sequence[Mapping[str, Any]],
    observed: Sequence[Mapping[str, Any]],
    outcome_access: Mapping[str, Any],
) -> dict[str, Any]:
    """Rebuild common-event covariance and equal-target losses without pairwise deletion."""
    from .algebra import METHODS

    cases = sorted(predictions, key=lambda row: row["case_id"])
    case_ids = [row["case_id"] for row in cases]
    require(len(cases) == len(set(case_ids)) == 3, "three distinct target cases")
    truths = {row["case_id"]: row["pollen_fraction"] for row in observed}
    require(set(truths) == set(case_ids) and len(observed) == 3, "three score outcomes")
    total = cases[0]["replicates"]
    joint, aggregate, scores = {}, {}, []
    for method in METHODS:
        mask = [
            all(row["methods"][method]["valid_mask"][index] for row in cases)
            for index in range(total)
        ]
        physical = [
            [
                value
                for row in cases
                for value in row["methods"][method]["pollen"][index]
            ]
            for index in range(total)
        ]
        direct = [
            [
                value
                for row in cases
                for value in row["methods"][method]["direct_pollen"][index]
            ]
            for index in range(total)
        ]
        joint[method] = {
            "case_ids": case_ids,
            **matched_summaries(physical, direct, mask, include_all_direct=True),
        }
        physical_losses, direct_losses = [], []
        for row in cases:
            value = row["methods"][method]
            local_mask = value["valid_mask"]
            first = [
                losses(p, truths[row["case_id"]]) if keep else [None] * 3
                for p, keep in zip(value["pollen"], local_mask, strict=True)
            ]
            second = [losses(p, truths[row["case_id"]]) for p in value["direct_pollen"]]
            physical_losses.append(first)
            direct_losses.append(second)
            scores.append(
                {
                    "case_id": row["case_id"],
                    "method": method,
                    **matched_summaries(
                        first, second, local_mask, include_all_direct=True
                    ),
                }
            )
        average_physical = [
            [
                math.fsum(
                    finite(physical_losses[case][index][metric]) for case in range(3)
                )
                / 3
                for metric in range(3)
            ]
            if keep
            else [None] * 3
            for index, keep in enumerate(mask)
        ]
        average_direct = [
            [
                math.fsum(
                    finite(direct_losses[case][index][metric]) for case in range(3)
                )
                / 3
                for metric in range(3)
            ]
            for index in range(total)
        ]
        aggregate[method] = {
            "case_ids": case_ids,
            **matched_summaries(
                average_physical, average_direct, mask, include_all_direct=False
            ),
        }
    scores.sort(key=lambda row: (row["case_id"], METHODS.index(row["method"])))
    return {
        "schema_version": "coupled-pollen-bootstrap-summary.v1",
        "joint_predictions": joint,
        "score_diagnostics": {
            "observed": list(observed),
            "cases": scores,
            "aggregate": aggregate,
        },
        "outcome_access": dict(outcome_access),
    }
