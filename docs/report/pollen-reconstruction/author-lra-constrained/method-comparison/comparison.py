"""Compute descriptive paired score differences and retain every refused or worse case."""

from __future__ import annotations

from collections import Counter
import math
import statistics
from typing import Any

sources: dict[str, Any] = globals()["sources"]
require = sources["require"]
decode = sources["decode"]
join_support = sources["join_support"]
BASELINES = sources["BASELINES"]
METRICS = (
    "mae_fraction",
    "rmse_fraction",
    "total_variation",
    "bias_fraction",
    "count_conditioned_deviance",
)


def metric_delta(
    old: dict[str, Any], new: dict[str, Any], metric: str
) -> dict[str, Any]:
    before, after = old[metric], new[metric]
    if metric == "count_conditioned_deviance" and (before is None or after is None):
        require(
            (before is not None or old["zero_probability_positive_count"] is True)
            and (after is not None or new["zero_probability_positive_count"] is True),
            "null deviance requires explicit impossible-positive-count flag",
        )
        category = (
            "both_infinite"
            if before is after
            else "finite_after_original_infinite"
            if before is None
            else "infinite_after_original_finite"
        )
        return {
            "original": before,
            "cohort": after,
            "delta": None,
            "category": category,
        }
    require(
        type(before) in (int, float)
        and type(after) in (int, float)
        and math.isfinite(before)
        and math.isfinite(after),
        "finite stored point metrics required",
    )
    return {
        "original": before,
        "cohort": after,
        "delta": after - before,
        "category": "finite_pair",
    }


