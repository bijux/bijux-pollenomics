"""Separate outcome access after verified prediction publication."""

from __future__ import annotations

from pathlib import Path

from ...contracts import (
    Fold,
    TrainingAdmission,
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from ...splits import grouped_block_holdouts, grouped_leave_one_out, split_manifest
from ..block_assimilation import validate_block_local_prediction_row
from ..configuration import (
    BLOCK_LOCAL_PROFILE,
    BLOCK_METHODS,
    FITTED_PROFILE,
    LOCAL_EVALUATION_ROLES,
    LOCAL_METHOD,
    PROFILE,
    SOURCE_PROFILE,
    SpatialBlockLocalPollenSpec,
    identity,
    object_list,
    object_mapping,
)
from ..outputs import (
    ExperimentProduct,
    read_experiment_product,
    read_member,
)
from .blocks import _block_predictions
from .metadata import validate_singleton_metadata
from .provenance import validate_singleton_provenance
from .rows import _predictions


def _same_outer_fold(left: object, right: object) -> bool:
    """Compare canonical JSON values rather than tuple/list representations."""
    return canonical_json(left) == canonical_json(right)


def _block_local_predictions(
    manifest: dict[str, object],
    rows_value: object,
    metadata_value: object,
    split_value: object,
    admissions_value: object,
) -> tuple[dict[str, dict[str, object]], dict[tuple[str, str, str], dict[str, object]]]:
    scientific = object_mapping(manifest["scientific_payload"], "scientific")
    metadata = object_mapping(metadata_value, "experiment")
    if (
        manifest["profile"] != BLOCK_LOCAL_PROFILE
        or manifest["phase"] != "predictions"
        or rows_value != scientific["predictions"]
        or split_value != scientific["split_manifest"]
        or admissions_value != scientific["block_admissions"]
        or scientific["evaluation_roles"] != LOCAL_EVALUATION_ROLES
        or scientific["pollen_eligible_for_heldout_acceptance"] is not False
        or scientific["scientific_acceptance"] != "not_evaluated"
        or scientific["uncertainty_status"]
        != "point_predictions_only_intervals_not_implemented"
        or metadata.get("schema_version") != "lra-spatial-block-local-experiment.v1"
    ):
        raise ValidationRefusal("invalid_block_local_inventory", "Posture differs")
    spec = SpatialBlockLocalPollenSpec(object_mapping(metadata["request"], "request"))
    from ..inputs import channel_catalogue

    catalogue = metadata["observation_channels"]
    if canonical_json(catalogue) != canonical_json(channel_catalogue(spec)):
        raise ValidationRefusal("invalid_block_local_catalogue", "Ownership differs")
    records = [site.record for site in spec.sites]
    retained_split = object_mapping(split_value, "split_manifest")
    folds_source = grouped_block_holdouts(records)
    if (
        canonical_json(split_manifest(records, by_block=True))
        != canonical_json(retained_split)
        or manifest_sha256(retained_split) != scientific["split_manifest_sha256"]
        or canonical_json([fold.as_dict() for fold in folds_source])
        != canonical_json(scientific["folds"])
    ):
        raise ValidationRefusal("invalid_block_local_split", "Split differs")
    ownership = {
        record: fold.test_group_ids[0]
        for fold in grouped_leave_one_out(records)
        for record in fold.test_record_ids
    }
    if object_mapping(scientific["record_groups"], "groups") != ownership:
        raise ValidationRefusal("invalid_block_local_catalogue", "Groups differ")
    retained_folds = {
        identity(row["fold_id"]): row
        for value in object_list(scientific["folds"], "folds")
        if (row := object_mapping(value, "fold"))
    }
    folds: dict[str, dict[str, object]] = {}
    typed_admissions: dict[str, TrainingAdmission] = {}
    ordered: list[tuple[str, str, str]] = []
    admissions = object_mapping(admissions_value, "admissions")
    from ..fitted.admission import retained_training_admission

    for fold in folds_source:
        outer = retained_folds[fold.fold_id]
        folds[fold.fold_id] = outer
        ordered.extend(
            (fold.fold_id, record, LOCAL_METHOD) for record in fold.test_record_ids
        )
        if fold.fold_id in admissions:
            retained = retained_training_admission(admissions[fold.fold_id], fold)
            if dict(retained.record_groups) != ownership:
                raise ValidationRefusal(
                    "block_admission_identity_mismatch", fold.fold_id
                )
            typed_admissions[fold.fold_id] = retained
    if not set(admissions).issubset(folds):
        raise ValidationRefusal("invalid_block_local_admission", "Unknown fold")
    expected = set(ordered)
    predictions = {}
    for value in object_list(rows_value, "predictions"):
        row = object_mapping(value, "prediction")
        key = (
            identity(row["fold_id"]),
            identity(row["record_id"]),
            identity(row["method"]),
        )
        current_admission = typed_admissions.get(key[0])
        if (
            key not in expected
            or key in predictions
            or current_admission is None
            or row.get("profile") != BLOCK_LOCAL_PROFILE
            or row.get("method_kind") != "local_pollen_assimilation"
            or row.get("evaluation_roles") != LOCAL_EVALUATION_ROLES
            or row.get("pollen_eligible_for_heldout_acceptance") is not False
            or row.get("scientific_acceptance") != "not_evaluated"
            or not _same_outer_fold(row.get("outer_fold"), folds[key[0]])
            or manifest_sha256(
                {
                    name: item
                    for name, item in row.items()
                    if name != "prediction_manifest_sha256"
                }
            )
            != row.get("prediction_manifest_sha256")
        ):
            raise ValidationRefusal("invalid_block_local_prediction", ":".join(key))
        retained_outer = folds[key[0]]
        typed_fold = Fold(
            key[0],
            tuple(
                identity(value)
                for value in object_list(
                    retained_outer["train_record_ids"], "train_record_ids"
                )
            ),
            tuple(
                identity(value)
                for value in object_list(
                    retained_outer["test_record_ids"], "test_record_ids"
                )
            ),
            tuple(
                identity(value)
                for value in object_list(
                    retained_outer["train_group_ids"], "train_group_ids"
                )
            ),
            tuple(
                identity(value)
                for value in object_list(
                    retained_outer["test_group_ids"], "test_group_ids"
                )
            ),
        )
        validate_block_local_prediction_row(
            spec, typed_fold, current_admission, row, catalogue
        )
        predictions[key] = row
    failed: set[tuple[str, str, str]] = set()
    failure_status: dict[tuple[str, str, str], str] = {}
    refused, not_run = 0, 0
    for value in object_list(scientific["failures"], "failures"):
        row = object_mapping(value, "failure")
        key = (
            identity(row["fold_id"]),
            identity(row["record_id"]),
            identity(row["method"]),
        )
        if (
            key not in expected
            or key in predictions
            or key in failed
            or row.get("group_id") != ownership[key[1]]
            or row.get("status") not in {"refused", "not_run"}
            or (row.get("status") == "not_run")
            is not (row.get("reason_code") == "experiment_interrupted")
        ):
            raise ValidationRefusal("invalid_block_local_failure", ":".join(key))
        identity(row["reason_code"])
        status = identity(row["status"])
        refused += status == "refused"
        not_run += status == "not_run"
        failed.add(key)
        failure_status[key] = status
    counts = {
        "requested_folds": len(folds),
        "requested_predictions": len(expected),
        "generated_predictions": len(predictions),
        "refused_predictions": refused,
        "not_run_predictions": not_run,
        "failed_predictions": len(failed),
        "failed_folds": len({key[0] for key in failed}),
    }
    terminal: dict[tuple[str, str, str], str] = dict.fromkeys(predictions, "predicted")
    terminal.update(failure_status)
    first_not_run = next(
        (index for index, key in enumerate(ordered) if terminal[key] == "not_run"),
        None,
    )
    if (
        set(predictions) | failed != expected
        or any(
            type(scientific[name]) is not int or scientific[name] != count
            for name, count in counts.items()
        )
        or scientific["all_predictions_generated"] is not (not failed)
        or scientific["interrupted"] is not bool(not_run)
        or (
            first_not_run is not None
            and any(terminal[key] != "not_run" for key in ordered[first_not_run:])
        )
    ):
        raise ValidationRefusal(
            "incomplete_block_local_accounting", "Terminal set differs"
        )
    return folds, predictions


def read_withheld_predictions(
    directory: Path,
    *,
    expected_manifest_sha256: str,
) -> tuple[
    ExperimentProduct,
    dict[str, object],
    dict[str, dict[str, object]],
    dict[tuple[str, str], dict[str, object]],
    tuple[str, ...],
]:
    """Authenticate owned-copy withheld rows; scientific authorship stays unverified."""
    product, manifest = read_experiment_product(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    if manifest["profile"] not in {PROFILE, SOURCE_PROFILE, FITTED_PROFILE}:
        raise ValidationRefusal(
            "experiment_outcome_profile_mismatch",
            "Require an explicit all-target-pollen-withheld profile",
        )
    try:
        folds, predictions, methods = _predictions(
            manifest, read_member(product, "predictions.json")
        )
        metadata = object_mapping(read_member(product, "experiment.json"), "experiment")
        validate_singleton_metadata(
            metadata,
            object_mapping(manifest["scientific_payload"], "scientific_payload"),
            folds,
            predictions,
            methods,
        )
        validate_singleton_provenance(product, manifest, metadata, folds, predictions)
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise ValidationRefusal("invalid_prediction_inventory", str(exc)) from exc
    return product, manifest, folds, predictions, methods


def read_spatial_block_predictions(
    directory: Path,
    *,
    expected_manifest_sha256: str,
) -> tuple[
    ExperimentProduct,
    dict[str, object],
    dict[str, dict[str, object]],
    dict[tuple[str, str, str], dict[str, object]],
    tuple[str, ...],
]:
    """Authenticate multi-target original blocks without changing singleton reader keys."""
    from ..configuration import BLOCK_PROFILE

    product, manifest = read_experiment_product(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    if manifest["profile"] != BLOCK_PROFILE:
        raise ValidationRefusal(
            "experiment_outcome_profile_mismatch",
            "Require the explicit spatial-block profile",
        )
    try:
        folds, rows = _block_predictions(
            manifest, read_member(product, "predictions.json")
        )
        from ..fitted.metadata import validate_block_metadata

        validate_block_metadata(
            read_member(product, "experiment.json"),
            object_mapping(manifest["scientific_payload"], "scientific_payload"),
            folds,
            rows,
            read_member(product, "models.json"),
        )
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise ValidationRefusal("invalid_block_prediction_inventory", str(exc)) from exc
    return product, manifest, folds, rows, BLOCK_METHODS


def read_spatial_block_local_pollen_predictions(
    directory: Path,
    *,
    expected_manifest_sha256: str,
) -> tuple[
    ExperimentProduct,
    dict[str, object],
    dict[str, dict[str, object]],
    dict[tuple[str, str, str], dict[str, object]],
]:
    """Authenticate a complete multi-target block-local exploratory product."""
    from ..configuration import BLOCK_LOCAL_PROFILE

    product, manifest = read_experiment_product(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    if manifest["profile"] != BLOCK_LOCAL_PROFILE:
        raise ValidationRefusal(
            "experiment_outcome_profile_mismatch",
            "Require the explicit spatial-block local-pollen profile",
        )
    try:
        folds, rows = _block_local_predictions(
            manifest,
            read_member(product, "predictions.json"),
            read_member(product, "experiment.json"),
            read_member(product, "split_manifest.json"),
            read_member(product, "block_admissions.json"),
        )
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise ValidationRefusal("invalid_block_local_inventory", str(exc)) from exc
    return product, manifest, folds, rows


def read_scoring_predictions(
    directory: Path,
    *,
    expected_manifest_sha256: str,
) -> tuple[
    ExperimentProduct,
    dict[str, object],
    dict[str, dict[str, object]],
    dict[tuple[str, str, str], dict[str, object]],
    tuple[str, ...],
    dict[str, str],
]:
    """One authoritative intake for scoring; external singleton API stays unchanged."""
    from ..configuration import BLOCK_PROFILE

    _, checked = read_experiment_product(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    if checked["profile"] == BLOCK_PROFILE:
        product, manifest, folds, rows, methods = read_spatial_block_predictions(
            directory, expected_manifest_sha256=expected_manifest_sha256
        )
        ownership = {
            record: identity(group)
            for record, group in object_mapping(
                object_mapping(manifest["scientific_payload"], "scientific_payload")[
                    "record_groups"
                ],
                "record_groups",
            ).items()
        }
        return product, manifest, folds, rows, methods, ownership
    product, manifest, folds, singleton, methods = read_withheld_predictions(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    rows = {
        (fold, identity(value["record_id"]), method): value
        for (fold, method), value in singleton.items()
    }
    ownership = {
        identity(object_list(fold["test_record_ids"], "test_record_ids")[0]): identity(
            object_list(fold["test_group_ids"], "test_group_ids")[0]
        )
        for fold in folds.values()
    }
    return product, manifest, folds, rows, methods, ownership
