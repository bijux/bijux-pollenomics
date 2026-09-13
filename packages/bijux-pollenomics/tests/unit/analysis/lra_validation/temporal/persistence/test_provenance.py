"""Retained request and item contradictions cannot survive an outer byte rehash."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.batches.models import LRABatchItem
from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import make_request
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
)
from bijux_pollenomics.analysis.lra_validation.temporal.persistence import provenance
from bijux_pollenomics.analysis.lra_validation.temporal.persistence.admission import (
    admit_temporal_sources,
)

from .support import fixture_payload, spec_from_payload


def retained(root: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, ...]:
    spec = spec_from_payload(fixture_payload(root))
    source = admit_temporal_sources(spec, input_root=root)
    admitted = source.decision.require_training_admission().admitted_record_ids
    by_id = {site.record.record_id: site for site in spec.older_experiment.sites}
    anchor = by_id[spec.temporal_plan.required_regional_record_ids[0]]
    items: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    products: list[dict[str, Any]] = []
    for record in admitted:
        if record == anchor.record.record_id:
            continue
        item = LRABatchItem(
            record,
            make_request(
                spec.older_experiment,
                by_id[record],
                anchor,
                spec.temporal_plan.fold,
                root,
            ),
        )
        items.append(
            {
                "item_id": record,
                "request": item.payload(),
                "request_sha256": item.request_sha256,
            }
        )
        receipts.append(
            {
                "schema_version": "lra-batch-item.v1",
                "index": len(receipts),
                "item_id": record,
                "request_sha256": item.request_sha256,
                "item_status": "completed",
                "product": {"scientific_content_sha256": "a" * 64},
                "scientific_acceptance": "not_evaluated",
            }
        )
        products.append(
            {
                "record_id": record,
                "request_sha256": item.request_sha256,
                "scientific_content_sha256": "a" * 64,
            }
        )
    batch: dict[str, Any] = {
        "schema_version": "lra-batch-attempt.v1",
        "event": "attempt_started",
        "completion_receipt": "summary/receipt.json",
        "items": items,
        "batch_sha256": manifest_sha256(
            [{key: row[key] for key in ("item_id", "request_sha256")} for row in items]
        ),
    }
    summary: dict[str, Any] = {
        "schema_version": "lra-batch-result.v1",
        "items": receipts,
        "batch_sha256": batch["batch_sha256"],
        "batch_status": "finished",
        "interruption_reason": None,
        "all_items_completed": True,
        "scientific_acceptance": "not_evaluated",
        "counts": {
            status: len(items) if status == "completed" else 0
            for status in provenance.STATUSES
        },
    }
    members: dict[str, Any] = {
        "batches/older/receipt.json": batch,
        "batches/older/summary/receipt.json": summary,
        "operations.json": [
            {"fold_id": spec.temporal_plan.fold.fold_id, "batch": summary}
        ],
    }
    members.update(
        {
            f"batches/older/items/{index:06d}/receipt.json": row
            for index, row in enumerate(receipts)
        }
    )
    science = {
        "interrupted": False,
        "older_training_state": {"training_products": products},
        "consumed_pollen_record_ids": list(admitted),
        "consumed_geometry_record_ids": list(admitted),
    }
    monkeypatch.setattr(provenance, "read_member", lambda product, name: members[name])
    product = ExperimentProduct(root, "a" * 64, "b" * 64)
    return product, spec, source, science, members


def verify(values: tuple[Any, ...]) -> None:
    product, spec, source, science, members = values
    provenance.validate_temporal_requests(
        product, {"files": dict.fromkeys(members, "a" * 64)}, spec, source, science
    )


def test_complete_original_request_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    verify(retained(tmp_path, monkeypatch))


@pytest.mark.parametrize(
    "mutation",
    [
        "raw_sha",
        "ppe",
        "count",
        "missing_request",
        "item_sha",
        "rehash_ppe",
        "rehash_geometry",
        "rehash_count",
        "missing_item",
        "missing_attempt",
        "missing_summary",
        "summary_count",
        "extra_receipt",
        "state_content",
        "consumed",
    ],
)
def test_request_contradictions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    values = retained(tmp_path, monkeypatch)
    _, _, _, science, members = values
    batch = members["batches/older/receipt.json"]
    item = batch["items"][0]
    request = item["request"]
    if mutation == "raw_sha":
        next(row for row in request["evidence"] if row["role"] == "raw_snapshot")[
            "sha256"
        ] = "0" * 64
    elif mutation in {"ppe", "rehash_ppe"}:
        request["parameters"][0]["ppe"] += 1
    elif mutation in {"count", "rehash_count"}:
        request["local"]["samples"][0]["counts"][0] += 1
    elif mutation == "rehash_geometry":
        request["local"]["basin"]["diameter_m"] += 1
    elif mutation == "missing_request":
        batch["items"].pop()
    elif mutation == "item_sha":
        members["batches/older/items/000000/receipt.json"]["request_sha256"] = "0" * 64
    elif mutation in {"missing_item", "missing_attempt", "missing_summary"}:
        key = {
            "missing_item": "items/000000/receipt.json",
            "missing_attempt": "receipt.json",
            "missing_summary": "summary/receipt.json",
        }[mutation]
        del members["batches/older/" + key]
    elif mutation == "summary_count":
        members["batches/older/summary/receipt.json"]["counts"]["completed"] = 0
    elif mutation == "extra_receipt":
        members["batches/older/items/000999/receipt.json"] = {}
    elif mutation == "state_content":
        science["older_training_state"]["training_products"][0][
            "scientific_content_sha256"
        ] = "b" * 64
    elif mutation == "consumed":
        science["consumed_pollen_record_ids"].pop()
    if mutation.startswith("rehash_"):
        item["request_sha256"] = LRABatchItem(item["item_id"], request).request_sha256
        batch["batch_sha256"] = manifest_sha256(
            [
                {key: row[key] for key in ("item_id", "request_sha256")}
                for row in batch["items"]
            ]
        )
    with pytest.raises(ValidationRefusal):
        verify(values)


@pytest.mark.parametrize(
    "stage", ["before_attempt", "attempt_only", "partial_items", "complete_failure"]
)
def test_failed_or_interrupted_attempt_retains_available_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    values = retained(tmp_path, monkeypatch)
    _, _, _, science, members = values
    science["older_training_state"] = None
    members["operations.json"] = []
    if stage != "complete_failure":
        del members["batches/older/summary/receipt.json"]
        for key in list(members):
            if key.startswith("batches/older/items/") and (
                stage != "partial_items" or "000000" not in key
            ):
                del members[key]
    if stage == "before_attempt":
        del members["batches/older/receipt.json"]
    verify(values)


@pytest.mark.parametrize(
    "status,reason,experiment_interrupted,accepted",
    [
        ("interrupted", "keyboard_interrupt", False, False),
        ("interrupted", None, True, False),
        ("interrupted", "", True, False),
        ("finished", "keyboard_interrupt", True, False),
        ("interrupted", "keyboard_interrupt", True, True),
        ("finished", None, True, True),
    ],
)
def test_batch_interruption_is_one_way(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    reason: object,
    experiment_interrupted: bool,
    accepted: bool,
) -> None:
    values = retained(tmp_path, monkeypatch)
    _, _, _, science, members = values
    science["older_training_state"] = None
    science["interrupted"] = experiment_interrupted
    members["operations.json"] = []
    summary = members["batches/older/summary/receipt.json"]
    summary["batch_status"], summary["interruption_reason"] = status, reason
    if accepted:
        verify(values)
    else:
        with pytest.raises(ValidationRefusal):
            verify(values)
