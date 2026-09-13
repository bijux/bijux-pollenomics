"""Immutable retained-score projections bound to their preserved evidence bodies."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from ...contracts import (
    ValidationRefusal,
    canonical_json,
    finite_number,
    manifest_sha256,
)
from ...metrics import score_pollen, score_vegetation
from ..configuration import (
    LOCAL_EVALUATION_ROLES,
    LOCAL_PROFILE,
    TEMPORAL_PROFILE,
    identity,
    object_list,
    object_mapping,
)
from ..inputs import _unique_pairs
from ..score_values import score_observation
from .score_ledger import require_equal


@dataclass(frozen=True)
class ScoredExperimentEvidence:
    """Immutable retrospective evidence, not a prospective evaluation certificate."""

    canonical_evidence_json: str
    evidence_sha256: str

    def __post_init__(self) -> None:
        try:
            value = object_mapping(json.loads(self.canonical_evidence_json), "evidence")
            require_equal(
                canonical_json(value),
                self.canonical_evidence_json,
                "canonical evidence",
            )
            require_equal(
                manifest_sha256(value), self.evidence_sha256, "evidence digest"
            )
            require_equal(
                value["schema_version"], "pollenomics-scored-evidence.v1", "schema"
            )
            require_equal(value["scientific_acceptance"], "not_evaluated", "posture")
            validate_evidence_envelope(value)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationRefusal("invalid_scored_evidence", str(exc)) from exc


def validate_evidence_envelope(value: dict[str, object]) -> None:
    """Refuse incomplete caller-constructed objects before readiness traverses them."""
    fields = {
        "schema_version",
        "kind",
        "profile",
        "data_kind",
        "scientific_acceptance",
        "prediction_manifest_sha256",
        "prediction_scientific_content_sha256",
        "score_manifest_sha256",
        "score_scientific_content_sha256",
        "source_authentication",
        "folds",
        "methods",
        "source_catalogue",
        "retained_member_json",
        "prediction_scientific_payload",
        "score_scientific_payload",
        "prediction_manifest_json",
        "score_manifest_json",
        "outcome_inventory",
        "outcome_access",
        "requested_units",
        "units",
        "prediction_frozen_at",
        "first_test_access_at",
        "final_policy",
    }
    require_equal(sorted(value), sorted(fields), "evidence fields")
    require_equal(value["kind"], "retrospective_scored_evidence", "evidence kind")
    require_equal(value["data_kind"], "synthetic", "evidence source posture")
    for key in ("prediction_frozen_at", "first_test_access_at", "final_policy"):
        require_equal(value[key], None, "absent historical " + key)
    _scientific_binding(value)
    _member_bindings(value)
    folds = [
        object_mapping(fold, "fold") for fold in object_list(value["folds"], "folds")
    ]
    methods = [identity(method) for method in object_list(value["methods"], "methods")]
    keys = []
    for unit in object_list(value["units"], "units"):
        row = object_mapping(unit, "unit")
        required = {
            "fold_id",
            "record_id",
            "group_id",
            "method_id",
            "target",
            "producer_target",
            "evaluation_role",
            "eligible_target_kind",
            "status",
            "prediction",
            "prediction_manifest_sha256",
            "fitted_model_sha256",
            "metric",
            "metric_verification",
            "source_row",
            "upstream_prediction",
            "interval",
        }
        require_equal(sorted(row), sorted(required), "evidence unit fields")
        _normalized_unit(row, value)
        keys.append(
            tuple(
                identity(row[key])
                for key in ("fold_id", "record_id", "method_id", "target")
            )
        )
    expected = [
        (identity(fold["fold_id"]), identity(record), method, target)
        for fold in folds
        for record in object_list(fold["test_record_ids"], "records")
        for method in methods
        for target in ("vegetation_cover", "pollen_composition")
    ]
    require_equal(sorted(keys), sorted(set(expected)), "evidence requested universe")
    if type(value["requested_units"]) is not int:
        raise ValidationRefusal(
            "invalid_scored_evidence", "Requested count must be an integer"
        )
    require_equal(value["requested_units"], len(expected), "evidence denominator")


def score_retained_observation(
    row: dict[str, object], prediction: dict[str, object], target: str, local: bool
) -> dict[str, object]:
    if not local:
        observed = row.get("observation")
        return score_observation(
            target,
            prediction,
            None if observed is None else object_mapping(observed, "observation"),
        )
    observed = row.get("observation")
    if observed is None:
        return {"status": "missing_observation", "mae_fraction": None}
    expected_unit = "fraction" if target == "vegetation_cover" else "count"
    require_equal(row.get("observation_unit"), expected_unit, "local observation unit")
    values = object_mapping(observed, "observation")
    vector = {
        key: finite_number(value)
        for key, value in object_mapping(row["prediction"], "prediction").items()
    }
    if target == "vegetation_cover":
        return score_vegetation(
            vector,
            {
                key: None if value is None else finite_number(value)
                for key, value in values.items()
            },
        ).as_dict()
    counts: dict[str, int | None] = {}
    for key, value in values.items():
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int)
        ):
            raise ValidationRefusal("invalid_pollen_counts", key)
        counts[key] = value
    return score_pollen(vector, counts).as_dict()


def _scientific_binding(value: dict[str, object]) -> None:
    require_equal(
        value["source_authentication"],
        "caller_pinned_retained_products; external_source_bytes_not_reopened",
        "source authentication scope",
    )
    for kind in ("prediction", "score"):
        text = value[kind + "_manifest_json"]
        if not isinstance(text, str):
            raise ValidationRefusal(
                "invalid_scored_evidence", "Manifest bytes must be UTF-8 text"
            )
        require_equal(
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
            value[kind + "_manifest_sha256"],
            "exact " + kind + " manifest bytes",
        )
        manifest = object_mapping(
            json.loads(text, object_pairs_hook=_unique_pairs), "original manifest"
        )
        require_equal(
            manifest["schema_version"], "lra-experiment-product.v1", "original schema"
        )
        require_equal(manifest["status"], "generated_exploratory", "original status")
        require_equal(
            manifest["scientific_acceptance"], "not_evaluated", "original acceptance"
        )
        require_equal(
            manifest["scientific_content_sha256"],
            value[kind + "_scientific_content_sha256"],
            "original scientific digest",
        )
        require_equal(
            manifest["scientific_payload"],
            value[kind + "_scientific_payload"],
            "original scientific body",
        )
        require_equal(manifest["profile"], value["profile"], "original profile")
        require_equal(
            manifest["phase"],
            "predictions" if kind == "prediction" else "scores",
            "original phase",
        )
    prediction = object_mapping(
        value["prediction_scientific_payload"], "prediction scientific payload"
    )
    score = object_mapping(
        value["score_scientific_payload"], "score scientific payload"
    )
    require_equal(
        manifest_sha256(prediction),
        value["prediction_scientific_content_sha256"],
        "prediction scientific identity",
    )
    require_equal(
        manifest_sha256(score),
        value["score_scientific_content_sha256"],
        "score scientific identity",
    )
    stem = "predictions" if value["profile"] == TEMPORAL_PROFILE else "prediction"
    require_equal(
        score[stem + "_manifest_sha256"],
        value["prediction_manifest_sha256"],
        "score parent identity",
    )
    require_equal(
        score[stem + "_scientific_content_sha256"],
        value["prediction_scientific_content_sha256"],
        "score numerical parent",
    )
    require_equal(score["profile"], value["profile"], "score profile")
    require_equal(score["scientific_acceptance"], "not_evaluated", "score posture")
    rows = [
        object_mapping(unit, "unit")["source_row"]
        for unit in object_list(value["units"], "units")
    ]
    require_equal(
        sorted(rows, key=canonical_json),
        sorted(object_list(score["scores"], "scores"), key=canonical_json),
        "complete retained score bodies",
    )
    original_folds = prediction.get("folds")
    require_equal(
        sorted(object_list(value["folds"], "folds"), key=canonical_json),
        sorted(object_list(original_folds, "original folds"), key=canonical_json),
        "original fold identity",
    )


def _normalized_unit(unit: dict[str, object], evidence: dict[str, object]) -> None:
    row = object_mapping(unit["source_row"], "source row")
    profile = evidence["profile"]
    temporal, local = profile == TEMPORAL_PROFILE, profile == LOCAL_PROFILE
    method_key = "baseline" if "baseline" in row else "method"
    for name in ("fold_id", "record_id", "group_id"):
        require_equal(unit[name], row[name], "projected " + name)
    require_equal(unit["method_id"], row[method_key], "projected method")
    wire_target = identity(row["target"])
    target = (
        "pollen_composition" if temporal and wire_target == "pollen" else wire_target
    )
    require_equal(unit["target"], target, "projected target")
    require_equal(unit["producer_target"], wire_target, "original target")
    metric = object_mapping(row["metrics" if temporal else "score"], "metric")
    require_equal(unit["metric"], metric, "projected metric")
    require_equal(
        unit["status"],
        "prediction_failed"
        if metric["status"] == "failed_prediction"
        else metric["status"],
        "projected status",
    )
    require_equal(
        unit["eligible_target_kind"],
        not (local and target == "pollen_composition"),
        "target observation channel",
    )
    role = (
        LOCAL_EVALUATION_ROLES[target]
        if local
        else (
            "heldout_younger_pollen"
            if target == "pollen_composition"
            else "heldout_younger_vegetation"
        )
        if temporal
        else "heldout_prediction"
    )
    require_equal(unit["evaluation_role"], role, "projected role")
    require_equal(unit["interval"], None, "absent predictive interval")
    scientific = object_mapping(
        evidence["prediction_scientific_payload"], "prediction evidence"
    )
    candidates = [
        object_mapping(item, "prediction")
        for item in object_list(scientific["predictions"], "predictions")
    ]
    matches = [
        item
        for item in candidates
        if item["fold_id"] == unit["fold_id"]
        and item["record_id"] == unit["record_id"]
        and item.get("method", item.get("baseline")) == unit["method_id"]
    ]
    if len(matches) > 1:
        raise ValidationRefusal(
            "invalid_scored_evidence", "Duplicate original prediction"
        )
    prediction = matches[0] if matches else None
    require_equal(
        unit["upstream_prediction"], prediction, "retained original prediction"
    )
    require_equal(
        unit["fitted_model_sha256"],
        None if prediction is None else prediction.get("model_sha256"),
        "retained fitted identity",
    )
    digest = None if prediction is None else prediction["prediction_manifest_sha256"]
    require_equal(
        unit["prediction_manifest_sha256"], digest, "projected prediction identity"
    )
    require_equal(
        row.get("prediction_manifest_sha256"), digest, "source prediction identity"
    )
    vector = (
        None
        if prediction is None
        else prediction[
            "vegetation_fraction" if target == "vegetation_cover" else "pollen_fraction"
        ]
    )
    require_equal(unit["prediction"], vector, "projected prediction values")
    if prediction is None:
        require_equal(
            unit["status"], "prediction_failed", "missing original prediction"
        )
        verification = "parent_prediction_absence_confirmed"
    elif metric["status"] in {"observation_refused", "refused_observation"}:
        verification = (
            "existing_metric_refusal_recomputed"
            if row.get("observation") is not None
            else "retained_source_refusal_not_reexecuted"
        )
        if row.get("observation") is not None:
            try:
                score_retained_observation(row, prediction, target, local)
            except ValidationRefusal as exc:
                require_equal(
                    metric["reason_code"], exc.reason_code, "replayed metric refusal"
                )
            else:
                raise ValidationRefusal(
                    "invalid_scored_evidence", "Rewritten metric refusal"
                )
    else:
        require_equal(
            metric,
            score_retained_observation(row, prediction, target, local),
            "replayed retained metric",
        )
        verification = "existing_metric_recomputed"
    require_equal(
        unit["metric_verification"], verification, "metric verification scope"
    )


def _member_bindings(value: dict[str, object]) -> None:
    """Bind parsed catalogue/access projections to already retained member bytes."""
    bindings = (
        ("prediction", "experiment.json", "source_catalogue"),
        ("score", "outcome_inventory.json", "outcome_inventory"),
        ("score", "outcome_access.json", "outcome_access"),
    )
    members = object_mapping(value["retained_member_json"], "retained member text")
    require_equal(
        sorted(members),
        sorted(kind + "/" + name for kind, name, _ in bindings),
        "retained member universe",
    )
    for kind, name, projection in bindings:
        text = members[kind + "/" + name]
        manifest_text = value[kind + "_manifest_json"]
        if not isinstance(manifest_text, str):
            raise ValidationRefusal(
                "invalid_scored_evidence", "Retained manifest must be UTF-8 text"
            )
        manifest = object_mapping(
            json.loads(manifest_text, object_pairs_hook=_unique_pairs), "manifest"
        )
        if not isinstance(text, str):
            raise ValidationRefusal(
                "invalid_scored_evidence", "Retained member must be UTF-8 text"
            )
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        require_equal(
            digest,
            object_mapping(manifest["files"], "file inventory")[name],
            "retained member byte identity",
        )
        require_equal(
            json.loads(text, object_pairs_hook=_unique_pairs),
            value[projection],
            "parsed " + projection,
        )
