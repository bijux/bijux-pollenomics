"""Caller-pinned retained score admission without original outcome-source access."""

from __future__ import annotations

from pathlib import Path

from ...contracts import (
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from ...temporal.persistence.configuration import METHOD as TEMPORAL_METHOD
from ...temporal.persistence.reading import read_temporal_persistence_predictions
from ..configuration import (
    BLOCK_BASELINE_METHOD,
    BLOCK_PROFILE,
    FITTED_PROFILE,
    LOCAL_EVALUATION_ROLES,
    LOCAL_METHOD,
    LOCAL_PROFILE,
    TEMPORAL_PROFILE,
    InputReference,
    identity,
    object_list,
    object_mapping,
)
from ..outputs import (
    local_prediction_rows,
    read_experiment_product,
    read_member,
)
from .evidence import ScoredExperimentEvidence as ScoredExperimentEvidence
from .evidence import score_retained_observation as _metric
from .products import read_scoring_predictions
from .score_ledger import RetainedPredictionLedger as _Parent
from .score_ledger import require_equal as _equal
from .score_ledger import validate_outcome_access as _accesses
from .score_ledger import validate_score_summaries as _summaries


def _parent(directory: Path, expected: str) -> _Parent:
    product, manifest = read_experiment_product(
        directory, expected_manifest_sha256=expected
    )
    if manifest["profile"] == TEMPORAL_PROFILE:
        _, spec, scientific = read_temporal_persistence_predictions(
            directory, expected_manifest_sha256=expected
        )
        fold = spec.temporal_plan.fold
        rows = {
            (fold.fold_id, identity(row["record_id"]), TEMPORAL_METHOD): row
            for value in object_list(scientific["predictions"], "predictions")
            for row in [object_mapping(value, "prediction")]
        }
        source = object_mapping(scientific["source_admission"], "source admission")
        geometries = object_mapping(source["geometries"], "geometries")
        observation_context = {
            site.record.record_id: {
                "data_kind": "synthetic",
                "purpose": "exploratory",
                "record_id": site.record.record_id,
                "geometry_sha256": site.geometry.sha256,
                "sample_metadata": object_mapping(
                    geometries[site.record.record_id], "geometry"
                )["sample_metadata"],
                "taxa": spec.older_experiment.template()["taxa"],
            }
            for site in spec.older_experiment.sites
            if site.record.record_id in fold.test_record_ids
        }
        return _Parent(
            product,
            manifest,
            {fold.fold_id: fold.as_dict()},
            rows,
            (TEMPORAL_METHOD,),
            dict(spec.temporal_plan.record_groups),
            observation_context,
        )

    if manifest["profile"] == LOCAL_PROFILE:
        folds, values = local_prediction_rows(
            manifest,
            read_member(product, "predictions.json"),
            object_mapping(read_member(product, "experiment.json"), "experiment")[
                "observation_channels"
            ],
        )
        rows = {
            (fold, identity(row["record_id"]), LOCAL_METHOD): row
            for fold, row in values.items()
        }
        ownership = {
            identity(object_list(fold["test_record_ids"], "test records")[0]): identity(
                object_list(fold["test_group_ids"], "test groups")[0]
            )
            for fold in folds.values()
        }
        return _Parent(product, manifest, folds, rows, (LOCAL_METHOD,), ownership)
    return _Parent(
        *read_scoring_predictions(directory, expected_manifest_sha256=expected)
    )


def _references(
    inventory: dict[str, object], parent: _Parent
) -> dict[str, dict[str, object]]:
    temporal = parent.manifest["profile"] == TEMPORAL_PROFILE
    expected_schema = (
        "lra-local-pollen-outcomes.v1"
        if parent.manifest["profile"] == LOCAL_PROFILE
        else "lra-experiment-outcomes.v1"
    )
    if temporal:
        _equal(
            sorted(inventory),
            sorted(
                {
                    "schema_version",
                    "data_kind",
                    "purpose",
                    "predictions_manifest_sha256",
                    "records",
                }
            ),
            "temporal inventory fields",
        )
        _equal(
            inventory["schema_version"], "lra-temporal-outcomes.v1", "inventory schema"
        )
        _equal(inventory["purpose"], "exploratory", "inventory purpose")
        _equal(
            inventory["predictions_manifest_sha256"],
            parent.product.manifest_sha256,
            "inventory parent",
        )
        pairs = []
        for value in object_list(inventory["records"], "records"):
            row = object_mapping(value, "reference")
            _equal(
                sorted(row), sorted({"record_id", "observation"}), "reference fields"
            )
            pairs.append((identity(row["record_id"]), row["observation"]))
    else:
        _equal(
            sorted(inventory),
            sorted({"schema_version", "data_kind", "records"}),
            "inventory fields",
        )
        _equal(inventory["schema_version"], expected_schema, "inventory schema")
        pairs = list(object_mapping(inventory["records"], "records").items())
    _equal(inventory["data_kind"], "synthetic", "inventory data kind")
    result: dict[str, dict[str, object]] = {}
    for key, value in pairs:
        if key in result or key not in parent.ownership:
            raise ValidationRefusal(
                "retained_score_mismatch", "unknown/duplicate observation record"
            )
        ref = InputReference.parse(value, key)
        result[key] = {"path": ref.path, "sha256": ref.sha256}
    return result


def _row(
    value: object, parent: _Parent, refs: dict[str, dict[str, object]]
) -> tuple[tuple[str, str, str, str], dict[str, object]]:
    row = object_mapping(value, "score row")
    profile = parent.manifest["profile"]
    local, temporal = profile == LOCAL_PROFILE, profile == TEMPORAL_PROFILE
    method_field = (
        "method"
        if profile in {FITTED_PROFILE, BLOCK_PROFILE, LOCAL_PROFILE, TEMPORAL_PROFILE}
        else "baseline"
    )
    if ("baseline" in row) == ("method" in row):
        raise ValidationRefusal("retained_score_mismatch", "ambiguous method field")
    fold, record, method = (
        identity(row[key]) for key in ("fold_id", "record_id", method_field)
    )
    wire_target = identity(row["target"])
    target = (
        "pollen_composition" if temporal and wire_target == "pollen" else wire_target
    )
    if target not in {"vegetation_cover", "pollen_composition"} or (
        temporal and wire_target == "pollen_composition"
    ):
        raise ValidationRefusal("retained_score_mismatch", "target/profile")
    _equal(row["group_id"], parent.ownership.get(record), "record group")
    if not local and not temporal:
        _equal(row["record_ids"], [record], "score row ownership")
    prediction = parent.rows.get((fold, record, method))
    metric = object_mapping(row["metrics" if temporal else "score"], "metric")
    status = identity(metric["status"])
    role = "heldout_prediction"
    if local:
        role = LOCAL_EVALUATION_ROLES[target]
        _equal(row.get("evaluation_role"), role, "local target role")
        _equal(
            row.get("eligible_for_heldout_acceptance"),
            target == "vegetation_cover",
            "local eligibility",
        )
        _equal(row.get("method_kind"), "local_pollen_assimilation", "local method kind")
    elif temporal:
        role = (
            "heldout_younger_vegetation"
            if target == "vegetation_cover"
            else "heldout_younger_pollen"
        )
        _equal(row.get("evaluation_role"), role, "temporal target role")
    elif profile in {FITTED_PROFILE, BLOCK_PROFILE}:
        _equal(row.get("evaluation_role"), role, "fitted role")
        method_kind = (
            "admitted_reconstruction_training_mean"
            if method == BLOCK_BASELINE_METHOD
            else "fitted_spatial"
        )
        _equal(row.get("method_kind"), method_kind, "method kind")
    if not temporal:
        _equal(row.get("error_unit"), "fraction", "error unit")
    verification = "existing_metric_recomputed"
    vector = None
    if prediction is None:
        expected = (
            {
                "status": "failed_prediction",
                "reason_code": "temporal_prediction_unavailable",
            }
            if temporal
            else {"status": "prediction_failed", "mae_fraction": None}
        )
        _equal(metric, expected, "absent prediction accounting")
        if any(
            row.get(key) is not None
            for key in ("prediction", "prediction_manifest_sha256", "observation")
        ):
            raise ValidationRefusal(
                "retained_score_mismatch", "missing prediction has invented values"
            )
        verification = "parent_prediction_absence_confirmed"
    else:
        _equal(
            row.get("prediction_manifest_sha256"),
            prediction["prediction_manifest_sha256"],
            "prediction digest",
        )
        vector = prediction[
            "vegetation_fraction" if target == "vegetation_cover" else "pollen_fraction"
        ]
        if not temporal:
            _equal(row.get("prediction"), vector, "prediction values")
        _equal(row.get("bin_id"), prediction["bin_id"], "prediction bin")
        observed = row.get("observation")
        if local and target == "pollen_composition":
            _equal(
                observed, prediction["observed_pollen_count"], "admitted local pollen"
            )
            _equal(
                row.get("observation_reference"),
                prediction["observed_local_pollen_source"],
                "local pollen source",
            )
        elif observed is not None:
            _equal(
                row.get("observation_reference"),
                refs.get(record),
                "observation source declaration",
            )
            if not local:
                outcome = object_mapping(observed, "observation")
                _equal(outcome["record_id"], record, "observation owner")
                _equal(outcome["data_kind"], "synthetic", "observation posture")
                expected_context = (
                    parent.observation_context[record]
                    if temporal
                    else {
                        "schema_version": "lra-experiment-observation.v1",
                        "data_kind": "synthetic",
                        "record_id": record,
                        "bin_id": prediction["bin_id"],
                    }
                )
                _equal(
                    sorted(outcome),
                    sorted(
                        {
                            *expected_context,
                            "vegetation_unit",
                            "pollen_unit",
                            "vegetation_fraction",
                            "pollen_count",
                        }
                    ),
                    "observation fields",
                )
                for field, declared in expected_context.items():
                    _equal(outcome[field], declared, "observation " + field)
                if not temporal:
                    _equal(outcome["bin_id"], prediction["bin_id"], "observation bin")
                    _equal(
                        row.get("observation_sha256"),
                        refs.get(record, {}).get("sha256"),
                        "observation SHA",
                    )
        if status in {"observation_refused", "refused_observation"}:
            if record not in refs:
                raise ValidationRefusal(
                    "retained_score_mismatch",
                    "source refusal without a declared source",
                )
            identity(metric["reason_code"])
            identity(metric["detail"])
            if observed is not None:
                try:
                    _metric(row, prediction, target, local)
                except ValidationRefusal as exc:
                    _equal(
                        metric["reason_code"],
                        exc.reason_code,
                        "retained metric refusal",
                    )
                else:
                    raise ValidationRefusal(
                        "retained_score_mismatch",
                        "scorable retained observation was refused",
                    )
            verification = (
                "existing_metric_refusal_recomputed"
                if observed is not None
                else "retained_source_refusal_not_reexecuted"
            )
        else:
            _equal(
                metric,
                _metric(row, prediction, target, local),
                "complete descriptive metric",
            )
    return (fold, record, method, target), {
        "fold_id": fold,
        "record_id": record,
        "group_id": row["group_id"],
        "method_id": method,
        "target": target,
        "producer_target": wire_target,
        "evaluation_role": role,
        "eligible_target_kind": not (local and target == "pollen_composition"),
        "status": "prediction_failed" if status == "failed_prediction" else status,
        "prediction": vector,
        "prediction_manifest_sha256": None
        if prediction is None
        else prediction["prediction_manifest_sha256"],
        "fitted_model_sha256": None
        if prediction is None
        else prediction.get("model_sha256"),
        "metric": metric,
        "metric_verification": verification,
        "source_row": row,
        "upstream_prediction": prediction,
        "interval": None,
    }


def read_scored_experiment_evidence(
    predictions: Path,
    *,
    expected_prediction_manifest_sha256: str,
    scores: Path,
    expected_scores_manifest_sha256: str,
) -> ScoredExperimentEvidence:
    """Join pinned retained products; no source files, models, clocks or final approval."""
    try:
        # Authenticate both caller identities before decoding any numerical members.
        read_experiment_product(
            predictions, expected_manifest_sha256=expected_prediction_manifest_sha256
        )
        product, manifest = read_experiment_product(
            scores, expected_manifest_sha256=expected_scores_manifest_sha256
        )
        parent = _parent(predictions, expected_prediction_manifest_sha256)
        profile = parent.manifest["profile"]
        _equal(manifest["profile"], profile, "score profile")
        _equal(manifest["phase"], "scores", "score phase")
        scientific = object_mapping(
            manifest["scientific_payload"], "scientific payload"
        )
        temporal = profile == TEMPORAL_PROFILE
        stem = "predictions" if temporal else "prediction"
        _equal(
            scientific[stem + "_manifest_sha256"],
            parent.product.manifest_sha256,
            "score parent",
        )
        _equal(
            scientific[stem + "_scientific_content_sha256"],
            parent.product.scientific_content_sha256,
            "scientific parent",
        )
        _equal(scientific["profile"], profile, "scientific profile")
        _equal(
            scientific["scientific_acceptance"], "not_evaluated", "scientific posture"
        )
        inventory = object_mapping(
            read_member(product, "outcome_inventory.json"), "outcome inventory"
        )
        _equal(
            scientific["outcome_inventory_sha256"],
            manifest_sha256(inventory),
            "outcome inventory identity",
        )
        refs = _references(inventory, parent)
        values = object_list(read_member(product, "scores.json"), "scores")
        _equal(values, scientific["scores"], "retained score member")
        units = {}
        for value in values:
            key, unit = _row(value, parent, refs)
            if key in units:
                raise ValidationRefusal(
                    "retained_score_mismatch", "duplicate score unit"
                )
            units[key] = unit
        expected = {
            (fold_id, identity(record), method, target)
            for fold_id, fold in parent.folds.items()
            for record in object_list(fold["test_record_ids"], "test records")
            for method in parent.methods
            for target in ("vegetation_cover", "pollen_composition")
        }
        _equal(sorted(units), sorted(expected), "complete requested score universe")
        accesses = read_member(product, "outcome_access.json")
        _accesses(accesses, parent, refs)
        _summaries(product, scientific, parent, list(units.values()))
        payload = {
            "schema_version": "pollenomics-scored-evidence.v1",
            "kind": "retrospective_scored_evidence",
            "profile": profile,
            "data_kind": "synthetic",
            "scientific_acceptance": "not_evaluated",
            "prediction_manifest_sha256": parent.product.manifest_sha256,
            "prediction_scientific_content_sha256": parent.product.scientific_content_sha256,
            "score_manifest_sha256": product.manifest_sha256,
            "score_scientific_content_sha256": product.scientific_content_sha256,
            "source_authentication": "caller_pinned_retained_products; external_source_bytes_not_reopened",
            "folds": list(parent.folds.values()),
            "methods": parent.methods,
            "source_catalogue": read_member(parent.product, "experiment.json"),
            "retained_member_json": {
                "prediction/experiment.json": (
                    parent.product.directory / "experiment.json"
                )
                .read_bytes()
                .decode("utf-8"),
                "score/outcome_inventory.json": (
                    product.directory / "outcome_inventory.json"
                )
                .read_bytes()
                .decode("utf-8"),
                "score/outcome_access.json": (product.directory / "outcome_access.json")
                .read_bytes()
                .decode("utf-8"),
            },
            "prediction_scientific_payload": parent.manifest["scientific_payload"],
            "score_scientific_payload": scientific,
            "prediction_manifest_json": (parent.product.directory / "manifest.json")
            .read_bytes()
            .decode("utf-8"),
            "score_manifest_json": (product.directory / "manifest.json")
            .read_bytes()
            .decode("utf-8"),
            "outcome_inventory": inventory,
            "outcome_access": accesses,
            "requested_units": len(expected),
            "units": [units[key] for key in sorted(units)],
            "prediction_frozen_at": None,
            "first_test_access_at": None,
            "final_policy": None,
        }
        for item in (parent.product, product):
            read_experiment_product(
                item.directory, expected_manifest_sha256=item.manifest_sha256
            )
        return ScoredExperimentEvidence(
            canonical_json(payload), manifest_sha256(payload)
        )
    except (KeyError, ValueError, TypeError, IndexError) as exc:
        raise ValidationRefusal("invalid_retained_scores", str(exc)) from exc
