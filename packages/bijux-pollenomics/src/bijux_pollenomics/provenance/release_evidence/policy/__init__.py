"""Loading and validation of the governed release-evidence policy."""

from __future__ import annotations

import hashlib as hashlib
import json as json
from pathlib import Path as Path
from pathlib import PurePosixPath as PurePosixPath
from typing import Literal as Literal
from typing import cast as cast

from ..codec import _canonical_json as _canonical_json
from ..codec import _mapping as _mapping
from ..codec import _mapping_list as _mapping_list
from ..codec import _require_digest as _require_digest
from ..codec import _require_identity as _require_identity
from ..codec import _require_unique as _require_unique
from ..codec import _string_field as _string_field
from ..codec import _string_items as _string_items
from ..models import ArtifactRole as ArtifactRole
from ..models import ReleaseEvidenceError as ReleaseEvidenceError
from ..models import _ARTIFACT_ROLES as _ARTIFACT_ROLES
from ..models import _ArtifactOwnershipRule as _ArtifactOwnershipRule
from ..models import _BundleInventory as _BundleInventory
from ..models import _EmbeddedProducerIdentity as _EmbeddedProducerIdentity
from ..models import _PropagationContractIdentity as _PropagationContractIdentity
from ..models import _RELEASE_POLICY_PATH as _RELEASE_POLICY_PATH
from ..models import _ReleaseEvidencePolicy as _ReleaseEvidencePolicy
from ..models import _RequiredArtifact as _RequiredArtifact
from ..models import _RequiredReconciliation as _RequiredReconciliation
from ..repository import _path_has_prefix as _path_has_prefix
from ..repository import _read_repository_file as _read_repository_file
from ..repository import _relative_path as _relative_path
from .artifacts import _parse_artifact_ownership, _parse_required_artifacts
from .contracts import (
    _parse_allowed_digest_aliases,
    _parse_governed_request_ids,
    _parse_propagation_contract,
    _parse_required_gate_ids,
)
from .embedded import _parse_bundle_inventories, _parse_embedded_producers
from .reconciliation import _parse_required_reconciliations


def _load_release_evidence_policy(root: Path) -> _ReleaseEvidencePolicy:
    payload = _read_repository_file(root, _RELEASE_POLICY_PATH)

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseEvidenceError(f"duplicate release policy field: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(payload, object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(
            "release evidence policy is not valid JSON"
        ) from error
    record = _mapping(value, "release evidence policy")
    if payload != _canonical_json(record) + b"\n":
        raise ReleaseEvidenceError("release evidence policy is not canonical JSON")
    if set(record) != {
        "schema_version",
        "mode",
        "recording_authority_path",
        "authorized_producer_paths",
        "artifact_ownership",
        "required_artifacts",
        "embedded_producer_identities",
        "bundle_inventories",
        "allowed_cross_role_digest_aliases",
        "required_gate_ids",
        "governed_request_artifact_ids",
        "propagation_contract",
        "required_reconciliations",
    }:
        raise ReleaseEvidenceError("release evidence policy fields are invalid")
    if record["schema_version"] != "release-evidence-policy.v3":
        raise ReleaseEvidenceError("unsupported release evidence policy schema")
    mode = _string_field(record, "mode")
    if mode not in {"product", "fixture"}:
        raise ReleaseEvidenceError("invalid release evidence policy mode")
    if mode == "fixture" and (root / ".git").exists():
        raise ReleaseEvidenceError(
            "fixture release policy is forbidden in a Git worktree"
        )

    authorized = tuple(_string_items(record, "authorized_producer_paths"))
    if not authorized or list(authorized) != sorted(authorized):
        raise ReleaseEvidenceError(
            "authorized producer paths must be non-empty and sorted"
        )
    _require_unique(authorized, "authorized producer path")
    for path in authorized:
        _relative_path(path)
    recording_authority_path = _string_field(record, "recording_authority_path")
    if recording_authority_path not in authorized:
        raise ReleaseEvidenceError("recording authority must be an authorized producer")

    ownership = _parse_artifact_ownership(record, authorized)
    required_artifacts = _parse_required_artifacts(record, authorized)
    known_required = {item.identity for item in required_artifacts}
    embedded_producers = _parse_embedded_producers(
        record, required_artifacts, known_required
    )
    bundle_inventories = _parse_bundle_inventories(
        record, required_artifacts, known_required
    )
    governed_request_artifact_ids = _parse_governed_request_ids(record, known_required)
    propagation_contract = _parse_propagation_contract(record)
    allowed_aliases = _parse_allowed_digest_aliases(record, known_required)
    required_gate_ids = _parse_required_gate_ids(record)
    required = _parse_required_reconciliations(record)

    return _ReleaseEvidencePolicy(
        mode=mode,
        recording_authority_path=recording_authority_path,
        authorized_producer_paths=authorized,
        artifact_ownership=ownership,
        required_artifacts=required_artifacts,
        embedded_producer_identities=embedded_producers,
        bundle_inventories=bundle_inventories,
        allowed_cross_role_digest_aliases=frozenset(allowed_aliases),
        required_gate_ids=frozenset(required_gate_ids),
        governed_request_artifact_ids=frozenset(governed_request_artifact_ids),
        propagation_contract=propagation_contract,
        required_reconciliations=required,
        output_digest=f"sha256:{hashlib.sha256(payload).hexdigest()}",
    )
