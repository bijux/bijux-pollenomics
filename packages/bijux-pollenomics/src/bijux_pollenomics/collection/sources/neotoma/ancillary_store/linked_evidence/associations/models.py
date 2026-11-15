"""Explicit source anchors and finite bounds for later entity associations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ....capture.resources.models import DEFAULT_RESOURCE_LIMITS, NeotomaResourceLimits

SCHEMA = "neotoma-linked-source-associations.v1"
MAX_TARGETS = 10000
MAX_PARTS = 256
PART_TARGET_BYTES = 2 * 1024 * 1024
MAX_PART_BYTES = 3 * 1024 * 1024
MAX_METADATA_BYTES = 16 * 1024 * 1024
MAX_BYTES = 256 * 1024 * 1024


@dataclass(frozen=True)
class NeotomaLinkedAssociationInputs:
    """Independently pinned source view, metadata context and literal entity owners."""

    federation_directory: Path
    expected_federation_sha256: str
    context_directory: Path
    expected_context_sha256: str
    native_archive_directory: Path
    expected_native_archive_sha256: str
    capsule_sources: Mapping[str, Path]
    evidence_sources: Mapping[str, Path] | None = None
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS

    def selection_kwargs(self) -> dict[str, Any]:
        """Pass the original anchors to the maintained selected source owner."""
        return {
            "expected_manifest_sha256": self.expected_federation_sha256,
            "expected_context_sha256": self.expected_context_sha256,
            "expected_native_archive_sha256": self.expected_native_archive_sha256,
            "context_directory": self.context_directory,
            "native_archive_directory": self.native_archive_directory,
            "capsule_sources": self.capsule_sources,
            "evidence_sources": self.evidence_sources,
            "limits": self.limits,
        }

    def anchors(self, evidence_sha256: str) -> dict[str, str]:
        """Portable logical identities, without developer paths or copied sources."""
        return {
            "federation_manifest_sha256": self.expected_federation_sha256,
            "context_manifest_sha256": self.expected_context_sha256,
            "native_archive_manifest_sha256": self.expected_native_archive_sha256,
            "evidence_manifest_sha256": evidence_sha256,
        }
