"""Build an opt-in derived chronology overlay without replacing retained evidence."""

from collections.abc import Mapping, Sequence
import json
from pathlib import Path
from typing import Any

_ENRICHMENT_FIELDS = frozenset(
    {
        "observation_relation_id",
        "linked_source_native_observation_count",
        "observation_link_status",
        "propagation_reason_codes",
    }
)
_BOUND_FIELDS = ("time_start_bp", "time_end_bp")


def _canonical(value: object) -> bytes:
    """Compare JSON types as well as values, independent of object key order."""
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    except (TypeError, ValueError) as error:
        raise ValueError("SEAD chronology is not canonical JSON") from error


def _index(
    rows: Sequence[Mapping[str, object]], expected_count: int
) -> dict[str, Mapping[str, object]]:
    if len(rows) != expected_count:
        raise ValueError("SEAD chronology count differs")
    result: dict[str, Mapping[str, object]] = {}
    for row in rows:
        identifier = row.get("chronology_claim_id")
        if not isinstance(identifier, str) or not identifier or identifier in result:
            raise ValueError("SEAD chronology identity differs")
        result[identifier] = row
    return result


def _shared(row: Mapping[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    fields = {key: value for key, value in row.items() if key not in _ENRICHMENT_FIELDS}
    age = fields.get("source_age_value")
    if (
        not isinstance(age, dict)
        or any(key not in age for key in _BOUND_FIELDS)
        or "original_interval_orientation" not in fields
    ):
        raise ValueError("SEAD chronology derived interval is incomplete")
    fields["source_age_value"] = {
        key: value for key, value in age.items() if key not in _BOUND_FIELDS
    }
    fields.pop("original_interval_orientation")
    return fields, age


def reconcile_chronology_rows(
    retained: Sequence[Mapping[str, object]],
    corrected: Sequence[Mapping[str, object]],
    *,
    expected_count: int,
) -> list[dict[str, Any]]:
    """Return changed derived fields only after reconciling every claim identity."""
    old = _index(retained, expected_count)
    new = _index(corrected, expected_count)
    if old.keys() != new.keys():
        raise ValueError("SEAD chronology identity sets differ")
    result: list[dict[str, Any]] = []
    for identifier in sorted(old):
        original, revised = old[identifier], new[identifier]
        original_shared, original_age = _shared(original)
        revised_shared, revised_age = _shared(revised)
        if _canonical(original_shared) != _canonical(revised_shared):
            raise ValueError(f"SEAD chronology nonderived fields differ: {identifier}")
        previous = [original_age[key] for key in _BOUND_FIELDS] + [
            original["original_interval_orientation"]
        ]
        current = [revised_age[key] for key in _BOUND_FIELDS] + [
            revised["original_interval_orientation"]
        ]
        if _canonical(previous) != _canonical(current):
            result.append(
                {
                    "chronology_claim_id": identifier,
                    "time_start_bp": current[0],
                    "time_end_bp": current[1],
                    "original_interval_orientation": current[2],
                }
            )
    return result


def validate_chronology_lineage(
    lineage_bytes: bytes,
    claim_bytes: bytes,
    admission: Mapping[str, object],
    expected_sha256: str,
) -> None:
    """Bind the chronology-relevant lineage fields to the captured admission."""
    import hashlib

    from bijux_pollenomics.collection.sources.sead.collection.repository_surfaces.contract import (
        historical_country_membership,
    )
    from bijux_pollenomics.evidence.sources.sead import (
        SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )

    if (
        len(expected_sha256) != 64
        or any(c not in "0123456789abcdef" for c in expected_sha256)
        or hashlib.sha256(lineage_bytes).hexdigest() != expected_sha256
    ):
        raise ValueError("SEAD chronology lineage digest differs")
    try:
        lineage = json.loads(lineage_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("SEAD chronology lineage is invalid") from error
    if not isinstance(lineage, dict):
        raise ValueError("SEAD chronology lineage is invalid")
    membership = historical_country_membership()
    if (
        lineage.get("schema_version") != "sead-normalized-surface-lineage.v2"
        or lineage.get("country_membership") != membership
        or any(
            lineage.get(field) != admission.get(source)
            for field, source in (
                ("source_run_id", "run_id"),
                ("build_id", "build_id"),
                ("acquisition_manifest_sha256", "acquisition_manifest_sha256"),
                ("parent_admission_sha256", "parent_admission_sha256"),
                ("acquisition_bundle_sha256", "acquisition_bundle_sha256"),
            )
        )
    ):
        raise ValueError("SEAD chronology lineage identity differs")
    surfaces = lineage.get("normalized_surface_sha256")
    inputs = lineage.get("refresh_input_sha256")
    if (
        not isinstance(surfaces, dict)
        or surfaces.get("normalized/chronology_claims.json")
        != hashlib.sha256(claim_bytes).hexdigest()
        or not isinstance(inputs, dict)
        or inputs.get("evidence/evidence_materialization_manifest.json")
        != SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256
        or inputs.get("boundary/normalized/nordic_country_boundaries.geojson")
        != membership["artifact_digest"].removeprefix("sha256:")
    ):
        raise ValueError("SEAD chronology lineage input differs")


def build_historical_chronology_overlay(
    data_root: Path, historical_country_authority_root: Path, *, lineage_sha256: str
) -> dict[str, Any]:
    """Return an in-memory overlay; a persisting caller must bind executed code identity.

    The lineage checks cover chronology and its historical evidence, not the
    unrelated site or spatial-context surfaces referenced by that lineage.
    """
    import hashlib

    from bijux_pollenomics.collection.sources.sead.acquisition.governed import (
        validate_governed_sead_admission,
    )
    from bijux_pollenomics.collection.sources.sead.collection.repository_surfaces.contract import (
        historical_country_membership,
    )
    from bijux_pollenomics.collection.sources.sead.evidence.claims import (
        build_sead_chronology_claim_bundle_from_snapshot,
    )
    from bijux_pollenomics.core.filesystem import read_regular_file
    from bijux_pollenomics.evidence.sources.sead import (
        SEAD_GOVERNED_ADMISSION_SHA256,
        SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        SEAD_GOVERNED_EVIDENCE_RUN_ID,
        read_validated_sead_evidence_documents,
    )

    root = Path(data_root).absolute()
    authority = Path(historical_country_authority_root).absolute()
    normalized = root / "sead/normalized"
    lineage_bytes = read_regular_file(
        normalized / "source_lineage.json", max_bytes=8 * 1024 * 1024
    )
    if (
        len(lineage_sha256) != 64
        or any(c not in "0123456789abcdef" for c in lineage_sha256)
        or hashlib.sha256(lineage_bytes).hexdigest() != lineage_sha256
    ):
        raise ValueError("SEAD chronology lineage digest differs")
    claim_bytes = read_regular_file(
        normalized / "chronology_claims.json", max_bytes=128 * 1024 * 1024
    )
    snapshot = validate_governed_sead_admission(
        root / "sead/raw/acquisitions" / SEAD_GOVERNED_EVIDENCE_RUN_ID,
        data_root=root,
        historical_country_authority_root=authority,
    )
    if (
        hashlib.sha256(_canonical(dict(snapshot.admission)) + b"\n").hexdigest()
        != SEAD_GOVERNED_ADMISSION_SHA256
    ):
        raise ValueError("SEAD chronology admitted bytes differ")
    validate_chronology_lineage(
        lineage_bytes, claim_bytes, snapshot.admission, lineage_sha256
    )
    computed = build_sead_chronology_claim_bundle_from_snapshot(snapshot)
    try:
        recorded = json.loads(claim_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("SEAD corrected chronology is invalid") from error
    if _canonical(computed) != _canonical(recorded):
        raise ValueError("SEAD corrected chronology differs from source recomputation")
    retained = read_validated_sead_evidence_documents(
        normalized / "acquisitions" / SEAD_GOVERNED_EVIDENCE_RUN_ID,
        ("chronology_claims.json",),
        expected_run_id=SEAD_GOVERNED_EVIDENCE_RUN_ID,
        expected_manifest_sha256=SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )["chronology_claims.json"]
    for field in (
        "source_run_id",
        "source_build_id",
        "acquisition_manifest_sha256",
        "acquisition_bundle_sha256",
        "country_decisions_sha256",
        "table_payload_sha256",
        "claim_count",
    ):
        if _canonical(retained.get(field)) != _canonical(computed.get(field)):
            raise ValueError("SEAD chronology source identities differ")
    old_rows, new_rows = retained.get("claims"), computed.get("claims")
    if (
        not isinstance(old_rows, list)
        or not isinstance(new_rows, list)
        or any(not isinstance(row, dict) for row in old_rows + new_rows)
    ):
        raise ValueError("SEAD chronology claim rows are invalid")
    changes = reconcile_chronology_rows(old_rows, new_rows, expected_count=25109)
    return {
        "schema_version": "sead-historical-derived-chronology-overlay.v1",
        "producer_code_identity": "external_execution_receipt_required",
        "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "admission_sha256": SEAD_GOVERNED_ADMISSION_SHA256,
        "evidence_manifest_sha256": SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        "lineage_sha256": lineage_sha256,
        "corrected_claims_sha256": hashlib.sha256(claim_bytes).hexdigest(),
        "admission_input_sha256": {
            name: hashlib.sha256(content).hexdigest()
            for name, content in sorted(snapshot.copied_files.items())
        },
        "country_membership": historical_country_membership(),
        "claim_id_set_sha256": hashlib.sha256(
            _canonical(sorted(row["chronology_claim_id"] for row in old_rows))
        ).hexdigest(),
        "claim_count": 25109,
        "changed_claim_count": len(changes),
        "changes": changes,
        "posture": "derived chronology only; retained evidence and scientific eligibility are unchanged",
    }
