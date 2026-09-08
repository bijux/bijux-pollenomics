"""End-to-end classification-audit materialization workflow."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .accounting import validate_accounting_reconciliation, validated_accounting_rows
from .constants import ACCEPTED_STATUSES, MANIFEST_NAME
from .manifest import build_manifest, canonical_json_bytes, sha256
from .models import (
    ClassificationAuditMaterializationResult,
    ClassificationAuditOutputPaths,
)
from .payloads import build_payloads
from .publication import publish_atomically, validate_output_paths
from .values import required_digest, required_text


def materialize_classification_audit(
    accounting: Mapping[str, object],
    *,
    paths: ClassificationAuditOutputPaths,
    allowed_output_parent: Path,
    classification_contract_version: str,
    classification_contract_digest: str,
    classification_producer_id: str,
    classification_producer_version: str,
    classification_producer_digest: str,
) -> ClassificationAuditMaterializationResult:
    """Reconcile and atomically publish a deterministic classification audit."""
    validate_output_paths(paths, Path(allowed_output_parent))
    classification_contract_version = required_text(
        classification_contract_version,
        field_name="classification_contract_version",
    )
    classification_contract_digest = required_digest(
        classification_contract_digest,
        field_name="classification_contract_digest",
    )
    classification_producer_id = required_text(
        classification_producer_id,
        field_name="classification_producer_id",
    )
    classification_producer_version = required_text(
        classification_producer_version,
        field_name="classification_producer_version",
    )
    classification_producer_digest = required_digest(
        classification_producer_digest,
        field_name="classification_producer_digest",
    )
    concepts, memberships = validated_accounting_rows(accounting)
    validate_accounting_reconciliation(accounting, concepts, memberships)
    payloads, release_status = build_payloads(
        accounting=accounting,
        concepts=concepts,
        memberships=memberships,
        classification_contract_version=classification_contract_version,
        classification_contract_digest=classification_contract_digest,
        classification_producer_id=classification_producer_id,
        classification_producer_version=classification_producer_version,
        classification_producer_digest=classification_producer_digest,
    )
    serialized_payloads = {
        name: canonical_json_bytes(payload) for name, payload in payloads.items()
    }
    manifest = build_manifest(
        accounting=accounting,
        serialized_payloads=serialized_payloads,
        classification_contract_version=classification_contract_version,
        classification_contract_digest=classification_contract_digest,
        classification_producer_id=classification_producer_id,
        classification_producer_version=classification_producer_version,
        classification_producer_digest=classification_producer_digest,
    )
    manifest_bytes = canonical_json_bytes(manifest)
    expected_files = {**serialized_payloads, MANIFEST_NAME: manifest_bytes}
    disposition = publish_atomically(
        output_root=paths.output_root,
        allowed_output_parent=Path(allowed_output_parent),
        expected_files=expected_files,
    )
    accepted_count = sum(
        str(row["mapping_status"]) in ACCEPTED_STATUSES for row in concepts
    )
    return ClassificationAuditMaterializationResult(
        output_root=paths.output_root,
        disposition=disposition,
        manifest_sha256=sha256(manifest_bytes),
        file_count=len(expected_files),
        concept_count=len(concepts),
        observation_count=len(memberships),
        accepted_mapping_count=accepted_count,
        release_status=release_status,
    )
