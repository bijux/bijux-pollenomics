"""Bind existing authenticated single-site REVEALS products into one cohort."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..batches.models import LRABatchItem, LRABatchResult, canonical_json
from ..engine.errors import LRARefusal
from ..inputs.validation import validate_request
from ..outputs.reading import read_lra_product
from .contracts import (
    RegionalComponentPlan,
    RegionalComponentRecord,
    RegionalComponentSet,
)
from .publication import publish_regional_component_set


def _refuse(reason: str, detail: str) -> None:
    raise LRARefusal(reason, detail)


def _regular_input(root: Path, relative: str, expected_sha256: str) -> None:
    root = root.absolute()
    if root.is_symlink() or not root.is_dir():
        _refuse("invalid_component_grouping_evidence", "Input root must be a directory")
    path = root / relative
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            _refuse(
                "invalid_component_grouping_evidence",
                "Grouping evidence cannot traverse a symbolic link",
            )
    try:
        if not path.is_file():
            raise OSError("not a regular file")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise LRARefusal("component_grouping_evidence_unavailable", str(exc)) from exc
    if digest != expected_sha256:
        _refuse(
            "component_grouping_evidence_mismatch",
            "Grouping evidence differs from the planned digest",
        )


def _symlink_ancestor(path: Path) -> bool:
    current = path.absolute()
    while True:
        if current.exists() and current.is_symlink():
            return True
        if current == current.parent:
            return False
        current = current.parent


def _overlaps(left: Path, right: Path) -> bool:
    left, right = left.absolute(), right.absolute()
    return left == right or left.is_relative_to(right) or right.is_relative_to(left)


def _producer_identity(manifest: dict[str, Any]) -> str:
    identity = manifest["scientific_identity"]
    payload = {
        "engine": manifest["engine"],
        **{
            name: identity[name]
            for name in (
                "engine_files",
                "host_adapter_files",
                "host_publication_files",
                "runtime_environment",
            )
        },
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _dependency_lock(payload: dict[str, Any]) -> str:
    locks = [
        row["sha256"] for row in payload["evidence"] if row["role"] == "dependency_lock"
    ]
    if len(locks) != 1:
        _refuse(
            "regional_component_cohort_mismatch",
            "Each component must bind exactly one dependency lock",
        )
    return str(locks[0])


def _cohort_identity(payload: dict[str, Any]) -> dict[str, object]:
    versions = payload["versions"]
    return {
        "data_kind": payload["data_kind"],
        "method_profile": payload["method_profile"],
        "pollen_unit": payload["pollen_unit"],
        "taxa": payload["taxa"],
        "parameters": payload["parameters"],
        "versions": {
            name: versions[name]
            for name in ("taxonomy", "parameters", "chronology", "binning")
        },
        "dependency_lock_sha256": _dependency_lock(payload),
    }


def _component_payload(
    item: LRABatchItem, plan: RegionalComponentPlan, input_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = item.payload()
    validated = validate_request(payload, input_root=input_root)
    if validated.sha256 != item.request_sha256:
        _refuse("regional_component_request_mismatch", item.item_id)
    if payload["operation"] != "reveals":
        _refuse(
            "unsupported_regional_component_operation",
            "Regional component sets accept single-site REVEALS requests only",
        )
    samples = payload["regional"]["samples"]
    bins = payload["temporal_matching"]["bins"]
    if len(samples) != 1 or len(bins) != 1:
        _refuse(
            "unsupported_regional_component_shape",
            "Each component must contain exactly one sample in one time bin",
        )
    sample, time_bin = samples[0], bins[0]
    if (
        sample["bin_id"] != plan.bin_id
        or time_bin["bin_id"] != plan.bin_id
        or [float(time_bin["younger_bp"]), float(time_bin["older_bp"])]
        != list(plan.bin_bounds_bp)
    ):
        _refuse(
            "regional_component_bin_mismatch",
            "Every component must use the plan's exact bin identity and BP bounds",
        )
    return payload, sample


def _summary_bytes(batch: LRABatchResult) -> bytes:
    path = batch.report_root.absolute() / "summary" / "receipt.json"
    try:
        if path.is_symlink() or not path.is_file():
            raise OSError("summary receipt is not a regular file")
        encoded: bytes = path.read_bytes()
    except OSError as exc:
        raise LRARefusal("regional_component_batch_unavailable", str(exc)) from exc
    expected = (canonical_json(batch.as_dict()) + "\n").encode()
    if encoded != expected:
        _refuse(
            "regional_component_batch_mismatch",
            "Batch summary bytes differ from the supplied terminal result",
        )
    return encoded


def bind_regional_component_set(
    items: tuple[LRABatchItem, ...],
    batch: LRABatchResult,
    plan: RegionalComponentPlan,
    *,
    input_root: Path,
    destination: Path,
) -> RegionalComponentSet:
    """Authenticate and publish heterogeneous component outcomes without pooling."""
    if tuple(item.item_id for item in items) != plan.ordered_item_ids:
        _refuse(
            "regional_component_item_order_mismatch",
            "Plan order must exactly match the original batch item order",
        )
    expected_batch = hashlib.sha256(
        canonical_json(
            [
                {"item_id": item.item_id, "request_sha256": item.request_sha256}
                for item in items
            ]
        ).encode()
    ).hexdigest()
    if batch.batch_sha256 != expected_batch or len(batch.items) != len(items):
        _refuse(
            "regional_component_batch_mismatch",
            "Batch identity or denominator differs from the declared items",
        )
    summary = _summary_bytes(batch)
    if hashlib.sha256(summary).hexdigest() != plan.batch_summary_sha256:
        _refuse(
            "regional_component_batch_mismatch",
            "Batch summary differs from the plan's external digest",
        )
    _regular_input(
        input_root,
        plan.grouping_evidence_path,
        plan.grouping_evidence_sha256,
    )
    initial_roots = [
        input_root.absolute(),
        batch.report_root.absolute(),
        destination.absolute(),
    ]
    if any(_symlink_ancestor(path) for path in initial_roots):
        _refuse(
            "unsafe_regional_component_path",
            "Input, report and destination trees cannot traverse symlinks",
        )
    for position, left in enumerate(initial_roots):
        if any(_overlaps(left, right) for right in initial_roots[position + 1 :]):
            _refuse(
                "overlapping_regional_component_paths",
                "Input, report and destination trees must be disjoint",
            )

    cohort: dict[str, object] | None = None
    site_ids: set[str] = set()
    sample_ids: set[str] = set()
    records: list[RegionalComponentRecord] = []
    component_sources: dict[int, Path] = {}
    request_bytes = {
        index: (item.canonical_request + "\n").encode()
        for index, item in enumerate(items)
    }
    producer_identity: str | None = None
    for index, (item, outcome) in enumerate(zip(items, batch.items, strict=True)):
        if (
            outcome.index != index
            or outcome.item_id != item.item_id
            or outcome.request_sha256 != item.request_sha256
        ):
            _refuse(
                "regional_component_batch_mismatch",
                "Batch item order or identity differs from the requested cohort",
            )
        payload, sample = _component_payload(item, plan, input_root)
        identity = _cohort_identity(payload)
        if cohort is None:
            cohort = identity
        elif identity != cohort:
            _refuse(
                "regional_component_cohort_mismatch",
                "Taxa, parameters, versions, units, profile and lock must agree",
            )
        if sample["site_id"] in site_ids or sample["sample_id"] in sample_ids:
            _refuse(
                "duplicate_regional_component_identity",
                "Site and sample identities must be unique within a component set",
            )
        site_ids.add(sample["site_id"])
        sample_ids.add(sample["sample_id"])
        product_path = None
        product_manifest = None
        product_scientific = None
        product_producer = None
        if outcome.item_status == "completed":
            if outcome.product is None:
                _refuse(
                    "regional_component_batch_mismatch",
                    "A completed component must retain its product identity",
                )
            verified = read_lra_product(
                outcome.product.directory,
                expected_manifest_sha256=outcome.product.manifest_sha256,
            )
            manifest = verified.manifest()
            if manifest["request_sha256"] != item.request_sha256:
                _refuse(
                    "regional_component_product_mismatch",
                    "Product request identity differs from its component",
                )
            if (
                verified.product.scientific_content_sha256
                != outcome.product.scientific_content_sha256
            ):
                _refuse(
                    "regional_component_product_mismatch",
                    "Batch product scientific identity differs from reopened bytes",
                )
            product_producer = _producer_identity(manifest)
            if producer_identity is None:
                producer_identity = product_producer
            elif product_producer != producer_identity:
                _refuse(
                    "regional_component_producer_mismatch",
                    "Completed components must share one exact "
                    "backend/runtime/code identity",
                )
            product_path = f"components/{index:06d}"
            product_manifest = verified.product.manifest_sha256
            product_scientific = verified.product.scientific_content_sha256
            component_sources[index] = verified.product.directory
        elif outcome.product is not None:
            _refuse(
                "regional_component_batch_mismatch",
                "Only completed components may reference a numerical product",
            )
        basin = payload["regional"]["basin"]
        records.append(
            RegionalComponentRecord(
                index=index,
                item_id=item.item_id,
                request_sha256=item.request_sha256,
                site_id=sample["site_id"],
                sample_id=sample["sample_id"],
                bin_id=sample["bin_id"],
                basin_type=basin["site_type"],
                basin_diameter_m=float(basin["diameter_m"]),
                geometry_evidence_id=basin["geometry_evidence_id"],
                item_status=outcome.item_status,
                product_path=product_path,
                product_manifest_sha256=product_manifest,
                product_scientific_content_sha256=product_scientific,
                product_producer_identity_json=product_producer,
                canonical_error=outcome.canonical_error,
            )
        )
    roots = [
        input_root.absolute(),
        batch.report_root.absolute(),
        destination.absolute(),
    ]
    roots.extend(path.absolute() for path in component_sources.values())
    if any(_symlink_ancestor(path) for path in roots):
        _refuse(
            "unsafe_regional_component_path",
            "Input, report, product and destination trees cannot traverse symlinks",
        )
    for position, left in enumerate(roots):
        if any(_overlaps(left, right) for right in roots[position + 1 :]):
            _refuse(
                "overlapping_regional_component_paths",
                "Input, report, product and destination trees must be disjoint",
            )
    # Recheck the entire source closure immediately before the atomic copy.
    if _summary_bytes(batch) != summary:
        _refuse("regional_component_source_changed", "Batch summary changed")
    _regular_input(
        input_root, plan.grouping_evidence_path, plan.grouping_evidence_sha256
    )
    for item, outcome in zip(items, batch.items, strict=True):
        _component_payload(item, plan, input_root)
        if outcome.item_status == "completed" and outcome.product is not None:
            read_lra_product(
                outcome.product.directory,
                expected_manifest_sha256=outcome.product.manifest_sha256,
            )
    return publish_regional_component_set(
        plan,
        tuple(records),
        batch_sha256=batch.batch_sha256,
        batch_summary_bytes=summary,
        grouping_evidence_source=input_root.absolute() / plan.grouping_evidence_path,
        component_sources=component_sources,
        request_bytes=request_bytes,
        destination=destination,
    )