def compare(bodies: dict[str, bytes], protocol: dict[str, Any]) -> dict[str, Any]:
    context = sources["admit"](bodies, protocol)
    folds = context["folds"]
    sites = context["sites"]
    old_dispositions = context["old_dispositions"]
    new_slots = context["new_slots"]
    new_scores = context["new_scores"]
    old_predictions = context["old_predictions"]
    old_scores = context["old_scores"]
    preparations = context["preparations"]
    taxa = context["taxa"]
    paired, all_folds, unpaired = [], [], []
    for fold_key, fold in sorted(folds.items()):
        fold_id = fold_key[0]
        target = fold["test_record_ids"][0]
        site = sites[target]
        old_disposition = old_dispositions[fold_key]
        require(
            old_disposition["target_record_id"] == target,
            "native disposition target differs",
        )
        raw = decode(bodies["prepared:" + site["raw"]["path"]])
        geometry = decode(bodies["prepared:" + site["geometry"]["path"]])
        cohort_status = []
        for baseline in BASELINES:
            key = (fold_id, target, baseline)
            slot = new_slots[key]
            score = new_scores[key]
            require(
                slot["status"] == "predicted" and score["status"] == "scored",
                "admitted complete fifteen-fold cohort required",
            )
            cohort_status.append(slot["status"])
            if old_disposition["status"] == "refused":
                require(
                    key not in old_predictions
                    and old_scores[key]["score"]["status"] == "prediction_failed",
                    "original refusal must remain literal",
                )
                unpaired.append(
                    {
                        "fold_id": fold_id,
                        "record_id": target,
                        "baseline": baseline,
                        "original_score": None,
                        "original_reason": old_disposition["reason_code"],
                        "cohort_score": score,
                        "paired_comparison_available": False,
                    }
                )
                continue
            before = old_scores[key]
            old_prediction = old_predictions[key]
            new_prediction = slot["prediction"]
            require(
                before["score"]["status"] == "scored"
                and before["target"] == score["target"] == "pollen_composition"
                and before["bin_id"]
                == new_prediction["bin_id"]
                == raw["sample"]["bin_id"],
                "scored outcome/bin support differs",
            )
            require(
                old_prediction["prediction_manifest"]["fold"]
                == new_prediction["prediction_manifest"]["fold"]
                == fold,
                "prediction fold ancestry differs",
            )
            require(
                target
                not in old_prediction["prediction_manifest"]["allowed_input_closure"]
                and target
                not in new_prediction["prediction_manifest"]["allowed_input_closure"],
                "target entered its own training closure",
            )
            require(
                set(old_prediction["pollen_fraction"])
                == set(new_prediction["pollen_fraction"])
                == set(taxa),
                "prediction taxon support differs",
            )
            support = join_support(
                preparations[fold_key],
                slot["geometry"],
                fold,
                raw,
                geometry,
                site,
                taxa,
            )
            counts = dict(zip(taxa, raw["sample"]["counts"], strict=True))
            require(
                before["observation_sha256"] == site["raw"]["sha256"]
                and before["observation"]["pollen_count"] == counts
                and before["score"]["observed_total_count"]
                == score["observed_total_count"]
                == sum(counts.values())
                and all(
                    type(errors) is list
                    and len(errors) == len(taxa)
                    and all(
                        type(pair) is list
                        and len(pair) == 2
                        and type(pair[0]) is str
                        and type(pair[1]) in (int, float)
                        and math.isfinite(pair[1])
                        for pair in errors
                    )
                    and len({pair[0] for pair in errors}) == len(taxa)
                    and {pair[0] for pair in errors} == set(taxa)
                    for errors in (
                        before["score"]["signed_error_by_taxon"],
                        score["signed_error_by_taxon"],
                    )
                ),
                "exact observation count/taxon support differs",
            )
            metrics = {
                metric: metric_delta(before["score"], score, metric)
                for metric in METRICS
            }
            worse = [
                metric
                for metric, row in metrics.items()
                if metric != "bias_fraction"
                and (
                    (row["delta"] is not None and row["delta"] > 0)
                    or row["category"] == "infinite_after_original_finite"
                )
            ]
            paired.append(
                {
                    "fold_id": fold_id,
                    "record_id": target,
                    "baseline": baseline,
                    "support": support,
                    "metrics": metrics,
                    "worse_error_metrics": worse,
                    "original_prediction_sha256": old_prediction[
                        "prediction_manifest_sha256"
                    ],
                    "cohort_prediction_sha256": new_prediction[
                        "prediction_manifest_sha256"
                    ],
                }
            )
        all_folds.append(
            {
                "fold_id": fold_id,
                "record_id": target,
                "original_status": old_disposition["status"],
                "original_reason": old_disposition["reason_code"] or None,
                "cohort_status": "predicted"
                if set(cohort_status) == {"predicted"}
                else "refused",
                "paired_baseline_rows": 3
                if old_disposition["status"] == "predicted"
                else 0,
            }
        )
    require(
        len(paired) == 42
        and len(all_folds) == 15
        and len({row["fold_id"] for row in paired}) == 14,
        "complete matched14 bythree plus15 dispositions required",
    )
    summaries = []
    for baseline in BASELINES:
        rows = [row for row in paired if row["baseline"] == baseline]
        result: dict[str, Any] = {
            "baseline": baseline,
            "paired_folds": len(rows),
            "weighting": "equal fold; descriptive dependent point differences",
        }
        for metric in METRICS:
            finite = [
                row["metrics"][metric]["delta"]
                for row in rows
                if row["metrics"][metric]["category"] == "finite_pair"
            ]
            result[metric] = {
                "finite_paired_denominator": len(finite),
                "categories": dict(
                    Counter(row["metrics"][metric]["category"] for row in rows)
                ),
                "mean_delta": statistics.fmean(finite) if finite else None,
                "median_delta": statistics.median(finite) if finite else None,
                "minimum_delta": min(finite) if finite else None,
                "maximum_delta": max(finite) if finite else None,
                "positive_delta_folds": sum(value > 0 for value in finite),
                "negative_delta_folds": sum(value < 0 for value in finite),
                "zero_delta_folds": sum(value == 0 for value in finite),
            }
        summaries.append(result)
    return {
        "schema_version": "author-love-matched-method-comparison.v1",
        "question": protocol["question"],
        "method_difference": protocol["method_difference"],
        "counts": {
            "all_folds": 15,
            "original_scored_folds": 14,
            "original_refused_folds": 1,
            "cohort_scored_folds": 15,
            "cohort_refused_folds": 0,
            "matched_folds": 14,
            "paired_baseline_rows": 42,
        },
        "fold_dispositions": all_folds,
        "paired_scores": paired,
        "unmatched_cohort_scores": unpaired,
        "summaries": summaries,
        "negative_transfer_cases": [
            row for row in paired if row["worse_error_metrics"]
        ],
        "comparison_performed_without_refits_or_rescoring": True,
        "scope": protocol["scope"],
    }
