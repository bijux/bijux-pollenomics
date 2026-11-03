"""Compare new thinning predictions with their own and retained source baselines."""

from __future__ import annotations

import hashlib
from math import fsum, isfinite
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)

from ..inputs import decode, require

BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")
HELLINGER = ("hellinger_20km", "hellinger_100km")
METHODS = (*BASELINES, *HELLINGER)
METRICS = ("mae_fraction", "total_variation", "hellinger")


def loss(
    pollen: list[float], taxa: list[str], counts: dict[str, int]
) -> dict[str, Any]:
    """Use the existing fraction/count scorer without changing its denominator."""
    require(set(counts) == set(taxa), "Complete observed taxon axis required")
    fractions = dict(zip(taxa, pollen, strict=True))
    scored = score_pollen(fractions, counts)
    require(scored.status == "scored", "A compatible positive count is required")
    observed = {taxon: counts[taxon] / sum(counts.values()) for taxon in taxa}
    return {
        "mae_fraction": scored.mae_fraction,
        "total_variation": scored.total_variation,
        "hellinger": hellinger_distance(fractions, observed),
        "count_conditioned_deviance": scored.count_conditioned_deviance,
        "zero_probability_positive_count": scored.zero_probability_positive_count,
    }


def retained_metrics(
    repository: Path,
    protocol: dict[str, Any],
    packet: dict[str, Any],
    counts: dict[str, dict[str, int]],
) -> dict[str, dict[str, dict[str, float]]]:
    """Join immutable prior scores after the caller authenticates new predictions."""
    pin = protocol["qualified_sources"]["outer_scores"]
    relative = Path(pin["path"])
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "Repository score reference required",
    )
    path = repository / relative
    require(
        path.is_file()
        and not any(parent.is_symlink() for parent in (path, *path.parents))
        and path.stat().st_size == pin["bytes"],
        "Retained scoring object is absent or redirected",
    )
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == pin["sha256"], "Prior score changed")
    rows = decode(raw)
    require(type(rows) is list and len(rows) == 15, "Fifteen retained outer rows")
    by_owner = {row["outer_target"]: row for row in rows}
    require(
        len(by_owner) == 15 and set(by_owner) == set(packet["groups"]),
        "Retained score owner population differs",
    )
    refs = {row["record_id"]: row for row in packet["observation_refs"]}
    result: dict[str, dict[str, dict[str, float]]] = {}
    for target in packet["cohort"]["selected"]:
        row = by_owner[target]
        require(
            row["status"] == "scored"
            and row["selected_scale_km"] == 20.0
            and type(row["observed_count"]) is int
            and row["observed_count"] == sum(counts[target].values())
            and row["observed_reference"] == refs[target],
            "Retained target outcome/support or full-cohort scale differs",
        )
        metrics = {name: row["matched_baselines"][name] for name in BASELINES}
        metrics["hellinger_20km"] = row["metrics"]
        for values in metrics.values():
            require(
                set(values) == set(METRICS)
                and all(
                    type(x) in (int, float) and isfinite(x) and 0 <= x <= 1
                    for x in values.values()
                ),
                "Finite bounded exact retained score axis required",
            )
        result[target] = metrics
    return result


def _comparison(
    target: str,
    model: dict[str, Any],
    reference_method: str,
    channel: str,
    reference: dict[str, Any] | None,
) -> dict[str, Any]:
    paired = model["status"] == "scored" and reference is not None
    differences = None
    if paired:
        assert reference is not None
        differences = {
            metric: model["metrics"][metric] - reference[metric] for metric in METRICS
        }
    return {
        "target": target,
        "model_method_id": model["method_id"],
        "reference_method_id": reference_method,
        "reference_channel": channel,
        "status": "paired" if paired else "not_paired_prediction_refusal",
        "model_minus_reference": differences,
    }


