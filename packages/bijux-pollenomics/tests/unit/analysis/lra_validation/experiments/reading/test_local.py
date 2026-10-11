"""Grouped local-pollen products bind retained requests before outcome access."""

import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.batches.models import LRABatchItem
from bijux_pollenomics.analysis.lra_validation import (
    ValidationRefusal,
    grouped_leave_one_out,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.contracts import canonical_json
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    LOCAL_EVALUATION_ROLES,
    LOCAL_METHOD,
    LOCAL_PROFILE,
    LocalPollenSpec,
    object_list,
    object_mapping,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
    channel_catalogue,
    local_channel_evidence,
    make_request,
)
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
    publish_phase,
    stage_directory,
    write_json,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reading import local_product

from ..test_assimilation import local_payload


def _engine() -> dict[str, str]:
    return {
        "distribution": "bijux-pollenomics-lra",
        "version": "test",
        "numerical_backend": "python",
        "python_api": "bijux_pollenomics_lra.api",
        "extension_group": "bijux_pollenomics.extensions",
        "extension_name": "lra",
        "extension_target": "bijux_pollenomics_lra.api:extension_descriptor",
    }


def _metadata(spec: LocalPollenSpec) -> dict[str, object]:
    return {
        "profile": LOCAL_PROFILE,
        "method": LOCAL_METHOD,
        "request_template": spec.template(),
        "regional_priority": spec.regional_priority,
        "local_ring_count": spec.local_ring_count,
        "local_support_radius_m": spec.local_support_radius_m,
        "support_profile": spec.support_profile,
        "observation_channels": channel_catalogue(spec),
        "source_catalogue": [
            {
                "record_id": site.record.record_id,
                "site_id": site.record.site_id,
                "identity_keys": site.record.identity_keys,
                "raw_path": site.raw.path,
                "raw_sha256": site.raw.sha256,
                "geometry_path": site.geometry.path,
                "geometry_sha256": site.geometry.sha256,
            }
            for site in spec.sites
        ],
    }


