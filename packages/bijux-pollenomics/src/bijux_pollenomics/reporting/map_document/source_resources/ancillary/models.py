"""Independent federation dependencies and detached, outcome-free source metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
    NeotomaContextArchiveBindings,
)


def _digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


@dataclass(frozen=True)
class AtlasSourceArchiveInput:
    """An independent source archive anchor; no selected source access is granted."""

    directory: Path
    expected_manifest_sha256: str

    def __post_init__(self) -> None:
        """Require an explicit source path and independent manifest digest."""
        if not isinstance(self.directory, Path) or not _digest(
            self.expected_manifest_sha256
        ):
            raise ValueError(
                "Atlas supporting archive requires an explicit Path and manifest SHA-256"
            )


@dataclass(frozen=True)
class AtlasContextArchiveInput(AtlasSourceArchiveInput):
    """Original site context authority remains explicit alongside the current epoch."""

    original: NeotomaContextArchiveBindings

    def __post_init__(self) -> None:
        """Validate separately anchored original source bindings."""
        super().__post_init__()
        if (
            not isinstance(self.original, NeotomaContextArchiveBindings)
            or any(
                not isinstance(value, Path)
                for value in (
                    self.original.context_directory,
                    self.original.native_archive_directory,
                )
            )
            or not all(
                _digest(value)
                for value in (
                    self.original.expected_context_sha256,
                    self.original.expected_native_archive_sha256,
                )
            )
        ):
            raise ValueError(
                "Atlas original context archive bindings require exact independent owners and anchors"
            )


@dataclass(frozen=True)
class AtlasTaxonAncestryArchiveInput(AtlasSourceArchiveInput):
    """Explicit recorded targets and detached chain/baseline metadata resolvers."""

    chain_sources: Mapping[str, Path]
    targets: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        """Freeze explicit metadata resolvers and selected native identities."""
        super().__post_init__()
        if not isinstance(self.chain_sources, Mapping) or any(
            not _digest(key) or not isinstance(path, Path)
            for key, path in self.chain_sources.items()
        ):
            raise ValueError(
                "Atlas ancestry requires explicit chain metadata resolvers"
            )
        if (
            type(self.targets) is not tuple
            or not self.targets
            or any(
                type(row) is not tuple
                or len(row) != 2
                or type(row[0]) is not str
                or row[0] not in {"taxon", "publication"}
                or type(row[1]) is not int
                or not 0 < row[1] < 2**53
                for row in self.targets
            )
            or len(set(self.targets)) != len(self.targets)
        ):
            raise ValueError(
                "Atlas ancestry targets require unique immutable native identities"
            )
        object.__setattr__(
            self, "chain_sources", MappingProxyType(dict(self.chain_sources))
        )


@dataclass(frozen=True)
class AtlasAncillaryArchivesInput:
    """All configured source epochs are retained in immutable per-family populations."""

    unit_metadata: tuple[AtlasSourceArchiveInput, ...] = ()
    reference_tables: tuple[AtlasSourceArchiveInput, ...] = ()
    context_resources: tuple[AtlasContextArchiveInput, ...] = ()
    taxon_ancestry: tuple[AtlasTaxonAncestryArchiveInput, ...] = ()

    def __post_init__(self) -> None:
        """Keep immutable source owners distinct by family and manifest."""
        for kind, population, expected in (
            ("unit_metadata", self.unit_metadata, AtlasSourceArchiveInput),
            ("reference_tables", self.reference_tables, AtlasSourceArchiveInput),
            ("context_resources", self.context_resources, AtlasContextArchiveInput),
            ("taxon_ancestry", self.taxon_ancestry, AtlasTaxonAncestryArchiveInput),
        ):
            if type(population) is not tuple or any(
                type(row) is not expected for row in population
            ):
                raise ValueError(
                    f"Atlas {kind} archives require an immutable tuple of exact typed source owners"
                )
            if len({row.expected_manifest_sha256 for row in population}) != len(
                population
            ):
                raise ValueError(f"Atlas {kind} archive identities must be unique")


@dataclass(frozen=True)
class AtlasAncillaryFederationInput:
    """An explicit dated federation, independent context and capsule resolvers."""

    directory: Path
    expected_manifest_sha256: str
    context_directory: Path
    expected_context_sha256: str
    capsule_sources: Mapping[str, Path]
    evidence_sources: Mapping[str, Path] | None = None
    archives: AtlasAncillaryArchivesInput | None = None

    def __post_init__(self) -> None:
        """Freeze independent federation, context, and capsule bindings."""
        if self.archives is not None and not isinstance(
            self.archives, AtlasAncillaryArchivesInput
        ):
            raise ValueError("Atlas supporting archive inputs have the wrong owner")
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


@dataclass(frozen=True)
class AtlasAncillarySupportingMetadata(AtlasAncillaryMetadata):
    """Additional archive metadata is emitted only for explicitly configured epochs."""

    supporting_archives: tuple[dict[str, Any], ...]
