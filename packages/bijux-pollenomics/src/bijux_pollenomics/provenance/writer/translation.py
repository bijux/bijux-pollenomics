"""Typed translation of canonical release-evidence request records."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal, cast

from ..release_evidence import (
    ArtifactInput,
    ArtifactReference,
    ArtifactRole,
    GateResult,
    GateStatus,
    ReleaseEvidenceError,
)
from .codec import (
    _bool_field,
    _list_field,
    _mapping,
    _string_field,
    _string_value,
)
from .reconciliation import _blocker, _reconciliation
from .service import write_release_evidence_manifest


def _write_request(
    root: Path, output_path: str, request: Mapping[str, object]
) -> dict[str, object]:
    from ..request import validate_release_evidence_request

    expected = {
        "schema_version",
        "code_commit",
        "dirty",
        "dependency_lock_digest",
        "artifacts",
        "gates",
        "reconciliations",
        "blockers",
    }
    if set(request) != expected:
        raise ReleaseEvidenceError("write request fields do not match the v3 contract")
    if request["schema_version"] != "release-evidence-request.v3":
        raise ReleaseEvidenceError("unsupported release-evidence request schema")
    validate_release_evidence_request(root, request)
    return write_release_evidence_manifest(
        root,
        output_path,
        code_commit=_string_field(request, "code_commit"),
        dirty=_bool_field(request, "dirty"),
        dependency_lock_digest=_string_field(request, "dependency_lock_digest"),
        artifacts=tuple(_artifact(item) for item in _list_field(request, "artifacts")),
        gates=tuple(_gate(item) for item in _list_field(request, "gates")),
        reconciliations=tuple(
            _reconciliation(item) for item in _list_field(request, "reconciliations")
        ),
        blockers=tuple(_blocker(item) for item in _list_field(request, "blockers")),
    )


def _artifact(value: object) -> ArtifactInput:
    record = _mapping(value, "artifact")
    expected = {
        "identity",
        "role",
        "path",
        "media_type",
        "schema_version",
        "parents",
        "config_digests",
        "producer_digest",
        "output_digest",
    }
    if set(record) != expected:
        raise ReleaseEvidenceError(
            "artifact request fields do not match the v3 contract"
        )
    parents = tuple(_parent(item) for item in _list_field(record, "parents"))
    config_digests = tuple(
        _string_value(item, "config digest")
        for item in _list_field(record, "config_digests")
    )
    producer_digest = record["producer_digest"]
    if producer_digest is not None and not isinstance(producer_digest, str):
        raise ReleaseEvidenceError("artifact producer_digest must be a string or null")
    return ArtifactInput(
        identity=_string_field(record, "identity"),
        role=cast(ArtifactRole, _string_field(record, "role")),
        path=_string_field(record, "path"),
        media_type=_string_field(record, "media_type"),
        schema_version=_string_field(record, "schema_version"),
        parents=parents,
        config_digests=config_digests,
        producer_digest=producer_digest,
        output_digest=_string_field(record, "output_digest"),
    )


def _parent(value: object) -> ArtifactReference:
    record = _mapping(value, "parent")
    if set(record) != {"identity", "output_digest"}:
        raise ReleaseEvidenceError("parent fields do not match the v3 contract")
    return ArtifactReference(
        identity=_string_field(record, "identity"),
        output_digest=_string_field(record, "output_digest"),
    )


def _gate(value: object) -> GateResult:
    record = _mapping(value, "gate")
    if set(record) != {
        "identity",
        "status",
        "required",
        "evidence_digest",
        "attestation",
        "authority_id",
    }:
        raise ReleaseEvidenceError("gate request fields do not match the v3 contract")
    authority_id = record["authority_id"]
    if authority_id is not None and not isinstance(authority_id, str):
        raise ReleaseEvidenceError("gate authority_id must be a string or null")
    return GateResult(
        identity=_string_field(record, "identity"),
        status=cast(GateStatus, _string_field(record, "status")),
        required=_bool_field(record, "required"),
        evidence_digest=_string_field(record, "evidence_digest"),
        attestation=cast(
            Literal[
                "local_self_attestation",
                "independent_execution_attestation",
                "external_authority_attestation",
            ],
            _string_field(record, "attestation"),
        ),
        authority_id=authority_id,
    )
