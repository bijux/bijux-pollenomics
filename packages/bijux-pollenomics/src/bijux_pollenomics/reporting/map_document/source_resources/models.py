"""Explicit input custody and metadata-only Atlas resource projection values."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any


def _published_base_url(value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) > 1024
        or re.fullmatch(r"/(?:[A-Za-z0-9][A-Za-z0-9._-]*/)*", value) is None
        or "artifacts" in {part.casefold() for part in value.split("/")}
    ):
        raise ValueError("Atlas source archive requires a canonical public URL prefix")
    return value


@dataclass(frozen=True)
class AtlasResourceArchiveInput:
    """Independent shared archive identity and an explicit portable public route."""

    directory: Path
    expected_manifest_sha256: str
    published_base_url: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.expected_manifest_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.expected_manifest_sha256) is None
        ):
            raise ValueError("Atlas source archive requires a manifest SHA-256")
        _published_base_url(self.published_base_url)


@dataclass(frozen=True)
class AtlasResourceCatalogueInput:
    """A publication and its independently configured manifest identity."""

    directory: Path
    expected_manifest_sha256: str
    archive: AtlasResourceArchiveInput | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.expected_manifest_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.expected_manifest_sha256) is None
        ):
            raise ValueError("Atlas resource catalogue requires a manifest SHA-256")
        if self.archive is not None and not isinstance(
            self.archive, AtlasResourceArchiveInput
        ):
            raise ValueError("Atlas resource archive input has the wrong owner")


@dataclass(frozen=True)
class AtlasResourceCatalogue:
    """Detached source metadata; these records carry no scientific admission."""

    resource_records: tuple[dict[str, Any], ...]
    site_records: tuple[dict[str, Any], ...]
    legacy_site_references: tuple[dict[str, Any], ...]
    source_descriptors: dict[str, Any]
    provenance: dict[str, Any]
    summary: dict[str, Any]
