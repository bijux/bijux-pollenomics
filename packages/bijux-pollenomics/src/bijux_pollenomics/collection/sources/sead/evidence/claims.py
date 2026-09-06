"""Materialize typed SEAD chronology claims from one admitted flat-table snapshot."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Final, cast

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadMaterializedAdmissionSnapshot,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory import (
    build_sead_site_rows_from_acquisition_tables,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization import (
    SeadChronologyClaim,
    normalize_sead_chronology_claims,
)

from .....core.files import write_json

CLAIM_BUNDLE_SCHEMA_VERSION: Final = "sead-chronology-claim-bundle.v1"
CLAIM_SCHEMA_VERSION: Final = "sead-chronology-claim.v1"


def build_sead_chronology_claim_bundle(
    acquisition_root: Path,
) -> dict[str, object]:
    """Validate raw-parent bytes and build one claim for every chronology row."""
    root = acquisition_root.resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("SEAD acquisition root must be a regular directory")
    admission = _read_object(root / "admission.json")
    if admission.get("schema_version") != "sead-acquisition-admission.v1":
        raise ValueError("SEAD admission schema is unsupported")
    if admission.get("source_family") != "sead":
        raise ValueError("SEAD admission source family is inconsistent")
    copied_records = admission.get("copied_files")
    if not isinstance(copied_records, list):
        raise TypeError("SEAD admission copied-file inventory is missing")
    copied = {}
    for record in copied_records:
        if not isinstance(record, dict):
            raise TypeError("SEAD admission copied-file record is invalid")
        relative_path = _required_text(record, "path")
        if relative_path in copied:
            raise ValueError("SEAD admission copied-file paths are duplicated")
        path = root / relative_path
        payload = path.read_bytes()
        expected_size = record.get("byte_count")
        if not isinstance(expected_size, int) or expected_size != len(payload):
            raise ValueError(f"SEAD admitted byte count changed: {relative_path}")
        expected_digest = _required_raw_sha256(record, "sha256")
        if _sha256(payload) != expected_digest:
            raise ValueError(f"SEAD admitted digest changed: {relative_path}")
        copied[relative_path] = payload

    return build_sead_chronology_claim_bundle_from_snapshot(
        SeadMaterializedAdmissionSnapshot(admission=admission, copied_files=copied)
    )


def build_sead_chronology_claim_bundle_from_snapshot(
    snapshot: SeadMaterializedAdmissionSnapshot,
) -> dict[str, object]:
    """Build claims exclusively from bytes retained by admission validation."""
    admission = snapshot.admission
    copied = snapshot.copied_files
    if admission.get("schema_version") != "sead-acquisition-admission.v1":
        raise ValueError("SEAD admission schema is unsupported")
    if admission.get("source_family") != "sead":
        raise ValueError("SEAD admission source family is inconsistent")
    build_id = _required_text(admission, "build_id")
    manifest_sha256 = _required_raw_sha256(admission, "acquisition_manifest_sha256")

    manifest_bytes = copied.get("manifest.json")
    if manifest_bytes is None or _sha256(manifest_bytes) != manifest_sha256:
        raise ValueError("SEAD admission manifest digest is inconsistent")
    table_payloads: dict[str, list[dict[str, object]]] = {}
    payload_digests: dict[str, str] = {}
    for table in SEAD_LINKED_SOURCE_TABLES:
        relative_path = f"payloads/{table}.json"
        payload_bytes = copied.get(relative_path)
        if payload_bytes is None:
            raise ValueError(f"SEAD admitted table payload is missing: {table}")
        document = _decode_object(payload_bytes, relative_path)
        if document.get("table") != table:
            raise ValueError(f"SEAD admitted table identity changed: {table}")
        rows = document.get("rows")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError(f"SEAD admitted rows are invalid: {table}")
        table_payloads[table] = [dict(row) for row in rows]
        payload_digests[table] = _sha256(payload_bytes)

    decisions_bytes = copied.get("country-decisions.json")
    if decisions_bytes is None:
        raise ValueError("SEAD admitted country decisions are missing")
    decisions_document = _decode_object(decisions_bytes, "country-decisions.json")
    decision_rows = decisions_document.get("decisions")
    if not isinstance(decision_rows, list) or any(
        not isinstance(row, dict) for row in decision_rows
    ):
        raise ValueError("SEAD admitted country decisions are invalid")
    decisions = {
        _positive_int(row.get("site_id"), "SEAD country decision site_id"): row
        for row in cast(list[dict[str, object]], decision_rows)
    }

    site_rows, relation_summary = build_sead_site_rows_from_acquisition_tables(
        table_payloads
    )
    for site in site_rows:
        site_id = _positive_int(site.get("site_id"), "SEAD site_id")
        decision = decisions.get(site_id)
        if decision is None:
            raise ValueError(f"SEAD admitted site lacks a country decision: {site_id}")
        country_code = _required_text(decision, "governed_country_code")
        if country_code not in {"SE", "DK", "NO", "FI"}:
            raise ValueError("SEAD admitted site must have an assigned Nordic country")
        decision_detail = decision.get("decision")
        if not isinstance(decision_detail, dict):
            raise TypeError("SEAD admitted country decision detail is invalid")
        site["country_code"] = country_code
        site["country_assignment_method"] = _required_text(
            decision_detail, "decision_method"
        )

    claims = normalize_sead_chronology_claims(
        site_rows,
        provenance_record_id=f"sead-acquisition-manifest:{manifest_sha256}",
        build_id=build_id,
    )
    for claim in claims:
        claim_row = cast(dict[str, object], claim)
        claim_row["schema_version"] = CLAIM_SCHEMA_VERSION
        claim_row["source_payload_sha256"] = payload_digests[claim["source_table"]]
        claim_row["acquisition_manifest_sha256"] = manifest_sha256

    country_counts = _partition_counts(claims, "country_code")
    claim_type_counts = _partition_counts(claims, "claim_type")
    comparability_counts = _partition_counts(claims, "comparability_status")
    eligibility_counts = _partition_counts(claims, "chronology_eligibility")
    refusal_reasons = Counter(
        reason for claim in claims for reason in claim["reason_codes"]
    )
    declared_scope = admission.get("declared_scope")
    full_evidence_admission = (
        isinstance(declared_scope, Mapping)
        and declared_scope.get("scope_key") == "full_evidence_relations"
        and declared_scope.get("table_count") == 61
        and declared_scope.get("join_count") == 86
    )
    return {
        "schema_version": CLAIM_BUNDLE_SCHEMA_VERSION,
        "source_family": "sead",
        "source_run_id": _required_text(admission, "run_id"),
        "source_scope_id": _required_text(admission, "scope_id"),
        "source_build_id": build_id,
        "acquisition_manifest_sha256": manifest_sha256,
        "acquisition_bundle_sha256": _required_text(
            admission, "acquisition_bundle_sha256"
        ),
        "country_decisions_sha256": _sha256(decisions_bytes),
        "table_payload_sha256": dict(sorted(payload_digests.items())),
        "relation_summary": relation_summary,
        "claim_count": len(claims),
        "country_counts": country_counts,
        "claim_type_counts": claim_type_counts,
        "comparability_counts": comparability_counts,
        "chronology_eligibility_counts": eligibility_counts,
        "refusal_reason_counts": dict(sorted(refusal_reasons.items())),
        "propagation_status": "refused",
        "propagation_reason_code": (
            "source_classification_not_accepted"
            if full_evidence_admission
            else "observation_relations_not_captured"
        ),
        "selection_policy": {
            "rule_version": "sead-retain-all-source-chronologies-v1",
            "posture": "retain_all_without_preferred_model",
        },
        "claims": claims,
    }


def write_sead_chronology_claim_bundle(
    acquisition_root: Path, output_path: Path
) -> Path:
    """Write the deterministic claim bundle through the repository JSON writer."""
    destination = output_path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_json(destination, build_sead_chronology_claim_bundle(acquisition_root))
    return destination


def write_sead_chronology_claim_bundle_from_snapshot(
    snapshot: SeadMaterializedAdmissionSnapshot, output_path: Path
) -> Path:
    """Write a claim bundle without reopening admission-controlled inputs."""
    destination = output_path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_json(destination, build_sead_chronology_claim_bundle_from_snapshot(snapshot))
    return destination


def _partition_counts(claims: list[SeadChronologyClaim], field: str) -> dict[str, int]:
    return dict(
        sorted(
            Counter(
                str(cast(Mapping[str, object], claim).get(field) or "UNASSIGNED")
                for claim in claims
            ).items()
        )
    )


def _read_object(path: Path) -> dict[str, object]:
    return _decode_object(path.read_bytes(), path.as_posix())


def _decode_object(payload: bytes, label: str) -> dict[str, object]:
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"SEAD JSON is invalid: {label}") from exc
    if not isinstance(document, dict):
        raise TypeError(f"SEAD JSON object is required: {label}")
    return document


def _required_text(document: Mapping[str, object], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"SEAD {field} must be nonempty text")
    return value.strip()


def _required_raw_sha256(document: Mapping[str, object], field: str) -> str:
    value = _required_text(document, field)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"SEAD {field} must be a lowercase SHA-256")
    return value


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


__all__ = [
    "CLAIM_BUNDLE_SCHEMA_VERSION",
    "CLAIM_SCHEMA_VERSION",
    "build_sead_chronology_claim_bundle",
    "write_sead_chronology_claim_bundle",
]
