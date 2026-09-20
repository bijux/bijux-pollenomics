"""Separate outcome access after verified prediction publication."""

from __future__ import annotations

from pathlib import Path

from ...contracts import ValidationRefusal
from ..configuration import (
    BLOCK_METHODS,
    FITTED_PROFILE,
    PROFILE,
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
    if manifest["profile"] not in {PROFILE, FITTED_PROFILE}:
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
