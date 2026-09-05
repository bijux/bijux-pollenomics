"""Discover and bind governed release artifacts to repository objects."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import cast

from ..release_evidence.models import ArtifactInput, ArtifactReference
from ..release_evidence.models import _ReleaseEvidencePolicy


def derive_artifact_inputs(
    root: Path,
    policy: _ReleaseEvidencePolicy,
    *,
    hash_repository_object: Callable[..., dict[str, object]],
) -> tuple[tuple[ArtifactInput, ...], dict[str, str]]:
    """Bind the exact governed artifact graph to its repository objects."""
    digests = {
        requirement.identity: cast(
            str,
            hash_repository_object(
                root,
                requirement.path,
                exclude_python_cache=requirement.role == "producer",
            )["output_digest"],
        )
        for requirement in policy.required_artifacts
    }
    producer_digests = {
        requirement.path: digests[requirement.identity]
        for requirement in policy.required_artifacts
        if requirement.role == "producer"
    }
    artifacts = tuple(
        ArtifactInput(
            identity=requirement.identity,
            role=requirement.role,
            path=requirement.path,
            media_type=requirement.media_type,
            schema_version=requirement.schema_version,
            parents=tuple(
                ArtifactReference(identity, digests[identity])
                for identity in requirement.required_parent_identities
            ),
            config_digests=tuple(
                digests[identity] for identity in requirement.required_config_identities
            ),
            producer_digest=(
                producer_digests[requirement.producer_path]
                if requirement.producer_path is not None
                else None
            ),
            output_digest=digests[requirement.identity],
        )
        for requirement in policy.required_artifacts
    )
    return artifacts, digests


def artifact_record(artifact: ArtifactInput) -> dict[str, object]:
    """Translate an artifact binding into the canonical request record."""
    return {
        "identity": artifact.identity,
        "role": artifact.role,
        "path": artifact.path,
        "media_type": artifact.media_type,
        "schema_version": artifact.schema_version,
        "parents": [
            {
                "identity": parent.identity,
                "output_digest": parent.output_digest,
            }
            for parent in artifact.parents
        ],
        "config_digests": list(artifact.config_digests),
        "producer_digest": artifact.producer_digest,
        "output_digest": artifact.output_digest,
    }
