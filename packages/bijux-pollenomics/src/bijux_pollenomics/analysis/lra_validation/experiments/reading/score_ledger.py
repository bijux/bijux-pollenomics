"""Complete retained score accounting and descriptive summary reconciliation."""

from __future__ import annotations

from dataclasses import dataclass, field

from ...contracts import (
    ValidationRefusal,
    canonical_json,
    finite_number,
)
from ..configuration import (
    BLOCK_PROFILE,
    LOCAL_EVALUATION_ROLES,
    LOCAL_PROFILE,
    TEMPORAL_PROFILE,
    identity,
    object_list,
    object_mapping,
)
from ..outputs import ExperimentProduct, read_member


@dataclass(frozen=True)
class RetainedPredictionLedger:
    product: ExperimentProduct
    manifest: dict[str, object]
    folds: dict[str, dict[str, object]]
    rows: dict[tuple[str, str, str], dict[str, object]]
    methods: tuple[str, ...]
    ownership: dict[str, str]
    observation_context: dict[str, dict[str, object]] = field(default_factory=dict)


def require_equal(actual: object, expected: object, label: str) -> None:
    if canonical_json(actual) != canonical_json(expected):
        raise ValidationRefusal("retained_score_mismatch", label)


def validate_outcome_access(
    values: object, parent: RetainedPredictionLedger, refs: dict[str, dict[str, object]]
) -> None:
    expected = []
    seen = set()
    temporal = parent.manifest["profile"] == TEMPORAL_PROFILE
    for fold_id, fold in sorted(parent.folds.items()):
        for raw in object_list(fold["test_record_ids"], "test records"):
            record = identity(raw)
            if (
                record in seen
                or record not in refs
                or not any(
                    (fold_id, record, method) in parent.rows
                    for method in parent.methods
                )
            ):
                continue
            seen.add(record)
            ref = refs[record]
            if temporal:
                expected.append(
                    {
                        "record_id": record,
                        "path": ref["path"],
                        "sha256": ref["sha256"],
                        "predictions_manifest_sha256": parent.product.manifest_sha256,
                        "access_order": "after_retained_prediction_admission",
                    }
                )
            else:
                expected.append(
                    {
                        "record_id": record,
                        "observation_sha256": ref["sha256"],
                        "prediction_manifest_sha256": parent.product.manifest_sha256,
                        "ordering": "published_predictions_before_vegetation_open"
                        if parent.manifest["profile"] == LOCAL_PROFILE
                        else "verified_published_predictions_before_outcome_open",
                    }
                )
    require_equal(values, expected, "complete retained access ordering")


def validate_score_summaries(
    product: ExperimentProduct,
    scientific: dict[str, object],
    parent: RetainedPredictionLedger,
    units: list[dict[str, object]],
) -> None:
    profile = parent.manifest["profile"]
    if profile == TEMPORAL_PROFILE:
        expected: dict[str, object] = {"vegetation_cover": None, "pollen": None}
        for unit in units:
            expected[identity(unit["producer_target"])] = {
                "requested": 1,
                "generated_prediction": int(unit["upstream_prediction"] is not None),
                "status": object_mapping(unit["metric"], "metric")["status"],
            }
        require_equal(scientific["denominators"], expected, "temporal denominators")
        require_equal(
            scientific["final_policy_evaluation"],
            "not_performed",
            "final policy posture",
        )
        return
    summaries = object_list(read_member(product, "summaries.json"), "summaries")
    require_equal(summaries, scientific["summaries"], "summary member")
    keys = set()
    for value in summaries:
        row = object_mapping(value, "summary")
        method = identity(row["baseline" if "baseline" in row else "method"])
        target = identity(row["target"])
        if (method, target) in keys:
            raise ValidationRefusal("retained_score_mismatch", "duplicate summary")
        keys.add((method, target))
        selected = [
            u for u in units if u["method_id"] == method and u["target"] == target
        ]
        metrics = [object_mapping(u["metric"], "metric") for u in selected]
        errors = [
            finite_number(m["mae_fraction"]) for m in metrics if m["status"] == "scored"
        ]
        require_equal(row["requested"], len(selected), "summary denominator")
        require_equal(row["scored"], len(errors), "summary scored")
        require_equal(
            row["by_status"],
            {
                identity(s): sum(m["status"] == s for m in metrics)
                for s in {m["status"] for m in metrics}
            },
            "summary statuses",
        )
        require_equal(
            row["mean_mae_fraction"],
            sum(errors) / len(errors) if errors else None,
            "summary mean",
        )
        require_equal(row["interval_coverage"], None, "unsupported coverage")
        require_equal(
            row["uncertainty_status"],
            "intervals_not_implemented",
            "summary uncertainty",
        )
        if profile == LOCAL_PROFILE:
            require_equal(
                row["evaluation_role"], LOCAL_EVALUATION_ROLES[target], "summary role"
            )
            require_equal(
                row["eligible_for_heldout_acceptance"],
                target == "vegetation_cover",
                "summary eligibility",
            )
        else:
            require_equal(
                row["scoring_unit"],
                "heldout_group_within_original_spatial_block"
                if profile == BLOCK_PROFILE
                else "outer_site_group",
                "summary scoring unit",
            )
            require_equal(
                row["zero_probability_positive_count"],
                sum(m.get("zero_probability_positive_count") is True for m in metrics),
                "impossible count",
            )
            require_equal(
                row["independence"],
                "within_block_targets_correlated_and_training_blocks_overlap"
                if profile == BLOCK_PROFILE
                else "overlapping_training_cv_not_independent_fixed_model",
                "independence",
            )
    require_equal(
        sorted(keys),
        sorted(
            (m, t)
            for m in parent.methods
            for t in ("vegetation_cover", "pollen_composition")
        ),
        "summary universe",
    )
    if profile != LOCAL_PROFILE:
        require_equal(
            scientific["uncertainty_status"], "intervals_not_implemented", "uncertainty"
        )
        paired = []
        indexed = {
            (u["fold_id"], u["record_id"], u["target"], u["method_id"]): u
            for u in units
        }
        for unit in units:
            if (
                "training_mean" not in parent.methods
                or unit["method_id"] == "training_mean"
            ):
                continue
            base = indexed[
                (unit["fold_id"], unit["record_id"], unit["target"], "training_mean")
            ]
            current, reference = (
                object_mapping(unit["metric"], "metric"),
                object_mapping(base["metric"], "metric"),
            )
            if current["status"] == reference["status"] == "scored":
                paired.append(
                    {
                        "fold_id": unit["fold_id"],
                        "group_id": unit["group_id"],
                        "record_id": unit["record_id"],
                        "baseline": unit["method_id"],
                        "reference_baseline": "training_mean",
                        "target": unit["target"],
                        "mae_improvement_fraction": finite_number(
                            reference["mae_fraction"]
                        )
                        - finite_number(current["mae_fraction"]),
                    }
                )
        actual = read_member(product, "paired_baseline_differences.json")
        require_equal(
            actual, scientific["paired_baseline_differences"], "paired member"
        )
        require_equal(
            sorted(object_list(actual, "paired"), key=canonical_json),
            sorted(paired, key=canonical_json),
            "paired metrics",
        )
