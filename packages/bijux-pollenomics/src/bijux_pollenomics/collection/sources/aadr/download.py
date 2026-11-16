from __future__ import annotations

from collections.abc import Callable
import hashlib
from pathlib import Path

from ....core.http import BINARY_MAX_BYTES
from .constants import (
    AADR_DATAVERSE_PERSISTENT_ID,
    AADR_DOWNLOAD_URL_TEMPLATE,
    REQUEST_HEADERS,
)
from .models import AadrAnnoDownloadReport, AadrAnnoFile, AadrReleaseResolution
from .resolution import resolve_aadr_release, validate_release_version

# Release metadata cannot raise the operational ceiling for in-memory acquisition.
AADR_ANNO_MAX_BYTES = 256 * 1024 * 1024


def download_aadr_anno_files(
    output_root: Path,
    version: str,
    *,
    fetch_binary_fn: Callable[..., bytes],
    fetch_release_history_metadata_fn: Callable[[], dict[str, object]],
    write_json_fn: Callable[[Path, object], None],
) -> AadrAnnoDownloadReport:
    """Download public .anno files after preflighting the operational byte ceiling."""
    output_root = Path(output_root)
    version_dir = output_root / validate_release_version(version)

    resolution = resolve_aadr_release(
        version=version, metadata=fetch_release_history_metadata_fn()
    )
    for anno_file in resolution.anno_files:
        if type(anno_file.filesize) is not int or anno_file.filesize < 0:
            raise ValueError("AADR filesize must be a nonnegative integer")
        if anno_file.filesize > AADR_ANNO_MAX_BYTES:
            raise ValueError(
                f"AADR anno operational byte ceiling exceeded for {anno_file.filename}: "
                f"{anno_file.filesize} > {AADR_ANNO_MAX_BYTES}"
            )
    version_dir.mkdir(parents=True, exist_ok=True)
    downloaded_files: list[Path] = []
    for anno_file in resolution.anno_files:
        dataset_dir = version_dir / anno_file.dataset_name
        dataset_dir.mkdir(parents=True, exist_ok=True)
        destination = dataset_dir / anno_file.filename
        payload = fetch_binary_fn(
            AADR_DOWNLOAD_URL_TEMPLATE.format(file_id=anno_file.file_id),
            headers=REQUEST_HEADERS,
            insecure=False,
            max_bytes=anno_file.filesize or BINARY_MAX_BYTES,
        )
        validate_downloaded_anno_payload(anno_file, payload)
        destination.write_bytes(payload)
        downloaded_files.append(destination)

    manifest_path = version_dir / "release_manifest.json"
    write_release_manifest(
        manifest_path,
        version=version,
        resolution=resolution,
        downloaded_files=downloaded_files,
        write_json_fn=write_json_fn,
    )

    return AadrAnnoDownloadReport(
        version=version,
        version_dir=version_dir,
        downloaded_files=tuple(downloaded_files),
        manifest_path=manifest_path,
    )


def validate_downloaded_anno_payload(anno_file: AadrAnnoFile, payload: bytes) -> None:
    """Verify one downloaded AADR payload against the release metadata."""
    if anno_file.filesize and len(payload) != anno_file.filesize:
        raise ValueError(
            f"Downloaded AADR file size mismatch for {anno_file.filename}: expected {anno_file.filesize}, got {len(payload)}"
        )
    if anno_file.md5:
        digest = hashlib.md5(payload, usedforsecurity=False).hexdigest()
        if digest != anno_file.md5.casefold():
            raise ValueError(
                f"Downloaded AADR checksum mismatch for {anno_file.filename}: expected {anno_file.md5}, got {digest}"
            )


def write_release_manifest(
    path: Path,
    *,
    version: str,
    resolution: AadrReleaseResolution,
    downloaded_files: list[Path],
    write_json_fn: Callable[[Path, object], None],
) -> None:
    """Persist the upstream Dataverse release metadata for one downloaded AADR version."""
    dataset_version = resolution.dataset_version
    write_json_fn(
        path,
        {
            "source": "AADR",
            "persistent_id": AADR_DATAVERSE_PERSISTENT_ID,
            "requested_version": version,
            "dataverse_version_number": dataset_version.get("versionNumber"),
            "dataverse_version_minor_number": dataset_version.get("versionMinorNumber"),
            "release_time": dataset_version.get("releaseTime"),
            "last_update_time": dataset_version.get("lastUpdateTime"),
            "downloaded_files": [
                str(file.relative_to(path.parent)) for file in downloaded_files
            ],
            "anno_files": [
                {
                    "dataset_name": file.dataset_name,
                    "filename": file.filename,
                    "file_id": file.file_id,
                    "md5": file.md5,
                    "filesize": file.filesize,
                }
                for file in resolution.anno_files
            ],
        },
    )


__all__ = [
    "download_aadr_anno_files",
    "validate_downloaded_anno_payload",
    "write_release_manifest",
]