def _fixture(
    root: Path,
    *,
    mutation: str | None = None,
    terminal: tuple[str, ...] | None = None,
) -> ExperimentProduct:
    spec = LocalPollenSpec(local_payload(root / "inputs"))
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    terminal = terminal or tuple("predicted" for _ in folds)
    assert len(terminal) == len(folds)
    by_record = {site.record.record_id: site for site in spec.sites}
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    operations: list[dict[str, Any]] = []
    for fold, status in zip(folds, terminal, strict=True):
        record = fold.test_record_ids[0]
        target = by_record[record]
        anchor_id = next(
            key for key in spec.regional_priority if key in fold.train_record_ids
        )
        anchor = by_record[anchor_id]
        if status != "predicted":
            failures.append(
                {
                    "fold_id": fold.fold_id,
                    "record_ids": list(fold.test_record_ids),
                    "status": status,
                    "reason_code": (
                        "experiment_interrupted"
                        if status == "not_run"
                        else "synthetic_refusal"
                    ),
                }
            )
            continue
        request = make_request(spec, target, anchor, fold, root / "inputs")
        request_sha256 = LRABatchItem(record, request).request_sha256
        counts_list = object_list(
            object_mapping(
                object_list(
                    object_mapping(request["local"], "local")["samples"], "samples"
                )[0],
                "sample",
            )["counts"],
            "counts",
        )
        counts = dict(zip(("Alnus", "Betula"), counts_list, strict=True))
        rings = [
            object_mapping(value, "ring")
            for value in object_list(request["rings"], "rings")
        ]
        scientific_content = hashlib.sha256(record.encode()).hexdigest()
        numerical = {
            "scientific_content_sha256": scientific_content,
            "scientific_identity_sha256": hashlib.sha256(
                (record + ":identity").encode()
            ).hexdigest(),
            "source_radius_label_m": rings[spec.local_ring_count - 1]["mean_m"],
            "local_support_radius_m": spec.local_support_radius_m,
            "support_profile": spec.support_profile,
            "composition": {"Alnus": 0.6, "Betula": 0.4},
        }
        row: dict[str, Any] = {
            "profile": LOCAL_PROFILE,
            "fold_id": fold.fold_id,
            "record_id": record,
            "group_id": fold.test_group_ids[0],
            "bin_id": "test-bin",
            "method": LOCAL_METHOD,
            "method_kind": "local_pollen_assimilation",
            "evaluation_roles": dict(LOCAL_EVALUATION_ROLES),
            "pollen_eligible_for_heldout_acceptance": False,
            "vegetation_fraction": {"Alnus": 0.6, "Betula": 0.4},
            "pollen_fraction": {"Alnus": 0.7, "Betula": 0.3},
            "observed_pollen_count": counts,
            "observed_pollen_unit": "count",
            "channel_admission": local_channel_evidence(spec, fold, target, anchor),
            "outer_fold": fold.as_dict(),
            "observed_local_pollen_source": {
                "record_id": record,
                "group_id": fold.test_group_ids[0],
                "path": target.raw.path,
                "sha256": target.raw.sha256,
                "role": "observed_local_pollen",
            },
            "regional_pollen_source": {
                "record_id": anchor_id,
                "path": anchor.raw.path,
                "sha256": anchor.raw.sha256,
                "role": "training_regional_pollen",
            },
            "unused_training_record_ids": [
                key for key in fold.train_record_ids if key != anchor_id
            ],
            "request_sha256": request_sha256,
            "numerical_product": numerical,
            "target_geometry_sha256": target.geometry.sha256,
            "support_profile": spec.support_profile,
            "local_support_radius_m": spec.local_support_radius_m,
            "preparation_profile": "synthetic-preparation-v1",
            "forward_method_profile": "synthetic-forward-v1",
            "engine_build": _engine(),
            "declared_inversion_rings": [
                {
                    key: value
                    for key, value in ring.items()
                    if key != "geometry_evidence_id"
                }
                for ring in rings
            ],
            "declared_forward_rings": [],
            "regional_cover": [0.5, 0.5],
            "full_k": [[1.0, 1.0]],
            "full_terrestrial_fraction": [1.0],
            "ring_bounds_m": [[0.0, 1000.0]],
            "uncertainty_status": "point_predictions_only_intervals_not_implemented",
        }
        attempt = {
            "item_id": record,
            "request_sha256": request_sha256,
            "request": request,
        }
        operation = {
            "schema_version": "lra-batch-item.v1",
            "index": len(operations),
            "item_id": record,
            "request_sha256": request_sha256,
            "item_status": "completed",
            "scientific_acceptance": "not_evaluated",
            "product": {
                "directory": "/retained/" + record,
                "manifest_sha256": hashlib.sha256(
                    (record + ":manifest").encode()
                ).hexdigest(),
                "scientific_content_sha256": scientific_content,
            },
            "cache_key": request_sha256,
            "cache_hit": False,
        }
        rows.append(row)
        attempts.append(attempt)
        operations.append(operation)

    if mutation == "request_count":
        request = attempts[0]["request"]
        request["local"]["samples"][0]["counts"][0] += 1
        digest = LRABatchItem(str(attempts[0]["item_id"]), request).request_sha256
        attempts[0]["request_sha256"] = digest
        operations[0]["request_sha256"] = digest
        rows[0]["request_sha256"] = digest
    elif mutation == "numerical_composition":
        rows[0]["numerical_product"]["composition"] = {
            "Alnus": 0.2,
            "Betula": 0.8,
        }
    elif mutation == "numerical_product":
        rows[0]["numerical_product"]["scientific_content_sha256"] = "f" * 64
    elif mutation == "source_path":
        rows[0]["observed_local_pollen_source"]["path"] = "other.json"
    elif mutation == "outcome":
        rows[0]["target_vegetation"] = {"Alnus": 0.6, "Betula": 0.4}
    elif mutation == "operation_outcome":
        operations[0]["observed_vegetation"] = {"Alnus": 0.6, "Betula": 0.4}

    for row in rows:
        row["prediction_manifest_sha256"] = manifest_sha256(row)
    identity = [
        {"item_id": item["item_id"], "request_sha256": item["request_sha256"]}
        for item in attempts
    ]
    batch_sha256 = manifest_sha256(identity)
    operation_statuses = ("completed", "refused", "failed", "not_run", "unobserved")
    operation_payload: dict[str, object] = (
        {
            "schema_version": "lra-batch-result.v1",
            "batch_sha256": batch_sha256,
            "batch_status": "finished",
            "interruption_reason": None,
            "all_items_completed": True,
            "scientific_acceptance": "not_evaluated",
            "counts": {
                status: sum(item["item_status"] == status for item in operations)
                for status in operation_statuses
            },
            "items": operations,
        }
        if attempts
        else {}
    )
    scientific: dict[str, object] = {
        "profile": LOCAL_PROFILE,
        "method": LOCAL_METHOD,
        "method_kind": "local_pollen_assimilation",
        "evaluation_roles": LOCAL_EVALUATION_ROLES,
        "pollen_eligible_for_heldout_acceptance": False,
        "folds": [fold.as_dict() for fold in folds],
        "predictions": rows,
        "failures": failures,
        "requested_folds": len(folds),
        "requested_predictions": len(folds),
        "generated_predictions": len(rows),
        "failed_folds": len(failures),
        "interrupted": any(row["status"] == "not_run" for row in failures),
        "all_predictions_generated": not failures,
        "implementation": {"synthetic.py": "a" * 64},
        "engine_identity": {"synthetic": {"version": "test"}},
        "uncertainty_status": "point_predictions_only_intervals_not_implemented",
    }
    if mutation == "count":
        scientific["generated_predictions"] = len(rows) - 1
    stage = stage_directory(root / "product")
    for name, value in (
        ("experiment.json", _metadata(spec)),
        ("folds.json", scientific["folds"]),
        ("predictions.json", rows),
        ("failures.json", failures),
        ("operations.json", operation_payload),
    ):
        write_json(stage, name, value)
    if attempts:
        receipt = {
            "schema_version": "lra-batch-attempt.v1",
            "event": "attempt_started",
            "completion_receipt": "summary/receipt.json",
            "batch_sha256": batch_sha256,
            "limits": {"max_workers": 1, "max_items": len(attempts)},
            "numerical_threads_per_worker": 1,
            "input_root": "/retained/inputs",
            "cache_root": "/retained/cache",
            "items": attempts,
            "resume_authority": "verified_cache_products_only_not_attempt_receipts",
        }
        batch = stage / "batch"
        batch.mkdir()
        (batch / "receipt.json").write_text(canonical_json(receipt) + "\n")
        summary = batch / "summary"
        summary.mkdir()
        (summary / "receipt.json").write_text(canonical_json(operation_payload) + "\n")
    return publish_phase(
        stage,
        root / "product",
        phase="predictions",
        scientific=scientific,
        profile=LOCAL_PROFILE,
    )


