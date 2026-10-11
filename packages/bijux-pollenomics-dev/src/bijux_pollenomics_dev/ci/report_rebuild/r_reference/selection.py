"""Select only two separately authenticated R source families."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.lra_validation.native_reference.capture import (
    CAPTURE_MANIFEST_SHA256,
    CAPTURE_SOURCE_REVISION,
)
from bijux_pollenomics_dev.lra_validation.reference_replay import CERTIFICATE_SHA256

from ..contracts import JsonObject, ReportRebuildError
from ..evidence import inventory_json
from ..original_r_reference import validated_original_r_reference
from .native import validated_native_r_reference


@dataclass(frozen=True)
class RReferences:
    """Exact protected source inventory and its assembly-visible admission identity."""

    inventory: tuple[InventoryEntry, ...]
    evidence: JsonObject
    retained_evidence: JsonObject


def validated_r_references(
    repository: Path,
    policy: JsonObject,
    *,
    original: bool,
    native: bool,
) -> RReferences:
    """Dispatch fixed validators; arbitrary retained ownership labels confer nothing."""
    entries: list[InventoryEntry] = []
    evidence: JsonObject = {}
    retained_evidence: JsonObject = {}
    if original:
        accepted = validated_original_r_reference(repository, policy)
        entries.extend(accepted)
        evidence["original_r_reference"] = {
            "certificate_sha256": CERTIFICATE_SHA256,
            "inventory": inventory_json(accepted),
        }
        retained_evidence["original_r_reference"] = {
            "certificate_sha256": CERTIFICATE_SHA256,
            "paths": [entry.path for entry in accepted],
        }
    if native:
        accepted = validated_native_r_reference(repository, policy)
        entries.extend(accepted)
        evidence["native_r_reference"] = {
            "capture_manifest_sha256": CAPTURE_MANIFEST_SHA256,
            "native_source_revision": CAPTURE_SOURCE_REVISION,
            "inventory": inventory_json(accepted),
        }
        retained_evidence["native_r_reference"] = {
            "capture_manifest_sha256": CAPTURE_MANIFEST_SHA256,
            "native_source_revision": CAPTURE_SOURCE_REVISION,
            "paths": [entry.path for entry in accepted],
        }
    paths = [entry.path for entry in entries]
    if len(paths) != len(set(paths)):
        raise ReportRebuildError("independently admitted R source families overlap")
    return RReferences(
        tuple(sorted(entries, key=lambda entry: entry.path)),
        evidence,
        retained_evidence,
    )
