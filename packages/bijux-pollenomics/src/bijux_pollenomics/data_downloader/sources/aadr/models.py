"""Typed records for resolved AADR release files and downloads."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AadrAnnoFile:
    """One downloadable `.anno` artifact inside an AADR release."""

    filename: str
    file_id: int
    dataset_name: str
    md5: str
    filesize: int


@dataclass(frozen=True)
class AadrReleaseResolution:
    """Resolved AADR release version together with its target files."""

    version: str
    dataset_version: dict[str, object]
    anno_files: tuple[AadrAnnoFile, ...]


@dataclass(frozen=True)
class AadrAnnoDownloadReport:
    """Downloaded AADR manifest for one staged release refresh."""

    version: str
    version_dir: Path
    downloaded_files: tuple[Path, ...]
    manifest_path: Path


__all__ = ["AadrAnnoDownloadReport", "AadrAnnoFile", "AadrReleaseResolution"]
