"""Governed SEAD document admission for atlas projection."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from pathlib import Path
from typing import cast

from bijux_pollenomics.evidence.sources.sead import (
    governed_sead_evidence_root,
    read_validated_sead_evidence_documents,
)

from ..constants import _SEAD_EVIDENCE_DOCUMENTS
from ..io import _read_json_object, _read_regular_bytes, _required_text
from ..sead_claims import _validate_sead_claim_parents
from .models import EvidenceBundle


def load_evidence_bundle(
    context_root: Path,
    *,
    expected_run_id: str,
    expected_manifest_sha256: str,
    expected_admission_sha256: str,
) -> EvidenceBundle:
    """Load and reconcile the governed evidence and acquisition manifests."""
    evidence_root = governed_sead_evidence_root(context_root)
    documents = read_validated_sead_evidence_documents(
        evidence_root,
        _SEAD_EVIDENCE_DOCUMENTS,
        expected_run_id=expected_run_id,
        expected_manifest_sha256=expected_manifest_sha256,
    )
    claims = documents["chronology_claims.json"]
    observations = documents["source_native_observations.json"]
    relations = documents["observation_relation_index.json"]
    events = documents["evidence_events.json"]
    validate_evidence_headers(claims, observations, relations, events)
    run_id = _required_text(claims.get("source_run_id"), "SEAD source run ID")
    acquisition_root = context_root / "sead" / "raw" / "acquisitions" / run_id
    admission = _validate_sead_claim_parents(acquisition_root, claims)
    manifest = _read_json_object(
        evidence_root / "evidence_materialization_manifest.json",
        "SEAD evidence materialization manifest",
    )
    file_set_sha256 = _required_text(
        manifest.get("file_set_sha256"), "SEAD evidence file-set SHA-256"
    )
    admission_sha256 = hashlib.sha256(
        _read_regular_bytes(acquisition_root / "admission.json", "SEAD admission")
    ).hexdigest()
    if admission_sha256 != expected_admission_sha256:
        raise ValueError("SEAD governed admission digest changed")
    return EvidenceBundle(
        context_root=context_root,
        acquisition_root=acquisition_root,
        claims=claims,
        observations=observations,
        relations=relations,
        events=events,
        manifest=manifest,
        admission=admission,
        run_id=run_id,
        file_set_sha256=file_set_sha256,
    )


def validate_evidence_headers(
    claims: Mapping[str, object],
    observations: Mapping[str, object],
    relations: Mapping[str, object],
    events: Mapping[str, object],
) -> None:
    """Require a single source, run, build, and acquisition identity."""
    documents = (
        (claims, "sead-chronology-claim-bundle.v1", "source_build_id"),
        (observations, "sead-source-native-evidence-bundle.v1", "build_id"),
        (relations, "sead-evidence-relation-index.v1", "build_id"),
        (events, "sead-evidence-event-bundle.v1", "build_id"),
    )
    run_id = claims.get("source_run_id")
    build_id = claims.get("source_build_id")
    acquisition_digest = claims.get("acquisition_manifest_sha256")
    for document, schema, build_field in documents:
        if document.get("schema_version") != schema:
            raise ValueError(f"SEAD evidence schema is unsupported: {schema}")
        if document.get("source_family") != "sead":
            raise ValueError("SEAD evidence source family changed")
        if document.get("source_run_id") != run_id:
            raise ValueError("SEAD evidence source run identities diverge")
        if document.get(build_field) != build_id:
            raise ValueError("SEAD evidence build identities diverge")
        if document.get("acquisition_manifest_sha256") != acquisition_digest:
            raise ValueError("SEAD evidence acquisition identities diverge")
    if (
        claims.get("propagation_status") != "refused"
        or claims.get("propagation_reason_code") != "source_classification_not_accepted"
    ):
        raise ValueError("SEAD propagation refusal posture changed")


def object_rows(
    document: Mapping[str, object], field: str, label: str
) -> list[Mapping[str, object]]:
    """Return a required list containing only mapping rows."""
    rows = document.get(field)
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError(f"{label} must be object rows")
    return cast(list[Mapping[str, object]], rows)