def test_strict_local_reader_binds_requests_numerical_products_and_denominator(
    tmp_path: Path,
) -> None:
    product = _fixture(tmp_path)
    reopened, manifest, folds, rows = local_product.read_local_pollen_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    assert reopened == product
    assert manifest["profile"] == LOCAL_PROFILE
    assert len(folds) == len(rows) == 4


@pytest.mark.parametrize(
    "mutation",
    [
        "request_count",
        "numerical_composition",
        "numerical_product",
        "source_path",
        "outcome",
        "operation_outcome",
        "count",
    ],
)
def test_rehashed_request_source_numerical_and_count_contradictions_refuse(
    tmp_path: Path, mutation: str
) -> None:
    product = _fixture(tmp_path, mutation=mutation)
    with pytest.raises(ValidationRefusal):
        local_product.read_local_pollen_predictions(
            product.directory, expected_manifest_sha256=product.manifest_sha256
        )


def test_partial_refusal_and_final_interruption_suffix_reopens(tmp_path: Path) -> None:
    product = _fixture(
        tmp_path,
        terminal=("predicted", "refused", "not_run", "not_run"),
    )
    _, _, folds, rows = local_product.read_local_pollen_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    assert len(folds) == 4
    assert len(rows) == 1


@pytest.mark.parametrize(
    "terminal",
    [
        ("predicted", "not_run", "predicted", "not_run"),
        ("predicted", "failed", "refused", "refused"),
    ],
)
def test_non_suffix_interruption_and_unsupported_failure_status_refuse(
    tmp_path: Path, terminal: tuple[str, ...]
) -> None:
    product = _fixture(tmp_path, terminal=terminal)
    with pytest.raises(ValidationRefusal):
        local_product.read_local_pollen_predictions(
            product.directory, expected_manifest_sha256=product.manifest_sha256
        )
