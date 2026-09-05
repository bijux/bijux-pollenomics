"""Artifact graph structure and lineage validation."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from pathlib import Path
from .codec import (
    _require_digest,
    _require_identity,
    _require_unique,
    _string_field,
)
from .models import (
    ArtifactInput,
    ReleaseEvidenceError,
    _ARTIFACT_ROLES,
    _CONFIG_ROLES,
    _DERIVED_ROLES,
    _OUTPUT_ROLES,
    _RELEASE_POLICY_PATH,
    _REQUIRED_ROLES,
    _ReleaseEvidencePolicy,
)
from .repository import (
    _hash_repository_object,
    _path_has_prefix,
)

from .bundles import _validate_manifest_bundle_closures
from .embedded import (
    _validate_embedded_input_inventory,
    _validate_embedded_producer_identities,
    _validate_embedded_schema_identity,
    _validate_propagation_contract_binding,
)


def _artifact_record(root: Path, item: ArtifactInput) -> dict[str, object]:
    _require_identity(item.identity, "artifact identity")
    if item.role not in _ARTIFACT_ROLES:
        raise ReleaseEvidenceError(f"invalid artifact role: {item.role}")
    if not item.media_type.strip() or not item.schema_version.strip():
        raise ReleaseEvidenceError(
            f"artifact {item.identity} lacks media/schema identity"
        )
    if item.producer_digest is not None:
        _require_digest(item.producer_digest, f"{item.identity} producer_digest")
    _require_digest(item.output_digest, f"{item.identity} output_digest")
    _require_unique((parent.identity for parent in item.parents), "parent identity")
    for parent in item.parents:
        _require_identity(parent.identity, "parent identity")
        _require_digest(parent.output_digest, "parent output_digest")
    _require_unique(item.config_digests, "config digest")
    for digest in item.config_digests:
        _require_digest(digest, "config digest")

    observed = _hash_repository_object(
        root,
        item.path,
        exclude_python_cache=item.role == "producer",
    )
    if observed["output_digest"] != item.output_digest:
        raise ReleaseEvidenceError(f"artifact digest changed: {item.identity}")
    return {
        "identity": item.identity,
        "role": item.role,
        "path": item.path,
        "media_type": item.media_type,
        "schema_version": item.schema_version,
        "parents": [
            {"identity": parent.identity, "output_digest": parent.output_digest}
            for parent in sorted(item.parents, key=lambda parent: parent.identity)
        ],
        "config_digests": sorted(item.config_digests),
        "producer_digest": item.producer_digest,
        **observed,
    }


def _validate_artifact_graph(
    root: Path,
    artifacts: Sequence[ArtifactInput],
    records: Sequence[Mapping[str, object]],
    dependency_lock_digest: str,
    policy: _ReleaseEvidencePolicy,
) -> None:
    requirements = {item.identity: item for item in policy.required_artifacts}
    if set(requirements) != {item.identity for item in artifacts}:
        missing = sorted(set(requirements) - {item.identity for item in artifacts})
        unexpected = sorted({item.identity for item in artifacts} - set(requirements))
        raise ReleaseEvidenceError(
            f"artifact inventory mismatch; missing={missing}, unexpected={unexpected}"
        )
    roles = {item.role for item in artifacts}
    missing_roles = sorted(_REQUIRED_ROLES - roles)
    if missing_roles:
        raise ReleaseEvidenceError(f"missing required artifact roles: {missing_roles}")
    by_identity = {item.identity: item for item in artifacts}
    digest_by_identity = {
        _string_field(record, "identity"): _string_field(record, "output_digest")
        for record in records
    }
    config_digests = {
        digest_by_identity[item.identity]
        for item in artifacts
        if item.role in _CONFIG_ROLES
    }
    producer_digests = {
        digest_by_identity[item.identity]
        for item in artifacts
        if item.role == "producer"
    }
    if not producer_digests:
        raise ReleaseEvidenceError("at least one producer artifact is required")
    producer_items = [item for item in artifacts if item.role == "producer"]
    _require_unique(
        (digest_by_identity[item.identity] for item in producer_items),
        "producer digest",
    )
    producer_digest_by_path = {
        item.path: digest_by_identity[item.identity] for item in producer_items
    }
    unknown_producer_paths = sorted(
        set(producer_digest_by_path) - set(policy.authorized_producer_paths)
    )
    if unknown_producer_paths:
        raise ReleaseEvidenceError(
            f"unauthorized producer paths: {unknown_producer_paths}"
        )
    lock_digests = {
        digest_by_identity[item.identity]
        for item in artifacts
        if item.role == "dependency_lock"
    }
    if lock_digests != {dependency_lock_digest}:
        raise ReleaseEvidenceError(
            "dependency lock digest does not identify the lock artifact"
        )

    input_paths = {item.path for item in artifacts if item.role not in _OUTPUT_ROLES}
    output_paths = {item.path for item in artifacts if item.role in _OUTPUT_ROLES}
    overlapping_paths = sorted(
        (input_path, output_path)
        for input_path in input_paths
        for output_path in output_paths
        if _path_has_prefix(input_path, output_path)
        or _path_has_prefix(output_path, input_path)
    )
    if overlapping_paths:
        raise ReleaseEvidenceError(
            "generated output overlaps an immutable input (output overwrite): "
            f"{overlapping_paths}"
        )

    policy_artifacts = [
        item
        for item in artifacts
        if item.identity == "release-evidence-policy"
        or item.path == _RELEASE_POLICY_PATH
    ]
    if len(policy_artifacts) != 1:
        raise ReleaseEvidenceError(
            "the fixed release evidence policy artifact is required exactly once"
        )
    policy_artifact = policy_artifacts[0]
    if (
        policy_artifact.identity != "release-evidence-policy"
        or policy_artifact.role != "configuration"
        or policy_artifact.path != _RELEASE_POLICY_PATH
        or policy_artifact.output_digest != policy.output_digest
    ):
        raise ReleaseEvidenceError("release evidence policy artifact is inconsistent")

    for item in artifacts:
        requirement = requirements[item.identity]
        if (
            item.role != requirement.role
            or item.path != requirement.path
            or item.media_type != requirement.media_type
            or item.schema_version != requirement.schema_version
        ):
            raise ReleaseEvidenceError(
                f"artifact does not match its exact product inventory: {item.identity}"
            )
        _validate_embedded_schema_identity(root, item, requirement)
        _validate_embedded_input_inventory(root, item, requirement)
        observed_parent_identities = tuple(
            sorted(parent.identity for parent in item.parents)
        )
        if observed_parent_identities != requirement.required_parent_identities:
            raise ReleaseEvidenceError(
                f"artifact parent inventory mismatch: {item.identity}"
            )
        if requirement.producer_path is None:
            if item.producer_digest is not None:
                raise ReleaseEvidenceError(
                    f"producer asserted for producerless input: {item.identity}"
                )
        elif item.producer_digest not in producer_digests:
            raise ReleaseEvidenceError(f"unknown producer digest: {item.identity}")
        matching_rules = [
            rule
            for rule in policy.artifact_ownership
            if rule.artifact_role == item.role
            and _path_has_prefix(item.path, rule.artifact_path_prefix)
        ]
        if requirement.producer_path is not None and len(matching_rules) != 1:
            raise ReleaseEvidenceError(
                f"artifact ownership policy is not exact for {item.identity}"
            )
        expected_producer = (
            producer_digest_by_path.get(matching_rules[0].producer_path)
            if matching_rules
            else None
        )
        if requirement.producer_path is not None and expected_producer is None:
            raise ReleaseEvidenceError(
                f"authorized producer is absent for {item.identity}"
            )
        if (
            requirement.producer_path is not None
            and item.producer_digest != expected_producer
        ):
            raise ReleaseEvidenceError(
                f"artifact producer ownership mismatch: {item.identity}"
            )
        required_producer_digest = (
            producer_digest_by_path.get(requirement.producer_path)
            if requirement.producer_path is not None
            else None
        )
        if item.producer_digest != required_producer_digest:
            raise ReleaseEvidenceError(
                f"artifact producer does not match exact inventory: {item.identity}"
            )
        if item.role == "producer" and item.producer_digest != item.output_digest:
            raise ReleaseEvidenceError(
                f"producer artifact is not self-identifying: {item.identity}"
            )
        if item.role in _DERIVED_ROLES and not item.parents:
            raise ReleaseEvidenceError(
                f"derived artifact lacks a parent: {item.identity}"
            )
        if item.role in _OUTPUT_ROLES and not item.config_digests:
            raise ReleaseEvidenceError(f"output lacks config digests: {item.identity}")
        if (
            item.role in _OUTPUT_ROLES
            and policy.output_digest not in item.config_digests
        ):
            raise ReleaseEvidenceError(
                f"output lacks release policy digest: {item.identity}"
            )
        expected_config_digests = {
            digest_by_identity[identity]
            for identity in requirement.required_config_identities
        }
        if set(item.config_digests) != expected_config_digests:
            raise ReleaseEvidenceError(
                f"artifact configuration closure mismatch: {item.identity}"
            )
        unknown_configs = set(item.config_digests) - config_digests
        if unknown_configs:
            raise ReleaseEvidenceError(f"unknown config digest: {item.identity}")
        for parent in item.parents:
            if parent.identity not in by_identity:
                raise ReleaseEvidenceError(f"missing parent: {parent.identity}")
            if digest_by_identity[parent.identity] != parent.output_digest:
                raise ReleaseEvidenceError(f"parent digest mismatch: {parent.identity}")

    records_by_digest: dict[str, list[ArtifactInput]] = {}
    for item in artifacts:
        records_by_digest.setdefault(digest_by_identity[item.identity], []).append(item)
    for digest, aliases in records_by_digest.items():
        if len({item.role for item in aliases}) <= 1:
            continue
        identities = {item.identity for item in aliases}
        unauthorized_pairs = [
            frozenset((left, right))
            for left in identities
            for right in identities
            if left < right
            and requirements[left].role != requirements[right].role
            and frozenset((left, right)) not in policy.allowed_cross_role_digest_aliases
        ]
        if unauthorized_pairs:
            raise ReleaseEvidenceError(
                f"unauthorized cross-role digest alias: {digest}"
            )

    used_producers = {
        item.producer_digest for item in artifacts if item.role != "producer"
    }
    unused_producers = sorted(producer_digests - used_producers)
    if unused_producers:
        raise ReleaseEvidenceError(f"unused producer artifacts: {unused_producers}")

    _reject_cycles(by_identity)
    _validate_embedded_producer_identities(root, by_identity, policy)
    _validate_manifest_bundle_closures(root, by_identity, policy)
    if policy.mode == "product":
        _validate_propagation_contract_binding(root, by_identity, policy)
    for item in artifacts:
        if item.role == "generated_output" and not _has_source_ancestor(
            item.identity, by_identity
        ):
            raise ReleaseEvidenceError(f"output lacks source lineage: {item.identity}")


def _reject_cycles(artifacts: Mapping[str, ArtifactInput]) -> None:
    visited: set[str] = set()
    active: set[str] = set()

    def visit(identity: str) -> None:
        if identity in active:
            raise ReleaseEvidenceError(f"artifact lineage cycle at {identity}")
        if identity in visited:
            return
        active.add(identity)
        for parent in artifacts[identity].parents:
            visit(parent.identity)
        active.remove(identity)
        visited.add(identity)

    for identity in sorted(artifacts):
        visit(identity)


def _has_source_ancestor(identity: str, artifacts: Mapping[str, ArtifactInput]) -> bool:
    item = artifacts[identity]
    if item.role in {"source_receipt", "source_snapshot"}:
        return True
    return any(
        _has_source_ancestor(parent.identity, artifacts) for parent in item.parents
    )
