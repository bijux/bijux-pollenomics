"""Independent small composition, access and matched-population controls."""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.thinning.verification.scoring import (
    audit_scores,
    losses,
)

from . import synthetic

METRICS = ("mae_fraction", "total_variation", "hellinger")
METHODS = (
    "training_mean",
    "nearest_site",
    "inverse_distance_squared",
    "hellinger_20km",
    "hellinger_100km",
)


def _literal_loss(pollen: list[float]) -> dict[str, Any]:
    truth = [2 / 3, 1 / 3] + [0.0] * 28
    l1 = math.fsum(abs(a - b) for a, b in zip(pollen, truth, strict=True))
    impossible = pollen[0] == 0 or pollen[1] == 0
    deviance = (
        None
        if impossible
        else max(
            0.0, 2 * (2 * math.log(2 / (3 * pollen[0])) + math.log(1 / (3 * pollen[1])))
        )
    )
    return {
        "mae_fraction": l1 / 30,
        "total_variation": l1 / 2,
        "hellinger": math.hypot(
            *(math.sqrt(a) - math.sqrt(b) for a, b in zip(pollen, truth, strict=True))
        )
        / math.sqrt(2),
        "count_conditioned_deviance": deviance,
        "zero_probability_positive_count": impossible,
    }


def scored_fixture(refuse: bool = False, impossible: bool = False) -> tuple[Any, ...]:
    packet, predictions, protocol = synthetic()
    if refuse:
        predictions[0] = {
            k: v
            for k, v in predictions[0].items()
            if k
            not in (
                "weights",
                "vegetation_fraction",
                "pollen_fraction",
                "local_deposition",
                "total_deposition",
            )
        }
        predictions[0].update(
            status="refused", reason="forward_model_domain", detail="zero finite mass"
        )
    if impossible:
        for row in predictions:
            row["pollen_fraction"] = [1.0] + [0.0] * 29
    selected = packet["cohort"]["selected"]
    counts = {
        t: dict(zip(packet["taxa"], [2, 1] + [0] * 28, strict=True)) for t in selected
    }
    refs = {r["record_id"]: r for r in packet["observation_refs"]}
    freeze = "a" * 64
    targets = []
    for target, context in zip(selected, packet["contexts"], strict=True):
        methods = []
        for prediction in [r for r in predictions if r["target"] == target]:
            row = {
                "target": target,
                "context_id": context["context_id"],
                "method_id": prediction["method_id"],
                "prediction_input_sha256": prediction["scientific_input_sha256"],
                "status": "scored"
                if prediction["status"] == "predicted"
                else "prediction_refused",
            }
            row.update(
                metrics=_literal_loss(prediction["pollen_fraction"])
            ) if prediction["status"] == "predicted" else row.update(
                reason=prediction["reason"]
            )
            methods.append(row)
        mi = {r["method_id"]: r for r in methods}
        old = {method: dict.fromkeys(METRICS, 0.0) for method in METHODS[:-1]}
        comparisons = []
        specs = [
            (h, b, "within_thinned") for h in METHODS[-2:] for b in METHODS[:3]
        ] + [
            (m, m if m in METHODS[:3] else "hellinger_20km", "retained_full_fifteen")
            for m in METHODS
        ]
        for model, reference, channel in specs:
            second: Any = (
                mi[reference].get("metrics")
                if channel == "within_thinned"
                else old[reference]
            )
            valid = mi[model]["status"] == "scored" and second is not None
            comparisons.append(
                {
                    "target": target,
                    "model_method_id": model,
                    "reference_method_id": reference,
                    "reference_channel": channel,
                    "status": "paired" if valid else "not_paired_prediction_refusal",
                    "model_minus_reference": {
                        m: mi[model]["metrics"][m] - second[m] for m in METRICS
                    }
                    if valid
                    else None,
                }
            )
        targets.append(
            {
                "target": target,
                "context_id": context["context_id"],
                "observed_reference": refs[target],
                "observed_total_count": 3,
                "observed_counts": counts[target],
                "vegetation_accuracy": "not_evaluated_no_independent_measured_observation",
                "methods": methods,
                "retained_full15_metrics": old,
                "comparisons": comparisons,
            }
        )
    method_summaries = {}
    for method in METHODS:
        rows = [
            next(r for r in t["methods"] if r["method_id"] == method) for t in targets
        ]
        valid = [r for r in rows if r["status"] == "scored"]
        bad = [
            r["target"]
            for r in valid
            if r["metrics"]["zero_probability_positive_count"]
        ]
        method_summaries[method] = {
            "requested_targets": 10,
            "scored_target_ids": [r["target"] for r in valid],
            "refused_target_ids": [
                r["target"] for r in rows if r["status"] != "scored"
            ],
            "impossible_positive_count_target_ids": bad,
            "mean_bounded_metrics_on_scored_targets": {
                m: math.fsum(r["metrics"][m] for r in valid) / len(valid)
                for m in METRICS
            }
            if valid
            else None,
            "mean_count_deviance": {
                "status": "infinite_positive_count_loss"
                if bad
                else "finite"
                if valid
                else "unavailable_no_scores",
                "value": math.fsum(
                    r["metrics"]["count_conditioned_deviance"] for r in valid
                )
                / len(valid)
                if valid and not bad
                else None,
            },
        }
    summaries = []
    for i, first in enumerate(targets[0]["comparisons"]):
        rows = [t["comparisons"][i] for t in targets]
        valid = [r for r in rows if r["status"] == "paired"]
        summaries.append(
            {
                **{
                    k: first[k]
                    for k in (
                        "model_method_id",
                        "reference_method_id",
                        "reference_channel",
                    )
                },
                "common_target_ids": [r["target"] for r in valid],
                "excluded_target_ids": [
                    r["target"] for r in rows if r["status"] != "paired"
                ],
                "mean_differences": {
                    m: math.fsum(r["model_minus_reference"][m] for r in valid)
                    / len(valid)
                    for m in METRICS
                }
                if valid
                else None,
                "improved_targets": {
                    m: sum(r["model_minus_reference"][m] < 0 for r in valid)
                    for m in METRICS
                },
            }
        )
    scores = {
        "schema_version": "author-lra-thinning-scores.v1",
        "prediction_freeze_sha256": freeze,
        "metric_axis": list(METRICS),
        "targets": targets,
        "method_summaries": method_summaries,
        "comparison_summaries": summaries,
        "unique_observed_total_count": 30,
        "scope": "exposed_point_only_geographic_thinning_and_changed_regional_source_not_field_accuracy",
    }
    accesses = [
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
    return packet, predictions, scores, accesses, counts, protocol


@pytest.mark.parametrize(
    "refused,impossible", [(False, False), (True, False), (False, True)]
)
def test_all_dispositions_and_impossible_mass_remain_explicit(
    refused: bool, impossible: bool
) -> None:
    args = scored_fixture(refused, impossible)
    facts = audit_scores(*args)
    assert facts["scoring_dispositions_verified"] == 50
    assert facts["unique_counted_mass"] == 30
    if impossible:
        summary = args[2]["method_summaries"]["training_mean"]
        assert summary["mean_count_deviance"] == {
            "status": "infinite_positive_count_loss",
            "value": None,
        }
        assert len(summary["scored_target_ids"]) == 10


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate_access",
        "wrong_role",
        "wrong_freeze",
        "observation_identity",
        "count_total",
        "count_boolean",
        "count_axis",
        "unique_denominator",
        "missing_target",
        "missing_method",
        "loss",
        "refused_population",
        "old_loss",
        "paired_identity",
        "improved_count",
        "old_deviance",
    ],
)
def test_score_access_pairing_and_denominator_tampering_refuse(defect: str) -> None:
    args = list(deepcopy(scored_fixture()))
    packet, _, scores, accesses, counts, _ = args
    target = scores["targets"][0]
    if defect == "duplicate_access":
        accesses[-1] = accesses[0]
    elif defect == "wrong_role":
        accesses[0]["role"] = "inner_training"
    elif defect == "wrong_freeze":
        accesses[0]["prediction_freeze_sha256"] = "b" * 64
    elif defect == "observation_identity":
        target["observed_reference"] = packet["observation_refs"][1]
    elif defect == "count_total":
        target["observed_total_count"] = 30
    elif defect == "count_boolean":
        counts[target["target"]][packet["taxa"][0]] = True
    elif defect == "count_axis":
        counts[target["target"]].pop(packet["taxa"][-1])
    elif defect == "unique_denominator":
        scores["unique_observed_total_count"] = 150
    elif defect == "missing_target":
        scores["targets"].pop()
    elif defect == "missing_method":
        target["methods"].pop()
    elif defect == "loss":
        target["methods"][0]["metrics"]["hellinger"] = 0.1
    elif defect == "refused_population":
        scores["method_summaries"]["training_mean"]["refused_target_ids"] = [
            target["target"]
        ]
    elif defect == "old_loss":
        target["retained_full15_metrics"]["training_mean"]["hellinger"] = 0.1
    elif defect == "paired_identity":
        target["comparisons"][0]["reference_channel"] = "retained_full_fifteen"
    elif defect == "improved_count":
        scores["comparison_summaries"][0]["improved_targets"]["hellinger"] = 10
    else:
        target["retained_full15_metrics"]["training_mean"][
            "count_conditioned_deviance"
        ] = 0.0
    with pytest.raises((ValueError, KeyError)):
        audit_scores(*args)


def test_exact_zero_observation_and_positive_count_impossibility() -> None:
    packet, _, _ = synthetic()
    counts = dict(zip(packet["taxa"], [3] + [0] * 29, strict=True))
    result = losses([1.0] + [0.0] * 29, packet["taxa"], counts)
    assert result == {
        "mae_fraction": 0.0,
        "total_variation": 0.0,
        "hellinger": 0.0,
        "count_conditioned_deviance": 0.0,
        "zero_probability_positive_count": False,
    }
    counts[packet["taxa"][1]] = 1
    result = losses([1.0] + [0.0] * 29, packet["taxa"], counts)
    assert result["count_conditioned_deviance"] is None
    assert result["zero_probability_positive_count"] is True
    assert result["hellinger"] > 0
