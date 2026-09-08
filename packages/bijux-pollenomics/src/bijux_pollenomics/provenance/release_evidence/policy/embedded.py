"""Embedded producer and bundle-inventory policy validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import _BundleInventory, _EmbeddedProducerIdentity, _RequiredArtifact


def _parse_embedded_producers(
    record: Mapping[str, object],
    required_artifacts: Sequence[_RequiredArtifact],
    known_required: Set[str],
) -> tuple[_EmbeddedProducerIdentity, ...]:
    from . import (
        ReleaseEvidenceError,
        _EmbeddedProducerIdentity,
        _mapping_list,
        _path_has_prefix,
        _relative_path,
        _require_identity,
        _require_unique,
        _string_field,
        _string_items,
    )

    embedded_producers: list[_EmbeddedProducerIdentity] = []
    for item in _mapping_list(record, "embedded_producer_identities"):
        if set(item) != {
            "artifact_identity",
            "producer_artifact_identity",
            "producer_id",
            "producer_version",
            "id_field",
            "version_field",
            "digest_field",
            "digest_prefix",
            "source_paths",
        }:
            raise ReleaseEvidenceError(
                "embedded producer identity policy fields are invalid"
            )
        artifact_identity = _string_field(item, "artifact_identity")
        producer_artifact_identity = _string_field(item, "producer_artifact_identity")
        producer_id = _string_field(item, "producer_id")
        producer_version = _string_field(item, "producer_version")
        id_field = _string_field(item, "id_field")
        version_field = _string_field(item, "version_field")
        digest_field = _string_field(item, "digest_field")
        digest_prefix = _string_field(item, "digest_prefix")
        source_paths = tuple(_string_items(item, "source_paths"))
        if artifact_identity not in known_required:
            raise ReleaseEvidenceError(
                "embedded producer names an unknown artifact identity"
            )
        if producer_artifact_identity not in known_required:
            raise ReleaseEvidenceError(
                "embedded producer names an unknown producer artifact"
            )
        producer_requirement = next(
            requirement
            for requirement in required_artifacts
            if requirement.identity == producer_artifact_identity
        )
        artifact_requirement = next(
            requirement
            for requirement in required_artifacts
            if requirement.identity == artifact_identity
        )
        if (
            producer_requirement.role != "producer"
            or artifact_requirement.producer_path != producer_requirement.path
        ):
            raise ReleaseEvidenceError(
                "embedded producer does not match artifact ownership"
            )
        for value, field_name in (
            (producer_id, "embedded producer id"),
            (producer_version, "embedded producer version"),
            (id_field, "embedded producer id field"),
            (version_field, "embedded producer version field"),
            (digest_field, "embedded producer digest field"),
        ):
            _require_identity(value, field_name)
        if digest_prefix not in {"", "sha256:"}:
            raise ReleaseEvidenceError("embedded producer digest prefix is invalid")
        if not source_paths:
            raise ReleaseEvidenceError("embedded producer source closure is empty")
        _require_unique(source_paths, "embedded producer source path")
        for source_path in source_paths:
            _relative_path(source_path)
        if not any(
            _path_has_prefix(source_path, producer_requirement.path)
            for source_path in source_paths
        ):
            raise ReleaseEvidenceError(
                "embedded producer closure does not include its owned source tree"
            )
        embedded_producers.append(
            _EmbeddedProducerIdentity(
                artifact_identity=artifact_identity,
                producer_artifact_identity=producer_artifact_identity,
                producer_id=producer_id,
                producer_version=producer_version,
                id_field=id_field,
                version_field=version_field,
                digest_field=digest_field,
                digest_prefix=digest_prefix,
                source_paths=source_paths,
            )
        )
    embedded_artifact_identities = [
        item.artifact_identity for item in embedded_producers
    ]
    _require_unique(embedded_artifact_identities, "embedded producer artifact identity")
    if embedded_artifact_identities != sorted(embedded_artifact_identities):
        raise ReleaseEvidenceError(
            "embedded producer identities must be sorted by artifact identity"
        )
    return tuple(embedded_producers)


def _parse_bundle_inventories(
    record: Mapping[str, object],
    required_artifacts: Sequence[_RequiredArtifact],
    known_required: Set[str],
) -> tuple[_BundleInventory, ...]:
    from . import (
        PurePosixPath,
        ReleaseEvidenceError,
        _BundleInventory,
        _mapping_list,
        _relative_path,
        _require_unique,
        _string_field,
        _string_items,
    )

    bundle_inventories: list[_BundleInventory] = []
    for item in _mapping_list(record, "bundle_inventories"):
        if set(item) != {"artifact_identity", "filenames"}:
            raise ReleaseEvidenceError("bundle inventory policy fields are invalid")
        artifact_identity = _string_field(item, "artifact_identity")
        filenames = tuple(_string_items(item, "filenames"))
        if artifact_identity not in known_required:
            raise ReleaseEvidenceError("bundle inventory names an unknown artifact")
        artifact_requirement = next(
            requirement
            for requirement in required_artifacts
            if requirement.identity == artifact_identity
        )
        if (
            artifact_requirement.media_type != "application/json"
            or PurePosixPath(artifact_requirement.path).name != "manifest.json"
        ):
            raise ReleaseEvidenceError(
                "bundle inventory artifact is not a JSON manifest"
            )
        if not filenames or list(filenames) != sorted(filenames):
            raise ReleaseEvidenceError(
                "bundle inventory filenames must be non-empty and sorted"
            )
        _require_unique(filenames, "bundle inventory filename")
        for filename in filenames:
            pure_filename = _relative_path(filename)
            if len(pure_filename.parts) != 1 or filename == "manifest.json":
                raise ReleaseEvidenceError("bundle inventory filename is unsafe")
        bundle_inventories.append(
            _BundleInventory(
                artifact_identity=artifact_identity,
                filenames=filenames,
            )
        )
    bundle_artifact_identities = [item.artifact_identity for item in bundle_inventories]
    _require_unique(bundle_artifact_identities, "bundle inventory artifact identity")
    if bundle_artifact_identities != sorted(bundle_artifact_identities):
        raise ReleaseEvidenceError(
            "bundle inventories must be sorted by artifact identity"
        )
    return tuple(bundle_inventories)
