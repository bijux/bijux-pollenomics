"""Embedded producer, schema, input, and propagation identities."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path, PurePosixPath

from .codec import (
    _digest_bytes,
    _mapping,
    _require_identity,
    _require_unique,
    _string_field,
)
from .models import (
    ArtifactInput,
    ReleaseEvidenceError,
    _ReleaseEvidencePolicy,
    _RequiredArtifact,
)
from .repository import (
    _read_repository_file,
)

_BUNDLE_RELEASE_METADATA_CONTRACTS = {
    "classification-audit-manifest.v1": (
        "classification-release-metadata.v1",
        "classification_release",
        "release_reason_codes",
        frozenset({"refused", "review_required"}),
    ),
    "propagation-output-manifest.v2": (
        "propagation-release-metadata.v2",
        "propagation_release",
        "reason_codes",
        frozenset({"refused", "review_required"}),
    ),
}


def _bundle_release_refusal_reasons(
    root: Path,
    artifacts: Mapping[str, ArtifactInput],
    policy: _ReleaseEvidencePolicy,
) -> tuple[str, ...]:
    """Read explicit release posture from manifest-bound bundle metadata."""
    reasons: list[str] = []
    for inventory in policy.bundle_inventories:
        if "release_metadata.json" not in inventory.filenames:
            continue
        artifact = artifacts[inventory.artifact_identity]
        manifest_payload = _read_repository_file(root, artifact.path)
        if _digest_bytes(manifest_payload) != artifact.output_digest:
            raise ReleaseEvidenceError(
                f"release metadata manifest identity changed: {artifact.identity}"
            )
        manifest = _release_metadata_object(
            manifest_payload, f"{artifact.identity} bundle manifest"
        )
        entries = manifest.get("files")
        if not isinstance(entries, list):
            raise ReleaseEvidenceError(
                f"release metadata manifest files are missing: {artifact.identity}"
            )
        metadata_entries = [
            _mapping(entry, "release metadata manifest entry")
            for entry in entries
            if isinstance(entry, Mapping)
            and entry.get("path") == "release_metadata.json"
        ]
        if len(metadata_entries) != 1:
            raise ReleaseEvidenceError(
                f"release metadata manifest entry is missing: {artifact.identity}"
            )
        metadata_path = (
            PurePosixPath(artifact.path).parent / "release_metadata.json"
        ).as_posix()
        metadata_payload = _read_repository_file(root, metadata_path)
        expected_digest = metadata_entries[0].get("sha256")
        if (
            not isinstance(expected_digest, str)
            or hashlib.sha256(metadata_payload).hexdigest() != expected_digest
        ):
            raise ReleaseEvidenceError(
                f"release metadata identity changed: {artifact.identity}"
            )
        metadata = _release_metadata_object(
            metadata_payload, f"{artifact.identity} release metadata"
        )
        schema_version = _release_metadata_text(
            metadata, "schema_version", artifact.identity
        )
        status_namespace = _release_metadata_text(
            metadata, "status_namespace", artifact.identity
        )
        release_status = _release_metadata_text(
            metadata, "release_status", artifact.identity
        )
        for field, value in (
            ("schema_version", schema_version),
            ("status_namespace", status_namespace),
            ("release_status", release_status),
        ):
            _require_identity(value, f"release metadata {field}")
        public_release_allowed = metadata.get("public_release_allowed")
        if type(public_release_allowed) is not bool:
            raise ReleaseEvidenceError(
                f"release metadata approval is invalid: {artifact.identity}"
            )
        reason_fields = [
            field
            for field in ("reason_codes", "release_reason_codes")
            if field in metadata
        ]
        if len(reason_fields) != 1:
            raise ReleaseEvidenceError(
                f"release metadata reason vocabulary is invalid: {artifact.identity}"
            )
        raw_reason_codes = metadata[reason_fields[0]]
        if not isinstance(raw_reason_codes, list) or any(
            not isinstance(reason_code, str) for reason_code in raw_reason_codes
        ):
            raise ReleaseEvidenceError(
                f"release metadata reason codes are invalid: {artifact.identity}"
            )
        reason_codes = tuple(raw_reason_codes)
        _require_unique(reason_codes, "release metadata reason code")
        for reason_code in reason_codes:
            _require_identity(reason_code, "release metadata reason code")
        contract = _BUNDLE_RELEASE_METADATA_CONTRACTS.get(artifact.schema_version)
        if policy.mode == "product" and contract is None:
            raise ReleaseEvidenceError(
                f"release metadata contract is not governed: {artifact.identity}"
            )
        if contract is not None:
            (
                expected_schema,
                expected_namespace,
                expected_reason_field,
                allowed_statuses,
            ) = contract
            if schema_version != expected_schema:
                raise ReleaseEvidenceError(
                    f"release metadata schema does not match bundle authority: "
                    f"{artifact.identity}"
                )
            if status_namespace != expected_namespace:
                raise ReleaseEvidenceError(
                    f"release metadata namespace does not match bundle authority: "
                    f"{artifact.identity}"
                )
            if reason_fields[0] != expected_reason_field:
                raise ReleaseEvidenceError(
                    f"release metadata reason vocabulary does not match bundle "
                    f"authority: {artifact.identity}"
                )
            if release_status not in allowed_statuses:
                raise ReleaseEvidenceError(
                    f"release metadata status is not governed: {artifact.identity}"
                )
        if public_release_allowed and (
            release_status in {"refused", "review_required"} or reason_codes
        ):
            raise ReleaseEvidenceError(
                f"release metadata approval contradicts refusal posture: "
                f"{artifact.identity}"
            )
        if not public_release_allowed and not reason_codes:
            raise ReleaseEvidenceError(
                f"release metadata refusal lacks reasons: {artifact.identity}"
            )
        if not public_release_allowed:
            reasons.extend(
                f"required_artifact_release_refused:{artifact.identity}:"
                f"{schema_version}:{status_namespace}:{release_status}:{reason_code}"
                for reason_code in reason_codes
            )
    return tuple(sorted(reasons))


def _release_metadata_object(payload: bytes, label: str) -> Mapping[str, object]:
    """Decode a bundle posture object after its bytes have been identity-checked."""
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(f"invalid JSON in {label}") from error
    if not isinstance(document, Mapping):
        raise ReleaseEvidenceError(f"JSON object required in {label}")
    return document


def _release_metadata_text(
    metadata: Mapping[str, object], field: str, artifact_identity: str
) -> str:
    """Read a non-empty governed release-posture vocabulary value."""
    value = metadata.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ReleaseEvidenceError(
            f"release metadata {field} is invalid: {artifact_identity}"
        )
    return value


def _validate_embedded_producer_identities(
    root: Path,
    artifacts: Mapping[str, ArtifactInput],
    policy: _ReleaseEvidencePolicy,
) -> None:
    for requirement in policy.embedded_producer_identities:
        artifact = artifacts[requirement.artifact_identity]
        try:
            document = json.loads(_read_repository_file(root, artifact.path))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ReleaseEvidenceError(
                f"embedded producer identity is not valid JSON: {artifact.identity}"
            ) from error
        if not isinstance(document, Mapping):
            raise ReleaseEvidenceError(
                f"embedded producer identity is missing: {artifact.identity}"
            )
        if (
            document.get(requirement.id_field) != requirement.producer_id
            or document.get(requirement.version_field) != requirement.producer_version
        ):
            raise ReleaseEvidenceError(
                f"embedded producer id/version mismatch: {artifact.identity}"
            )
        source_records = [
            {
                "path": source_path,
                "sha256": hashlib.sha256(
                    _read_repository_file(root, source_path)
                ).hexdigest(),
            }
            for source_path in requirement.source_paths
        ]
        producer_digest = hashlib.sha256(
            json.dumps(source_records, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()
        expected_digest = requirement.digest_prefix + producer_digest
        if document.get(requirement.digest_field) != expected_digest:
            raise ReleaseEvidenceError(
                f"embedded producer digest mismatch: {artifact.identity}"
            )


def _validate_propagation_contract_binding(
    root: Path,
    artifacts: Mapping[str, ArtifactInput],
    policy: _ReleaseEvidencePolicy,
) -> None:
    contract = policy.propagation_contract
    propagation = json.loads(_read_repository_file(root, artifacts["propagation"].path))
    scenario = json.loads(_read_repository_file(root, artifacts["scenario"].path))
    if not isinstance(propagation, Mapping) or not isinstance(scenario, Mapping):
        raise ReleaseEvidenceError("propagation contract evidence must be JSON objects")
    propagation_path = PurePosixPath(artifacts["propagation"].path)
    scenario_path = PurePosixPath(artifacts["scenario"].path)
    if propagation_path.parent != scenario_path.parent:
        raise ReleaseEvidenceError(
            "propagation manifest and sensitivity must share one immutable bundle"
        )
    shared_identity_fields = (
        "build_id",
        "event_manifest_digest",
        "propagation_contract_version",
        "propagation_contract_digest",
        "propagation_producer_id",
        "propagation_producer_version",
        "propagation_producer_digest",
    )
    if any(
        propagation.get(field) is None or propagation.get(field) != scenario.get(field)
        for field in shared_identity_fields
    ):
        raise ReleaseEvidenceError("propagation bundle identity mismatch")
    if propagation.get(
        "propagation_contract_version"
    ) != contract.contract_version or propagation.get(
        "propagation_contract_digest"
    ) != contract.output_digest.removeprefix("sha256:"):
        raise ReleaseEvidenceError("propagation manifest contract identity mismatch")
    files = propagation.get("files")
    if not isinstance(files, list):
        raise ReleaseEvidenceError("propagation manifest file inventory is missing")
    sensitivity_entries = [
        entry
        for entry in files
        if isinstance(entry, Mapping) and entry.get("path") == scenario_path.name
    ]
    sensitivity_payload = _read_repository_file(root, artifacts["scenario"].path)
    if (
        len(sensitivity_entries) != 1
        or sensitivity_entries[0].get("sha256")
        != hashlib.sha256(sensitivity_payload).hexdigest()
    ):
        raise ReleaseEvidenceError(
            "propagation manifest does not bind the sensitivity artifact"
        )
    classification_payload = _read_repository_file(
        root, artifacts["classification"].path
    )
    classification = json.loads(classification_payload)
    if not isinstance(classification, Mapping):
        raise ReleaseEvidenceError("classification lineage evidence is invalid")
    classification_files = classification.get("files")
    accepted_queue_entries = (
        [
            entry
            for entry in classification_files
            if isinstance(entry, Mapping)
            and entry.get("path") == "accepted_mapping_queue.json"
        ]
        if isinstance(classification_files, list)
        else []
    )
    if (
        scenario.get("classification_review_digest")
        != hashlib.sha256(classification_payload).hexdigest()
        or scenario.get("classification_contract_version")
        != classification.get("classification_contract_version")
        or len(accepted_queue_entries) != 1
        or scenario.get("accepted_classification_mapping_count")
        != accepted_queue_entries[0].get("record_count")
    ):
        raise ReleaseEvidenceError("propagation classification lineage mismatch")
    scenarios = scenario.get("scenarios")
    if not isinstance(scenarios, list):
        raise ReleaseEvidenceError("propagation sensitivity scenarios are missing")
    matches = [
        item
        for item in scenarios
        if isinstance(item, Mapping) and item.get("scenario_id") == contract.scenario_id
    ]
    if len(matches) != 1 or (
        matches[0].get("maximum_distance_km") != contract.maximum_distance_km
        or matches[0].get("maximum_lag_years") != contract.maximum_lag_years
    ):
        raise ReleaseEvidenceError("default propagation scenario identity mismatch")


def _validate_embedded_schema_identity(
    root: Path, item: ArtifactInput, requirement: _RequiredArtifact
) -> None:
    if item.media_type != "application/json" and not item.media_type.endswith("+json"):
        if requirement.schema_identity_field is not None:
            raise ReleaseEvidenceError(
                f"non-JSON artifact declares embedded schema identity: {item.identity}"
            )
        return
    payload = _read_repository_file(root, item.path)

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseEvidenceError(
                    f"duplicate JSON field in artifact: {item.identity}"
                )
            result[key] = value
        return result

    try:
        parsed = json.loads(payload, object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(
            f"artifact is not valid JSON: {item.identity}"
        ) from error
    if not isinstance(parsed, Mapping):
        raise ReleaseEvidenceError(f"JSON artifact is not an object: {item.identity}")
    field = requirement.schema_identity_field
    if field is None:
        if any(
            candidate in parsed for candidate in ("schema_version", "schema", "$schema")
        ):
            raise ReleaseEvidenceError(
                f"unversioned JSON artifact exposes an undeclared schema identity: {item.identity}"
            )
        return
    if parsed.get(field) != requirement.schema_version:
        raise ReleaseEvidenceError(
            f"embedded schema identity mismatch: {item.identity}"
        )


def _validate_embedded_input_inventory(
    root: Path, item: ArtifactInput, requirement: _RequiredArtifact
) -> None:
    if not requirement.required_embedded_input_paths:
        return
    try:
        parsed = json.loads(_read_repository_file(root, item.path))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(
            f"embedded input inventory is not valid JSON: {item.identity}"
        ) from error
    if not isinstance(parsed, Mapping) or not isinstance(
        parsed.get("input_artifacts"), list
    ):
        raise ReleaseEvidenceError(
            f"embedded input inventory is missing: {item.identity}"
        )
    observed: dict[str, Mapping[str, object]] = {}
    for raw_record in parsed["input_artifacts"]:
        record = _mapping(raw_record, "embedded input artifact")
        if set(record) != {"path", "sha256", "byte_count"}:
            raise ReleaseEvidenceError(
                f"embedded input record fields are invalid: {item.identity}"
            )
        path = _string_field(record, "path")
        if path in observed:
            raise ReleaseEvidenceError(
                f"duplicate embedded input path: {item.identity}"
            )
        observed[path] = record
    if set(observed) != set(requirement.required_embedded_input_paths):
        raise ReleaseEvidenceError(
            f"embedded input inventory mismatch: {item.identity}"
        )
    for path in requirement.required_embedded_input_paths:
        payload = _read_repository_file(root, path)
        record = observed[path]
        if record["sha256"] != hashlib.sha256(payload).hexdigest() or record[
            "byte_count"
        ] != len(payload):
            raise ReleaseEvidenceError(
                f"embedded input digest mismatch: {item.identity}: {path}"
            )
