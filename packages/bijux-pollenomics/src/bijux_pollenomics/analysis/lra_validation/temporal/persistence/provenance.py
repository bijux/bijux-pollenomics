"""Bind retained older requests and item receipts without reopening original sources."""

from __future__ import annotations

from ....lra.batches.models import LRABatchItem
from ....lra.engine.errors import LRARefusal
from ...contracts import ValidationRefusal, canonical_json, manifest_sha256
from ...experiments.configuration import identity, object_list, object_mapping
from ...experiments.outputs import ExperimentProduct, read_member
from ...experiments.reading.provenance import _validate_request
from .admission import TemporalSourceAdmission
from .configuration import TemporalPersistenceSpec

PREFIX = "batches/older/"
STATUSES = ("completed", "refused", "failed", "not_run", "unobserved")


def _same(actual: object, expected: object, label: str) -> None:
    if canonical_json(actual) != canonical_json(expected):
        raise ValidationRefusal("temporal_request_provenance_mismatch", label)


def _geometry(
    request: dict[str, object],
    source: TemporalSourceAdmission,
    record: str,
    anchor: str,
) -> None:
    geometries = source.geometries()
    for role, owner in (("local", record), ("regional", anchor)):
        geometry = object_mapping(geometries[owner], "geometry")
        section = object_mapping(request[role], role)
        sample = object_mapping(object_list(section["samples"], "samples")[0], "sample")
        _same(
            {
                key: value
                for key, value in sample.items()
                if key not in {"counts", "raw_evidence_id"}
            },
            geometry["sample_metadata"],
            "original sample geometry/chronology",
        )
        _same(
            section["basin"],
            dict(
                object_mapping(geometry["basin"], "basin"),
                geometry_evidence_id="geometry:" + owner,
            ),
            "original basin",
        )
        if role == "local":
            _same(
                request["rings"],
                [
                    dict(
                        object_mapping(value, "ring"),
                        geometry_evidence_id="geometry:" + owner,
                    )
                    for value in object_list(geometry["inversion_rings"], "rings")
                ],
                "original inversion rings",
            )


def validate_temporal_requests(
    product: ExperimentProduct,
    manifest: dict[str, object],
    spec: TemporalPersistenceSpec,
    source: TemporalSourceAdmission | None,
    scientific: dict[str, object],
) -> None:
    """Verify internal retained closure, not numerical regeneration or authorship."""
    try:
        _validate(product, manifest, spec, source, scientific)
    except (LRARefusal, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ValidationRefusal):
            raise
        raise ValidationRefusal(
            "invalid_temporal_request_provenance", str(exc)
        ) from exc