def score_targets(
    packet: dict[str, Any],
    predictions: list[dict[str, Any]],
    counts: dict[str, dict[str, int]],
    prior: dict[str, dict[str, dict[str, float]]],
    prediction_freeze_sha256: str,
) -> dict[str, Any]:
    """Keep fifty dispositions and eleven paired channels per selected target."""
    selected, taxa = packet["cohort"]["selected"], packet["taxa"]
    contexts = {row["target"]: row for row in packet["contexts"]}
    index = {(row["target"], row["method_id"]): row for row in predictions}
    require(
        len(selected) == len(set(selected)) == len(contexts) == 10
        and set(contexts) == set(counts) == set(prior) == set(selected)
        and len(index) == len(predictions) == 50
        and set(index)
        == {(target, method) for target in selected for method in METHODS},
        "Complete ten-target/fifty-method scoring population required",
    )
    refs = {row["record_id"]: row for row in packet["observation_refs"]}
    targets: list[dict[str, Any]] = []
    for target in selected:
        context, observed = contexts[target], counts[target]
        rows: list[dict[str, Any]] = []
        for method in METHODS:
            prediction = index[target, method]
            require(
                prediction["context_id"] == context["context_id"]
                and prediction["status"] in {"predicted", "refused"},
                "Prediction context or disposition differs",
            )
            row: dict[str, Any] = {
                "target": target,
                "context_id": context["context_id"],
                "method_id": method,
                "prediction_input_sha256": prediction["scientific_input_sha256"],
                "status": "scored"
                if prediction["status"] == "predicted"
                else "prediction_refused",
            }
            if prediction["status"] == "predicted":
                row["metrics"] = loss(prediction["pollen_fraction"], taxa, observed)
            else:
                row["reason"] = prediction["reason"]
            rows.append(row)
        by_method = {row["method_id"]: row for row in rows}
        comparisons = [
            _comparison(
                target,
                by_method[model],
                reference,
                "within_thinned",
                by_method[reference].get("metrics"),
            )
            for model in HELLINGER
            for reference in BASELINES
        ]
        comparisons.extend(
            _comparison(
                target,
                by_method[method],
                method if method in BASELINES else "hellinger_20km",
                "retained_full_fifteen",
                prior[target][method if method in BASELINES else "hellinger_20km"],
            )
            for method in METHODS
        )
        targets.append(
            {
                "target": target,
                "context_id": context["context_id"],
                "observed_reference": refs[target],
                "observed_total_count": sum(observed.values()),
                "observed_counts": dict(observed),
                "vegetation_accuracy": "not_evaluated_no_independent_measured_observation",
                "methods": rows,
                "retained_full15_metrics": prior[target],
                "comparisons": comparisons,
            }
        )
    method_summaries: dict[str, Any] = {}
    for method in METHODS:
        rows = [
            next(r for r in t["methods"] if r["method_id"] == method) for t in targets
        ]
        scored = [r for r in rows if r["status"] == "scored"]
        impossible = [
            r["target"]
            for r in scored
            if r["metrics"]["zero_probability_positive_count"]
        ]
        method_summaries[method] = {
            "requested_targets": 10,
            "scored_target_ids": [r["target"] for r in scored],
            "refused_target_ids": [r["target"] for r in rows if r not in scored],
            "impossible_positive_count_target_ids": impossible,
            "mean_bounded_metrics_on_scored_targets": {
                metric: fsum(r["metrics"][metric] for r in scored) / len(scored)
                for metric in METRICS
            }
            if scored
            else None,
            "mean_count_deviance": {
                "status": "infinite_positive_count_loss"
                if impossible
                else "finite"
                if scored
                else "unavailable_no_scores",
                "value": fsum(
                    r["metrics"]["count_conditioned_deviance"] for r in scored
                )
                / len(scored)
                if scored and not impossible
                else None,
            },
        }
    comparison_summaries: list[dict[str, Any]] = []
    keys = [
        (r["model_method_id"], r["reference_method_id"], r["reference_channel"])
        for r in targets[0]["comparisons"]
    ]
    for model, reference, channel in keys:
        rows = [
            next(
                row
                for row in target["comparisons"]
                if (
                    row["model_method_id"],
                    row["reference_method_id"],
                    row["reference_channel"],
                )
                == (model, reference, channel)
            )
            for target in targets
        ]
        paired = [row for row in rows if row["status"] == "paired"]
        comparison_summaries.append(
            {
                "model_method_id": model,
                "reference_method_id": reference,
                "reference_channel": channel,
                "common_target_ids": [row["target"] for row in paired],
                "excluded_target_ids": [
                    row["target"] for row in rows if row not in paired
                ],
                "mean_differences": {
                    metric: fsum(row["model_minus_reference"][metric] for row in paired)
                    / len(paired)
                    for metric in METRICS
                }
                if paired
                else None,
                "improved_targets": {
                    metric: sum(
                        row["model_minus_reference"][metric] < 0 for row in paired
                    )
                    for metric in METRICS
                },
            }
        )
    return {
        "schema_version": "author-lra-thinning-scores.v1",
        "prediction_freeze_sha256": prediction_freeze_sha256,
        "metric_axis": list(METRICS),
        "targets": targets,
        "method_summaries": method_summaries,
        "comparison_summaries": comparison_summaries,
        "unique_observed_total_count": sum(t["observed_total_count"] for t in targets),
        "scope": "exposed_point_only_geographic_thinning_and_changed_regional_source_not_field_accuracy",
    }
