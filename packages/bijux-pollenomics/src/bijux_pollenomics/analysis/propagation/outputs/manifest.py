"""Bundle manifest construction and scenario lineage validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from bijux_pollenomics.analysis.propagation.network import (
    PROPAGATION_SENSITIVITY_SCENARIOS,
)

from .codec import _canonical_json_bytes, _is_sha256_digest, _refuse, _sha256
from .inputs import _json_object
from .producer import _identity_manifest_entries
from .publication import _payload_record_count


def _build_manifest(
    serialized_payloads: Mapping[str, bytes],
    *,
    schemas: Mapping[str, dict[str, Any]],
    build_id: str,
    event_manifest_digest: str,
    classification_contract_version: str,
    classification_review_digest: str,
    accepted_classification_mapping_count: int,
    propagation_contract_version: str,
    propagation_contract_digest: str,
    propagation_producer_id: str,
    propagation_producer_version: str,
    propagation_producer_digest: str,
) -> dict[str, object]:
    entries = tuple(
        {
            "path": name,
            "sha256": _sha256(serialized_payloads[name]),
            "record_count": _payload_record_count(serialized_payloads[name]),
        }
        for name in sorted(serialized_payloads)
    )
    digest_input = "".join(
        f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
        for entry in entries
    ).encode("utf-8")
    schema_entries = tuple(
        {
            "name": name,
            "schema_id": schemas[name]["$id"],
            "sha256": _sha256(_canonical_json_bytes(schemas[name])),
        }
        for name in sorted(schemas)
    )
    return {
        "schema_version": "propagation-output-manifest.v2",
        "build_id": build_id,
        "event_manifest_digest": event_manifest_digest,
        "classification_contract_version": classification_contract_version,
        "classification_review_digest": classification_review_digest,
        "accepted_classification_mapping_count": (
            accepted_classification_mapping_count
        ),
        "propagation_contract_version": propagation_contract_version,
        "propagation_contract_digest": propagation_contract_digest,
        "propagation_producer_id": propagation_producer_id,
        "propagation_producer_version": propagation_producer_version,
        "propagation_producer_digest": propagation_producer_digest,
        "bundle_digest": _sha256(digest_input),
        "payload_file_count": len(entries),
        "files": entries,
        "validated_record_schemas": schema_entries,
    }


def _validate_scenario_artifact_lineage(
    *,
    serialized_payloads: Mapping[str, bytes],
    manifest: Mapping[str, object],
    build_id: str,
    event_manifest_digest: str,
    classification_contract_version: str,
    classification_review_digest: str,
    accepted_classification_mapping_count: int,
    propagation_contract_version: str,
    propagation_contract_digest: str,
    propagation_producer_id: str,
    propagation_producer_version: str,
    propagation_producer_digest: str,
) -> None:
    reason_code = "invalid_scenario_artifact_lineage"
    sensitivity = _json_object(
        serialized_payloads["sensitivity_summary.json"],
        reason_code=reason_code,
        label="sensitivity summary",
    )
    release = _json_object(
        serialized_payloads["release_metadata.json"],
        reason_code=reason_code,
        label="propagation release metadata",
    )
    parsed_manifest = _json_object(
        _canonical_json_bytes(manifest),
        reason_code=reason_code,
        label="propagation manifest",
    )
    expected_lineage: dict[str, object] = {
        "build_id": build_id,
        "event_manifest_digest": event_manifest_digest,
        "classification_contract_version": classification_contract_version,
        "classification_review_digest": classification_review_digest,
        "accepted_classification_mapping_count": (
            accepted_classification_mapping_count
        ),
        "propagation_contract_version": propagation_contract_version,
        "propagation_contract_digest": propagation_contract_digest,
        "propagation_producer_id": propagation_producer_id,
        "propagation_producer_version": propagation_producer_version,
        "propagation_producer_digest": propagation_producer_digest,
    }
    digest_fields = {
        "event_manifest_digest",
        "classification_review_digest",
        "propagation_contract_digest",
        "propagation_producer_digest",
    }
    artifacts = (
        (
            "sensitivity summary",
            sensitivity,
            "propagation-sensitivity-summary.v1",
            len(PROPAGATION_SENSITIVITY_SCENARIOS),
        ),
        (
            "release metadata",
            release,
            "propagation-release-metadata.v2",
            1,
        ),
        (
            "manifest",
            parsed_manifest,
            "propagation-output-manifest.v2",
            None,
        ),
    )
    for label, artifact, schema_version, record_count in artifacts:
        if (
            type(artifact.get("schema_version")) is not str
            or artifact.get("schema_version") != schema_version
        ):
            _refuse(reason_code, f"{label} schema_version is not governed")
        if record_count is not None and (
            type(artifact.get("record_count")) is not int
            or artifact.get("record_count") != record_count
        ):
            _refuse(reason_code, f"{label} record_count is invalid")
        for field_name, expected in expected_lineage.items():
            observed = artifact.get(field_name)
            if field_name == "accepted_classification_mapping_count":
                valid_type = type(observed) is int and observed >= 0
            else:
                valid_type = type(observed) is str and bool(observed.strip())
            if (
                not valid_type
                or field_name in digest_fields
                and not _is_sha256_digest(observed)
                or observed != expected
            ):
                _refuse(
                    reason_code,
                    f"{label} {field_name} does not match governed lineage",
                )

    entries = _identity_manifest_entries(parsed_manifest, reason_code=reason_code)
    if {name for name, _, _ in entries} != set(serialized_payloads):
        _refuse(reason_code, "manifest payload inventory is incomplete")
    for name, digest, count in entries:
        payload_bytes = serialized_payloads[name]
        if digest != _sha256(payload_bytes) or count != _payload_record_count(
            payload_bytes
        ):
            _refuse(reason_code, f"manifest entry is not content-bound: {name}")
    digest_input = "".join(
        f"{name}\0{digest}\0{count}\n" for name, digest, count in entries
    ).encode("utf-8")
    if parsed_manifest.get("bundle_digest") != _sha256(digest_input):
        _refuse(reason_code, "manifest bundle_digest does not reconcile")
