"""Independent postfreeze losses, matched comparisons and target denominators."""

from __future__ import annotations

from decimal import Decimal, localcontext
import math
import re
from typing import Any

from .predictions import BASELINES, METHODS, contexts, number, require, same

METRICS = ("mae_fraction", "total_variation", "hellinger")
HELLINGER = ("hellinger_20km", "hellinger_100km")


def _close(actual: Any, expected: Any) -> None:
    if isinstance(expected, dict):
        require(
            type(actual) is dict and actual.keys() == expected.keys(),
            "closed loss fields",
        )
        for key in expected:
            _close(actual[key], expected[key])
    elif isinstance(expected, list):
        require(
            type(actual) is list and len(actual) == len(expected),
            "complete loss population",
        )
        for first, second in zip(actual, expected, strict=True):
            _close(first, second)
    elif isinstance(expected, float):
        require(
            abs(number(actual) - expected) <= 1e-12 + 1e-10 * abs(expected),
            "independent loss disagreement",
        )
    else:
        same(actual, expected)


def _average(values: list[float]) -> float:
    with localcontext() as context:
        context.prec = 80
        return float(
            sum((Decimal.from_float(number(x)) for x in values), Decimal(0))
        ) / len(values)


def losses(
    pollen: list[float], taxa: list[str], counts: dict[str, int]
) -> dict[str, Any]:
    """Evaluate fraction losses and the declared count-conditioned deviance."""
    require(
        set(counts) == set(taxa)
        and all(type(x) is int and x >= 0 for x in counts.values())
        and 0 < sum(counts.values()) <= 2**53,
        "source-bound integer count denominator",
    )
    require(
        len(pollen) == 30
        and all(0 <= number(x) <= 1 for x in pollen)
        and abs(math.fsum(pollen) - 1) <= 1e-9,
        "scored closed composition",
    )
    with localcontext() as context:
        context.prec = 80
        p = [Decimal.from_float(number(x)) for x in pollen]
        observed = [Decimal.from_float(counts[t] / sum(counts.values())) for t in taxa]
        l1 = sum((abs(x - y) for x, y in zip(p, observed, strict=True)), Decimal(0))
        h = (
            sum(
                ((x.sqrt() - y.sqrt()) ** 2 for x, y in zip(p, observed, strict=True)),
                Decimal(0),
            )
            / 2
        ).sqrt()
        impossible = any(counts[t] > 0 and pollen[i] == 0 for i, t in enumerate(taxa))
        deviance = (
            None
            if impossible
            else float(
                max(
                    Decimal(0),
                    2
                    * sum(
                        (
                            Decimal(counts[t])
                            * (
                                Decimal(counts[t])
                                / (Decimal(sum(counts.values())) * p[i])
                            ).ln()
                            for i, t in enumerate(taxa)
                            if counts[t] > 0
                        ),
                        Decimal(0),
                    ),
                )
            )
        )
    return {
        "mae_fraction": float(l1 / 30),
        "total_variation": float(l1 / 2),
        "hellinger": float(h),
        "count_conditioned_deviance": deviance,
        "zero_probability_positive_count": impossible,
    }


def _mean(
    rows: list[dict[str, float]], fields: tuple[str, ...]
) -> dict[str, float] | None:
    if not rows:
        return None
    with localcontext() as context:
        context.prec = 80
        return {
            key: float(
                sum((Decimal.from_float(number(row[key])) for row in rows), Decimal(0))
            )
            / len(rows)
            for key in fields
        }