def _validate(
    product: ExperimentProduct,
    manifest: dict[str, object],
    spec: TemporalPersistenceSpec,
    source: TemporalSourceAdmission | None,
    scientific: dict[str, object],
) -> None:
    files = object_mapping(manifest["files"], "files")
    state = scientific["older_training_state"]
    operations = object_list(read_member(product, "operations.json"), "operations")
    name = PREFIX + "receipt.json"
    if name not in files:
        if (
            state is not None
            or operations
            or any(key.startswith(PREFIX) for key in files)
        ):
            raise ValidationRefusal("missing_temporal_batch_request", name)
        # Request construction may fail, or receive SIGINT, before begin_attempt.
        return
    if source is None:
        raise ValidationRefusal("missing_temporal_source_admission", name)
    admitted = source.decision.require_training_admission().admitted_record_ids
    anchor = spec.temporal_plan.required_regional_record_ids[0]
    expected = [record for record in admitted if record != anchor]
    batch = object_mapping(read_member(product, name), "batch")
    _same(batch["schema_version"], "lra-batch-attempt.v1", "attempt schema")
    _same(batch["event"], "attempt_started", "attempt event")
    _same(batch["completion_receipt"], "summary/receipt.json", "completion path")
    items = [
        object_mapping(value, "item") for value in object_list(batch["items"], "items")
    ]
    _same(
        [row["item_id"] for row in items],
        expected,
        "exact original admitted request order",
    )
    catalogue: dict[str, dict[str, object]] = {
        site.record.record_id: {
            "site_id": site.record.site_id,
            "raw_path": site.raw.path,
            "raw_sha256": site.raw.sha256,
            "geometry_path": site.geometry.path,
            "geometry_sha256": site.geometry.sha256,
        }
        for site in spec.older_experiment.sites
    }
    identities: list[dict[str, object]] = []
    for item in items:
        _same(sorted(item), ["item_id", "request", "request_sha256"], "request fields")
        record = identity(item["item_id"])
        request = object_mapping(item["request"], "request")
        digest = LRABatchItem(record, request).request_sha256
        _same(item["request_sha256"], digest, "request body digest")
        _validate_request(
            {"local_ring_count": spec.older_experiment.local_ring_count},
            spec.older_experiment.template(),
            catalogue,
            record,
            anchor,
            request,
        )
        _geometry(request, source, record, anchor)
        identities.append({"item_id": record, "request_sha256": digest})
    _same(batch["batch_sha256"], manifest_sha256(identities), "ordered batch identity")
    for field in ("consumed_pollen_record_ids", "consumed_geometry_record_ids"):
        if not set(admitted).issubset(object_list(scientific[field], field)):
            raise ValidationRefusal("temporal_consumed_source_mismatch", field)
    receipts: list[dict[str, object]] = []
    allowed_members = {name, PREFIX + "summary/receipt.json"}
    for index, item in enumerate(items):
        path = PREFIX + f"items/{index:06d}/receipt.json"
        allowed_members.add(path)
        if path not in files:
            continue
        receipt = object_mapping(read_member(product, path), "item receipt")
        for field, expected_value in {
            "schema_version": "lra-batch-item.v1",
            "index": index,
            "item_id": item["item_id"],
            "request_sha256": item["request_sha256"],
            "scientific_acceptance": "not_evaluated",
        }.items():
            _same(receipt[field], expected_value, "item " + field)
        status = receipt["item_status"]
        if status not in STATUSES or (status == "completed") != ("product" in receipt):
            raise ValidationRefusal("invalid_temporal_batch_item", path)
        receipts.append(receipt)
    if any(key.startswith(PREFIX) and key not in allowed_members for key in files):
        raise ValidationRefusal("unexpected_temporal_batch_member", PREFIX)
    summary_name = PREFIX + "summary/receipt.json"
    if summary_name not in files:
        if state is not None or operations:
            raise ValidationRefusal("missing_temporal_batch_summary", summary_name)
        return  # A preserved early interrupt has no fabricated completion receipt.
    summary = object_mapping(read_member(product, summary_name), "summary")
    _same(len(receipts), len(items), "complete summary item denominator")
    _same(summary["items"], receipts, "summary/item receipts")
    for field, value in {
        "schema_version": "lra-batch-result.v1",
        "batch_sha256": batch["batch_sha256"],
        "scientific_acceptance": "not_evaluated",
        "counts": {
            status: sum(row["item_status"] == status for row in receipts)
            for status in STATUSES
        },
        "all_items_completed": all(
            row["item_status"] == "completed" for row in receipts
        ),
    }.items():
        _same(summary[field], value, "summary " + field)
    if summary["batch_status"] not in {"finished", "interrupted"}:
        raise ValidationRefusal("invalid_temporal_batch_summary", "batch status")
    if summary["batch_status"] == "interrupted":
        identity(summary["interruption_reason"])
        _same(
            scientific["interrupted"],
            True,
            "interrupted batch requires interrupted experiment",
        )
    else:
        _same(
            summary["interruption_reason"], None, "finished batch interruption reason"
        )
    # A later post-batch SIGINT can interrupt an experiment after a finished batch.
    if operations:
        _same(
            operations,
            [{"fold_id": spec.temporal_plan.fold.fold_id, "batch": summary}],
            "operational batch",
        )
    if state is None:
        return
    _same(
        summary["all_items_completed"], True, "fitted state requires complete requests"
    )
    _same(summary["batch_status"], "finished", "fitted state requires finished batch")
    _same(len(operations), 1, "fitted state operational receipt")
    products = [
        object_mapping(value, "training product")
        for value in object_list(
            object_mapping(state, "state")["training_products"], "training_products"
        )
    ]
    _same(
        [row["record_id"] for row in products], expected, "fitted product denominator"
    )
    for fitted, item, receipt in zip(products, items, receipts, strict=True):
        _same(
            fitted["request_sha256"], item["request_sha256"], "fitted original request"
        )
        _same(
            fitted["scientific_content_sha256"],
            object_mapping(receipt["product"], "product")["scientific_content_sha256"],
            "fitted numerical product",
        )
