"""Independent federation dependencies and detached, outcome-free source metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any


def _digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


@dataclass(frozen=True)
class AtlasAncillaryFederationInput:
    """An explicit dated federation, independent context and capsule resolvers."""

    directory: Path
    expected_manifest_sha256: str
    context_directory: Path
    expected_context_sha256: str
    capsule_sources: Mapping[str, Path]
    evidence_sources: Mapping[str, Path] | None = None

    def __post_init__(self) -> None:
        if not _digest(self.expected_manifest_sha256) or not _digest(
            self.expected_context_sha256
        ):
            raise ValueError(
                "Atlas ancillary federation requires independent SHA-256 anchors"
            )
        if not isinstance(self.directory, Path) or not isinstance(
            self.context_directory, Path
        ):
            raise ValueError(
                "Atlas ancillary source directories must be explicit paths"
            )
        if not isinstance(self.capsule_sources, Mapping) or any(
            not _digest(key) or not isinstance(path, Path)
            for key, path in self.capsule_sources.items()
        ):
            raise ValueError("Atlas ancillary capsule resolvers have the wrong owner")
        object.__setattr__(
            self, "capsule_sources", MappingProxyType(dict(self.capsule_sources))
        )
        if self.evidence_sources is not None:
            if not isinstance(self.evidence_sources, Mapping) or any(
                not _digest(key) or not isinstance(path, Path)
                for key, path in self.evidence_sources.items()
            ):
                raise ValueError(
                    "Atlas ancillary evidence resolvers have the wrong owner"
                )
            object.__setattr__(
                self, "evidence_sources", MappingProxyType(dict(self.evidence_sources))
            )


@dataclass(frozen=True)
class AtlasAncillaryMetadata:
    """Source metadata preserves epochs and restrictions without entity admission."""

    slots: tuple[dict[str, Any], ...]
    observations: tuple[dict[str, Any], ...]
    linked_occurrences: tuple[dict[str, Any], ...]
    summary: dict[str, Any]
    provenance: dict[str, Any]
    source_manifest: dict[str, Any]
    integrity_scope: str = field(
        default="current_context_and_capsule_metadata", init=False
    )
    entity_body_hashes_verified: bool = field(default=False, init=False)
    source_assessments_replayed: bool = field(default=False, init=False)