def audit_scores(
    packet: dict[str, Any],
    predictions: list[dict[str, Any]],
    scores: dict[str, Any],
    accesses: list[dict[str, Any]],
    counts: dict[str, dict[str, int]],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    """Verify ten one-time outcome accesses and fifty dispositions without source I/O."""
    by_context = contexts(packet, protocol)
    selected = packet["cohort"]["selected"]
    require(set(counts) == set(selected), "exact ten scoring owners")
    require(scores["schema_version"] == "author-lra-thinning-scores.v1", "score schema")
    freeze = scores["prediction_freeze_sha256"]
    require(
        type(freeze) is str and re.fullmatch(r"[0-9a-f]{64}", freeze),
        "closed prediction freeze",
    )
    same(scores["metric_axis"], list(METRICS))
    require(len(predictions) == 50, "all fifty predictions retained")
    pi = {(r["target"], r["method_id"]): r for r in predictions}
    require(
        len(pi) == 50 and set(pi) == {(t, m) for t in selected for m in METHODS},
        "unique prediction slots",
    )
    refs = {r["record_id"]: r for r in packet["observation_refs"]}
    require(
        len(refs) == len(packet["observation_refs"]) == 10
        and set(refs) == set(selected),
        "ten observation references",
    )
    expected_access = [
        {
            "target": t,
            "role": "outer_scoring_after_prediction_readback",
            "observation_reference": refs[t],
            "geometry_reference": packet["geometry_refs"][t],
            "prediction_freeze_sha256": freeze,
            "scope": "previously_exposed_role_specific_access_not_globally_unread",
        }
        for t in selected
    ]
    same(accesses, expected_access)
    require(
        len(scores["targets"]) == 10
        and [r["target"] for r in scores["targets"]] == selected,
        "all ordered scored targets",
    )
    source_refs = {
        (r["target"], r["method_id"]): r
        for r in packet["retained_reference_predictions"]
    }
    require(
        len(source_refs) == len(packet["retained_reference_predictions"]) == 40
        and set(source_refs)
        == {(t, m) for t in selected for m in (*BASELINES, "hellinger_20km")},
        "forty matched immutable references",
    )
    targets = []
    for actual in scores["targets"]:
        target = actual["target"]
        context = next(r for r in by_context.values() if r["target"] == target)
        metadata = {
            "target": target,
            "context_id": context["context_id"],
            "observed_reference": refs[target],
            "observed_total_count": sum(counts[target].values()),
            "observed_counts": counts[target],
            "vegetation_accuracy": "not_evaluated_no_independent_measured_observation",
        }
        same({key: actual[key] for key in metadata}, metadata)
        require(
            len(actual["methods"]) == 5
            and [r["method_id"] for r in actual["methods"]] == list(METHODS),
            "complete five scoring dispositions",
        )
        for observed in actual["methods"]:
            prediction = pi[(target, observed["method_id"])]
            expected = {
                "target": target,
                "context_id": context["context_id"],
                "method_id": observed["method_id"],
                "prediction_input_sha256": prediction["scientific_input_sha256"],
                "status": "scored"
                if prediction["status"] == "predicted"
                else "prediction_refused",
            }
            require(
                prediction["context_id"] == context["context_id"]
                and prediction["status"] in ("predicted", "refused"),
                "scored prediction identity",
            )
            if prediction["status"] == "predicted":
                expected["metrics"] = losses(
                    prediction["pollen_fraction"], packet["taxa"], counts[target]
                )
            else:
                expected["reason"] = prediction["reason"]
            _close(observed, expected)
        old_metrics = actual["retained_full15_metrics"]
        require(
            set(old_metrics) == {*BASELINES, "hellinger_20km"},
            "four retained score axes",
        )
        for method in old_metrics:
            own = losses(
                source_refs[(target, method)]["pollen_fraction"],
                packet["taxa"],
                counts[target],
            )
            _close(old_metrics[method], {m: own[m] for m in METRICS})
        methods = {r["method_id"]: r for r in actual["methods"]}
        comparisons = []
        specification = [
            (h, b, "within_thinned") for h in HELLINGER for b in BASELINES
        ] + [
            (m, m if m in BASELINES else "hellinger_20km", "retained_full_fifteen")
            for m in METHODS
        ]
        for model, reference, channel in specification:
            first = methods[model]
            second = (
                methods[reference].get("metrics")
                if channel == "within_thinned"
                else old_metrics[reference]
            )
            paired = first["status"] == "scored" and second is not None
            comparisons.append(
                {
                    "target": target,
                    "model_method_id": model,
                    "reference_method_id": reference,
                    "reference_channel": channel,
                    "status": "paired" if paired else "not_paired_prediction_refusal",
                    "model_minus_reference": {
                        m: first["metrics"][m] - second[m] for m in METRICS
                    }
                    if paired
                    else None,
                }
            )
        # Differences and strict improvement signs are derived from the saved
        # numerically qualified loss scalars, not from alternate rounding of a
        # second metric implementation near an exact baseline equality.
        same(actual["comparisons"], comparisons)
        require(
            set(actual)
            == set(metadata) | {"methods", "retained_full15_metrics", "comparisons"},
            "closed target scoring fields",
        )
        targets.append(actual)
    summaries = {}
    for method in METHODS:
        rows = [
            next(r for r in t["methods"] if r["method_id"] == method) for t in targets
        ]
        valid = [r for r in rows if r["status"] == "scored"]
        impossible = [
            r["target"]
            for r in valid
            if r["metrics"]["zero_probability_positive_count"]
        ]
        summaries[method] = {
            "requested_targets": 10,
            "scored_target_ids": [r["target"] for r in valid],
            "refused_target_ids": [
                r["target"] for r in rows if r["status"] != "scored"
            ],
            "impossible_positive_count_target_ids": impossible,
            "mean_bounded_metrics_on_scored_targets": _mean(
                [r["metrics"] for r in valid], METRICS
            ),
            "mean_count_deviance": {
                "status": "infinite_positive_count_loss"
                if impossible
                else "finite"
                if valid
                else "unavailable_no_scores",
                "value": None
                if impossible or not valid
                else _average(
                    [r["metrics"]["count_conditioned_deviance"] for r in valid]
                ),
            },
        }
    _close(scores["method_summaries"], summaries)
    comparison_summaries = []
    for position, first in enumerate(targets[0]["comparisons"]):
        rows = [t["comparisons"][position] for t in targets]
        paired = [r for r in rows if r["status"] == "paired"]
        comparison_summaries.append(
            {
                **{
                    k: first[k]
                    for k in (
                        "model_method_id",
                        "reference_method_id",
                        "reference_channel",
                    )
                },
                "common_target_ids": [r["target"] for r in paired],
                "excluded_target_ids": [
                    r["target"] for r in rows if r["status"] != "paired"
                ],
                "mean_differences": _mean(
                    [r["model_minus_reference"] for r in paired], METRICS
                ),
                "improved_targets": {
                    m: sum(r["model_minus_reference"][m] < 0 for r in paired)
                    for m in METRICS
                },
            }
        )
    _close(scores["comparison_summaries"], comparison_summaries)
    require(
        type(scores["unique_observed_total_count"]) is int
        and scores["unique_observed_total_count"]
        == sum(sum(counts[t].values()) for t in selected),
        "unique target grain denominator",
    )
    same(
        scores["scope"],
        "exposed_point_only_geographic_thinning_and_changed_regional_source_not_field_accuracy",
    )
    require(
        set(scores)
        == {
            "schema_version",
            "prediction_freeze_sha256",
            "metric_axis",
            "targets",
            "method_summaries",
            "comparison_summaries",
            "unique_observed_total_count",
            "scope",
        },
        "closed score packet",
    )
    return {
        "status": "passed",
        "targets_verified": 10,
        "scoring_dispositions_verified": 50,
        "paired_channels_per_target": 11,
        "role_accesses_verified": 10,
        "unique_counted_mass": scores["unique_observed_total_count"],
        "scope": "Postfreeze source-bound pollen loss and matched descriptive summaries; no vegetation accuracy, intervals or generalization precision",
    }
