"""Separate outcome access after verified prediction publication."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from ..contracts import ValidationRefusal, finite_number, manifest_sha256
from .configuration import (
    BLOCK_BASELINE_METHOD,
    BLOCK_PROFILE,
    FITTED_PROFILE,
    SOURCE_PROFILE,
    InputReference,
    identity,
    object_list,
    object_mapping,
)
from .inputs import SAMPLE_FIELDS, read_reference
from .outputs import (
    ExperimentProduct,
    publish_phase,
    read_experiment_product,
    read_member,
    stage_directory,
    write_json,
)
from .reading import read_scoring_predictions
from .reading import read_withheld_predictions as read_withheld_predictions
from .score_values import score_observation as _score


def score_experiment_predictions(
    predictions: Path,
    *,
    expected_manifest_sha256: str,
    outcome_root: Path,
    outcome_inventory: Mapping[str, object],
    destination: Path,
    purpose: str = "exploratory",
) -> ExperimentProduct:
    """Score declared withheld targets separately after prediction authentication."""
    if purpose != "exploratory":
        raise ValidationRefusal(
            "final_experiment_not_implemented",
            "A qualified frozen policy/evaluator is required before final outcomes",
        )
    inventory = object_mapping(outcome_inventory, "outcome_inventory")
    if inventory.get("schema_version") == "lra-local-pollen-outcomes.v1":
        from .assimilation import _score_local_pollen_predictions

        return _score_local_pollen_predictions(
            predictions,
            expected_manifest_sha256=expected_manifest_sha256,
            outcome_root=outcome_root,
            outcome_inventory=inventory,
            destination=destination,
        )

    source_inventory = inventory.get("data_kind") == "source_observations"
    if set(inventory) != {"schema_version", "data_kind", "records"} or (
        inventory["schema_version"],
        inventory["data_kind"],
    ) not in {
        ("lra-experiment-outcomes.v1", "synthetic"),
        ("lra-source-pollen-outcomes.v1", "source_observations"),
    }:
        raise ValidationRefusal(
            "unsupported_experiment_outcomes",
            "Declare a supported outcome inventory and source posture",
        )
    references = {
        identity(key): InputReference.parse(value, key)
        for key, value in object_mapping(inventory["records"], "records").items()
    }
    product, manifest, folds, prediction_rows, methods, ownership = (
        read_scoring_predictions(
            predictions, expected_manifest_sha256=expected_manifest_sha256
        )
    )
    catalogue = {
        identity(record)
        for fold in folds.values()
        for record in object_list(fold["test_record_ids"], "test_record_ids")
    }
    if not set(references).issubset(catalogue):
        raise ValidationRefusal(
            "unknown_experiment_outcome",
            "Outcome references must name held-out catalogue records",
        )
    profile = identity(manifest["profile"])
    if source_inventory != (profile == SOURCE_PROFILE):
        raise ValidationRefusal(
            "experiment_outcome_profile_mismatch",
            "Outcome source posture differs from the prediction profile",
        )
    source_taxa: tuple[str, ...] = ()
    source_sites: dict[str, dict[str, object]] = {}
    if source_inventory:
        metadata = object_mapping(read_member(product, "experiment.json"), "experiment")
        source_taxa = tuple(
            identity(taxon)
            for taxon in object_list(
                object_mapping(metadata["request_template"], "request_template")[
                    "taxa"
                ],
                "taxa",
            )
        )
        source_sites = {
            identity(site["record_id"]): site
            for value in object_list(metadata["source_catalogue"], "source_catalogue")
            if (site := object_mapping(value, "site"))
        }
        for record_id, reference in references.items():
            declared_site = source_sites.get(record_id)
            if declared_site is None or (
                reference.path != declared_site["raw_path"]
                or reference.sha256 != declared_site["raw_sha256"]
            ):
                raise ValidationRefusal(
                    "source_outcome_reference_mismatch",
                    "Observed pollen must reopen the exact declared raw source",
                )
    method_field = (
        "method" if profile in {FITTED_PROFILE, BLOCK_PROFILE} else "baseline"
    )
    targets = (
        ("pollen_composition",)
        if source_inventory
        else ("vegetation_cover", "pollen_composition")
    )
    stage = stage_directory(destination)
    scores: list[dict[str, object]] = []
    observations: dict[str, dict[str, object]] = {}
    observation_errors: dict[str, ValidationRefusal] = {}
    accesses: list[dict[str, object]] = []
    requested_targets = [
        (fold_id, identity(record))
        for fold_id, fold in sorted(folds.items())
        for record in object_list(fold["test_record_ids"], "test_record_ids")
    ]
    for fold_id, record_id in requested_targets:
        record_ids = [record_id]
        group_id = ownership[record_id]
        for method in methods:
            prediction = prediction_rows.get((fold_id, record_id, method))
            outcome = None
            if prediction is not None and record_id in references:
                assert record_id is not None
                if (
                    record_id not in observations
                    and record_id not in observation_errors
                ):
                    accesses.append(
                        {
                            "record_id": record_id,
                            "observation_sha256": references[record_id].sha256,
                            "prediction_manifest_sha256": product.manifest_sha256,
                            "ordering": "verified_published_predictions_before_outcome_open",
                        }
                    )
                    write_json(stage, "outcome_access.json", accesses)
                    try:
                        value = read_reference(outcome_root, references[record_id])
                        if source_inventory:
                            site = source_sites[record_id]
                            sample = object_mapping(value.get("sample"), "sample")
                            counts = object_list(sample.get("counts"), "counts")
                            if (
                                set(value) != {"data_kind", "taxa", "sample"}
                                or value["data_kind"] != "source_observations"
                                or value["taxa"] != list(source_taxa)
                                or set(sample) != SAMPLE_FIELDS | {"counts"}
                                or sample.get("site_id") != site["site_id"]
                                or sample.get("bin_id") != prediction["bin_id"]
                                or len(counts) != len(source_taxa)
                                or any(
                                    type(count) is not int or count < 0
                                    for count in counts
                                )
                                or not 0
                                < sum(cast(int, count) for count in counts)
                                <= 2**53
                            ):
                                raise ValidationRefusal(
                                    "observation_identity_mismatch", record_id
                                )
                            identity(sample["sample_id"])
                            value = {
                                "schema_version": "lra-source-pollen-observation.v1",
                                "data_kind": "source_observations",
                                "record_id": record_id,
                                "sample_id": sample["sample_id"],
                                "bin_id": sample["bin_id"],
                                "pollen_unit": "count",
                                "pollen_count": dict(
                                    zip(source_taxa, counts, strict=True)
                                ),
                                "source_raw_sha256": references[record_id].sha256,
                            }
                        elif (
                            set(value)
                            != {
                                "schema_version",
                                "data_kind",
                                "record_id",
                                "bin_id",
                                "vegetation_unit",
                                "pollen_unit",
                                "vegetation_fraction",
                                "pollen_count",
                            }
                            or value["schema_version"]
                            != "lra-experiment-observation.v1"
                            or value["data_kind"] != "synthetic"
                            or value["record_id"] != record_id
                            or value["bin_id"] != prediction["bin_id"]
                        ):
                            raise ValidationRefusal(
                                "observation_identity_mismatch", record_id
                            )
                        observations[record_id] = value
                    except ValidationRefusal as exc:
                        observation_errors[record_id] = exc
                outcome = observations.get(record_id)
            for target in targets:
                row: dict[str, object] = {
                    "fold_id": fold_id,
                    "group_id": group_id,
                    "record_id": record_id,
                    "record_ids": record_ids,
                    method_field: method,
                    "target": target,
                    "error_unit": "fraction",
                    "bin_id": None if prediction is None else prediction["bin_id"],
                }
                if source_inventory:
                    row["evaluation_role"] = "heldout_pollen_prediction"
                if profile in {FITTED_PROFILE, BLOCK_PROFILE}:
                    method_kind = (
                        "admitted_reconstruction_training_mean"
                        if method == BLOCK_BASELINE_METHOD
                        else "fitted_spatial"
                    )
                    row.update(
                        method_kind=method_kind,
                        evaluation_role="heldout_prediction",
                    )
                if prediction is None:
                    row["score"] = {"status": "prediction_failed", "mae_fraction": None}
                else:
                    try:
                        if record_id in observation_errors:
                            raise observation_errors[record_id]
                        row["score"] = _score(target, prediction, outcome)
                    except ValidationRefusal as exc:
                        row["score"] = {
                            "status": "observation_refused",
                            "reason_code": exc.reason_code,
                            "detail": str(exc),
                            "mae_fraction": None,
                        }
                    row["prediction_manifest_sha256"] = prediction[
                        "prediction_manifest_sha256"
                    ]
                    row["prediction"] = prediction[
                        "vegetation_fraction"
                        if target == "vegetation_cover"
                        else "pollen_fraction"
                    ]
                if record_id in references and outcome is not None:
                    row["observation_sha256"] = references[record_id].sha256
                    row["observation_reference"] = {
                        "path": references[record_id].path,
                        "sha256": references[record_id].sha256,
                    }
                    row["observation"] = outcome
                scores.append(row)
    summaries = []
    for method in methods:
        for target in targets:
            values = [
                object_mapping(row["score"], "score")
                for row in scores
                if row[method_field] == method and row["target"] == target
            ]
            statuses = sorted({identity(value["status"]) for value in values})
            finite_errors = [
                finite_number(value["mae_fraction"])
                for value in values
                if value["status"] == "scored"
            ]
            summaries.append(
                {
                    method_field: method,
                    "target": target,
                    "scoring_unit": "heldout_group_within_original_spatial_block"
                    if profile == BLOCK_PROFILE
                    else "outer_site_group",
                    "independence": "within_block_targets_correlated_and_training_blocks_overlap"
                    if profile == BLOCK_PROFILE
                    else "overlapping_training_cv_not_independent_fixed_model",
                    "requested": len(requested_targets),
                    "by_status": {
                        status: sum(value["status"] == status for value in values)
                        for status in statuses
                    },
                    "mean_mae_fraction": sum(finite_errors) / len(finite_errors)
                    if finite_errors
                    else None,
                    "scored": len(finite_errors),
                    "zero_probability_positive_count": sum(
                        value.get("zero_probability_positive_count") is True
                        for value in values
                    ),
                    "interval_coverage": None,
                    "uncertainty_status": "intervals_not_implemented",
                }
            )
    paired = _paired_baseline_differences(scores, method_field, methods)
    read_experiment_product(
        predictions, expected_manifest_sha256=expected_manifest_sha256
    )
    scientific: dict[str, object] = {
        "profile": profile,
        "prediction_manifest_sha256": product.manifest_sha256,
        "prediction_scientific_content_sha256": product.scientific_content_sha256,
        "outcome_inventory_sha256": manifest_sha256(inventory),
        "scores": scores,
        "summaries": summaries,
        "paired_baseline_differences": paired,
        "uncertainty_status": "intervals_not_implemented",
        "scientific_acceptance": "not_evaluated",
    }
    for name, member in (
        ("scores.json", scores),
        ("summaries.json", summaries),
        ("paired_baseline_differences.json", paired),
        ("outcome_inventory.json", inventory),
        ("outcome_access.json", accesses),
    ):
        write_json(stage, name, member)
    return publish_phase(
        stage, destination, phase="scores", scientific=scientific, profile=profile
    )


def _paired_baseline_differences(
    scores: list[dict[str, object]], method_field: str, methods: tuple[str, ...]
) -> list[dict[str, object]]:
    """Compare each prediction only with its own record's training-mean row."""
    if "training_mean" not in methods:
        return []
    indexed = {
        (
            str(row["fold_id"]),
            str(row["record_id"]),
            str(row[method_field]),
            str(row["target"]),
        ): row
        for row in scores
    }
    paired = []
    for row in scores:
        if row[method_field] == "training_mean":
            continue
        reference = indexed[
            (
                str(row["fold_id"]),
                str(row["record_id"]),
                "training_mean",
                str(row["target"]),
            )
        ]
        actual_score = object_mapping(row["score"], "score")
        baseline_score = object_mapping(reference["score"], "score")
        if actual_score["status"] == baseline_score["status"] == "scored":
            paired.append(
                {
                    "fold_id": row["fold_id"],
                    "group_id": row["group_id"],
                    "record_id": row["record_id"],
                    "baseline": row[method_field],
                    "reference_baseline": "training_mean",
                    "target": row["target"],
                    "mae_improvement_fraction": finite_number(
                        baseline_score["mae_fraction"]
                    )
                    - finite_number(actual_score["mae_fraction"]),
                }
            )
    return paired
