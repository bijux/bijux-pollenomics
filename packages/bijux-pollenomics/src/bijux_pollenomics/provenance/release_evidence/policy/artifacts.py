"""Artifact ownership and required-artifact policy validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import _ArtifactOwnershipRule, _RequiredArtifact


def _parse_artifact_ownership(
    record: Mapping[str, object], authorized: Sequence[str]
) -> tuple[_ArtifactOwnershipRule, ...]:
    from . import (
        _ARTIFACT_ROLES,
        _ArtifactOwnershipRule,
        _mapping_list,
        _relative_path,
        _require_unique,
        _string_field,
        cast,
    )
    from . import ArtifactRole, ReleaseEvidenceError

    ownership: list[_ArtifactOwnershipRule] = []
    ownership_keys: list[str] = []
    for item in _mapping_list(record, "artifact_ownership"):
        if set(item) != {"artifact_role", "artifact_path_prefix", "producer_path"}:
            raise ReleaseEvidenceError("artifact ownership policy fields are invalid")
        role = _string_field(item, "artifact_role")
        if role not in _ARTIFACT_ROLES:
            raise ReleaseEvidenceError(f"invalid artifact ownership role: {role}")
        prefix = _string_field(item, "artifact_path_prefix")
        producer_path = _string_field(item, "producer_path")
        _relative_path(prefix)
        _relative_path(producer_path)
        if producer_path not in authorized:
            raise ReleaseEvidenceError(
                f"artifact ownership names an unauthorized producer: {producer_path}"
            )
        ownership.append(
            _ArtifactOwnershipRule(
                artifact_role=cast(ArtifactRole, role),
                artifact_path_prefix=prefix,
                producer_path=producer_path,
            )
        )
        ownership_keys.append(f"{prefix}\0{role}")
    if not ownership:
        raise ReleaseEvidenceError("artifact ownership policy must not be empty")
    _require_unique(ownership_keys, "artifact ownership rule")
    if ownership_keys != sorted(ownership_keys):
        raise ReleaseEvidenceError("artifact ownership rules must be sorted")
    return tuple(ownership)


def _parse_required_artifacts(
    record: Mapping[str, object], authorized: Sequence[str]
) -> tuple[_RequiredArtifact, ...]:
    from . import (
        _ARTIFACT_ROLES,
        _RequiredArtifact,
        _mapping_list,
        _relative_path,
        _require_identity,
        _require_unique,
        _string_field,
        _string_items,
        cast,
    )
    from . import ArtifactRole, ReleaseEvidenceError

    required_artifacts: list[_RequiredArtifact] = []
    required_artifact_identities: list[str] = []
    required_artifact_paths: list[str] = []
    for item in _mapping_list(record, "required_artifacts"):
        if set(item) != {
            "identity",
            "role",
            "path",
            "media_type",
            "schema_version",
            "schema_identity_field",
            "producer_path",
            "required_config_identities",
            "required_parent_identities",
            "required_embedded_input_paths",
        }:
            raise ReleaseEvidenceError("required artifact policy fields are invalid")
        identity = _string_field(item, "identity")
        role = _string_field(item, "role")
        path = _string_field(item, "path")
        media_type = _string_field(item, "media_type")
        schema_version = _string_field(item, "schema_version")
        raw_schema_identity_field = item["schema_identity_field"]
        if raw_schema_identity_field not in {
            None,
            "$schema",
            "schema",
            "schema_version",
        }:
            raise ReleaseEvidenceError(
                f"required artifact schema identity field is invalid: {identity}"
            )
        raw_producer_path = item["producer_path"]
        if raw_producer_path is not None and not isinstance(raw_producer_path, str):
            raise ReleaseEvidenceError(
                f"required artifact producer path is invalid: {identity}"
            )
        required_producer_path = raw_producer_path
        config_identities = tuple(_string_items(item, "required_config_identities"))
        parent_identities = tuple(_string_items(item, "required_parent_identities"))
        embedded_input_paths = tuple(
            _string_items(item, "required_embedded_input_paths")
        )
        _require_identity(identity, "required artifact identity")
        if role not in _ARTIFACT_ROLES:
            raise ReleaseEvidenceError(f"invalid required artifact role: {role}")
        _relative_path(path)
        if not media_type.strip() or not schema_version.strip():
            raise ReleaseEvidenceError(
                f"required artifact lacks media/schema identity: {identity}"
            )
        if (
            required_producer_path is not None
            and required_producer_path not in authorized
        ):
            raise ReleaseEvidenceError(
                f"required artifact names an unauthorized producer: {identity}"
            )
        if list(config_identities) != sorted(config_identities):
            raise ReleaseEvidenceError(
                f"required config identities are not sorted: {identity}"
            )
        _require_unique(config_identities, "required config identity")
        if list(parent_identities) != sorted(parent_identities):
            raise ReleaseEvidenceError(
                f"required parent identities are not sorted: {identity}"
            )
        _require_unique(parent_identities, "required parent identity")
        if list(embedded_input_paths) != sorted(embedded_input_paths):
            raise ReleaseEvidenceError(
                f"required embedded input paths are not sorted: {identity}"
            )
        _require_unique(embedded_input_paths, "required embedded input path")
        for embedded_path in embedded_input_paths:
            _relative_path(embedded_path)
        required_artifacts.append(
            _RequiredArtifact(
                identity=identity,
                role=cast(ArtifactRole, role),
                path=path,
                media_type=media_type,
                schema_version=schema_version,
                schema_identity_field=raw_schema_identity_field,
                producer_path=required_producer_path,
                required_config_identities=config_identities,
                required_parent_identities=parent_identities,
                required_embedded_input_paths=embedded_input_paths,
            )
        )
        required_artifact_identities.append(identity)
        required_artifact_paths.append(path)
    if not required_artifacts:
        raise ReleaseEvidenceError("required artifact inventory must not be empty")
    _require_unique(required_artifact_identities, "required artifact identity")
    _require_unique(required_artifact_paths, "required artifact path")
    if required_artifact_identities != sorted(required_artifact_identities):
        raise ReleaseEvidenceError("required artifacts must be sorted by identity")
    known_required = set(required_artifact_identities)
    for requirement in required_artifacts:
        unknown_configs = set(requirement.required_config_identities) - known_required
        if unknown_configs:
            raise ReleaseEvidenceError(
                f"required artifact has unknown config identities: {requirement.identity}"
            )
        unknown_parents = set(requirement.required_parent_identities) - known_required
        if (
            unknown_parents
            or requirement.identity in requirement.required_parent_identities
        ):
            raise ReleaseEvidenceError(
                f"required artifact has unknown/self parent identities: {requirement.identity}"
            )
    return tuple(required_artifacts)
