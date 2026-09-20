"""Atomic publication for authenticated, explicitly non-aggregated components."""

from __future__ import annotations

import hashlib
from importlib import metadata
import json
from pathlib import Path
import shutil
import tempfile

from ..outputs.atomic import publish_directory
from ..outputs.reading import read_lra_product
from .contracts import (
    ComponentStatus,
    ExecutionStatus,
    RegionalComponentPlan,
    RegionalComponentRecord,
    RegionalComponentSet,
)

_STATUSES: tuple[ComponentStatus, ...] = (
    "completed",
    "refused",
    "failed",
    "not_run",
    "unobserved",
)


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _inventory(root: Path) -> dict[str, str]:
    paths = list(root.rglob("*"))
    if root.is_symlink() or any(path.is_symlink() for path in paths):
        raise ValueError("Regional component bundle contains a symbolic link")
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in paths
        if path.is_file() and path != root / "manifest.json"
    }


def _symlink_ancestor(path: Path) -> bool:
    current = path.absolute()
    while True:
        if current.exists() and current.is_symlink():
            return True
        if current == current.parent:
            return False
        current = current.parent


def bundle_producer_identity() -> dict[str, object]:
    """Bind the component producer/facade bytes and installed host version."""
    package = Path(__file__).parent
    paths = [
        package / name
        for name in (
            "__init__.py",
            "contracts.py",
            "publication.py",
            "reading.py",
            "workflow.py",
        )
    ]
    paths.append(package.parent / "api.py")
    return {
        "host_version": metadata.version("bijux-pollenomics"),
        "files": {
            path.relative_to(package.parent).as_posix(): _sha256(path.read_bytes())
            for path in paths
        },
    }


def _execution_status(records: tuple[RegionalComponentRecord, ...]) -> ExecutionStatus:
    completed = sum(record.item_status == "completed" for record in records)
    if completed == len(records):
        return "complete"
    if completed == 0 and all(record.item_status == "refused" for record in records):
        return "refused"
    return "partial"


def publish_regional_component_set(
    plan: RegionalComponentPlan,
    records: tuple[RegionalComponentRecord, ...],
    *,
    batch_sha256: str,
    batch_summary_bytes: bytes,
    grouping_evidence_source: Path,
    component_sources: dict[int, Path],
    request_bytes: dict[int, bytes],
    destination: Path,
) -> RegionalComponentSet:
    """Publish exact component outcomes without calculating an aggregate."""
    status = _execution_status(records)
    producer_identity = bundle_producer_identity()
    counts: dict[str, int] = {
        item_status: sum(record.item_status == item_status for record in records)
        for item_status in _STATUSES
    }
    destination = destination.absolute()
    if _symlink_ancestor(destination):
        raise ValueError("Regional component destination has a symbolic-link ancestor")
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.pending-", dir=destination.parent)
    )
    evidence = stage / "evidence"
    evidence.mkdir()
    grouping_bytes = grouping_evidence_source.read_bytes()
    if _sha256(grouping_bytes) != plan.grouping_evidence_sha256:
        raise ValueError("Grouping evidence changed before publication")
    if _sha256(batch_summary_bytes) != plan.batch_summary_sha256:
        raise ValueError("Batch summary changed before publication")
    (evidence / "grouping.bin").write_bytes(grouping_bytes)
    (evidence / "batch-summary.json").write_bytes(batch_summary_bytes)
    requests = stage / "requests"
    requests.mkdir()
    for index, encoded_request in sorted(request_bytes.items()):
        (requests / f"{index:06d}.json").write_bytes(encoded_request)
    for record in records:
        if record.item_status != "completed":
            continue
        source = component_sources.get(record.index)
        if source is None or record.product_path is None:
            raise ValueError("Completed component source is unavailable")
        copied = stage / record.product_path
        shutil.copytree(source, copied)
        reopened = read_lra_product(
            copied, expected_manifest_sha256=record.product_manifest_sha256
        )
        if (
            reopened.product.scientific_content_sha256
            != record.product_scientific_content_sha256
        ):
            raise ValueError("Copied component scientific identity changed")

    plan_bytes = _canonical(plan.as_dict())
    component_bytes = b"".join(_canonical(record.as_dict()) for record in records)
    (stage / "plan.json").write_bytes(plan_bytes)
    (stage / "components.jsonl").write_bytes(component_bytes)
    scientific_identity = {
        "plan": plan.as_dict(),
        "batch_sha256": batch_sha256,
        "components": [record.scientific_identity() for record in records],
        "component_execution_status": status,
        "counts": counts,
        "aggregation_performed": False,
        "aggregation_profile": None,
        "regional_estimate": None,
        "regional_uncertainty": None,
        "publication_profile": None,
        "scientific_acceptance": "not_evaluated",
        "bundle_producer_identity": producer_identity,
    }
    scientific_digest = _sha256(_canonical(scientific_identity))
    manifest = {
        "schema_version": "regional-component-set.v1",
        "product_kind": "regional_site_component_set",
        "component_execution_status": status,
        "counts": counts,
        "requested_component_count": len(records),
        "aggregation_performed": False,
        "aggregation_profile": None,
        "regional_estimate": None,
        "regional_uncertainty": None,
        "publication_profile": None,
        "scientific_acceptance": "not_evaluated",
        "scientific_content_sha256": scientific_digest,
        "bundle_producer_identity": scientific_identity["bundle_producer_identity"],
        "scientific_identity": scientific_identity,
        "files": _inventory(stage),
    }
    if bundle_producer_identity() != producer_identity:
        raise ValueError("Regional component producer changed during publication")
    encoded = _canonical(manifest)
    (stage / "manifest.json").write_bytes(encoded)
    publish_directory(stage, destination)
    return RegionalComponentSet(
        destination,
        _sha256(encoded),
        scientific_digest,
        status,
        counts,
    )
