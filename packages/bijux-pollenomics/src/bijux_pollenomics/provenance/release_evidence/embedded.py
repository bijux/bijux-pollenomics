"""Embedded producer, schema, input, and propagation identities."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path, PurePosixPath

from .codec import (
    _mapping,
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
