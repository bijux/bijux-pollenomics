"""Independent literal bindings owned by one complete linked evidence operation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..models import NeotomaLinkedEvidence


@dataclass(frozen=True)
class _LinkedEvidenceSources:
    """Bind evidence, current metadata and exact captures without native-body caches."""

    evidence: NeotomaLinkedEvidence
    source_facets: Mapping[str, Path]
    capture_sources: Mapping[str, Path]
    context_directory: Path
    expected_context_sha256: str
    native_archive_directory: Path
    expected_native_archive_sha256: str
