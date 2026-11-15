"""Explicit input custody and metadata-only Atlas resource projection values."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class AtlasResourceCatalogueInput:
    """A publication and its independently configured manifest identity."""

    directory: Path
    expected_manifest_sha256: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.expected_manifest_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.expected_manifest_sha256) is None
        ):
            raise ValueError("Atlas resource catalogue requires a manifest SHA-256")


@dataclass(frozen=True)
class AtlasResourceCatalogue:
    """Detached source metadata; these records carry no scientific admission."""

    resource_records: tuple[dict[str, Any], ...]
    site_records: tuple[dict[str, Any], ...]
    legacy_site_references: tuple[dict[str, Any], ...]
    source_descriptors: dict[str, Any]
    provenance: dict[str, Any]
    summary: dict[str, Any]
