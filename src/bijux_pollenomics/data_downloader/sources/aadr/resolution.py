from __future__ import annotations

import json
from typing import Callable

from .constants import AADR_DATAVERSE_PERSISTENT_ID, AADR_DATAVERSE_VERSIONS_URL
from .models import AadrAnnoFile, AadrReleaseResolution


def resolve_anno_files(version: str, metadata: dict[str, object]) -> tuple[AadrAnnoFile, ...]:
    """Extract one release's public .anno files from the Dataverse version history."""
    return resolve_aadr_release(version=version, metadata=metadata).anno_files


def resolve_aadr_release(version: str, metadata: dict[str, object]) -> AadrReleaseResolution:
    """Resolve one requested AADR release from the Dataverse version history."""
    version_prefix = f"{version}_"
    for dataset_version in iter_release_versions(metadata):
        matched_files = extract_anno_files_from_release(dataset_version, version_prefix=version_prefix)
        if matched_files:
            return AadrReleaseResolution(
                version=version,
                dataset_version=dataset_version,
                anno_files=tuple(validate_anno_files(sorted(matched_files, key=lambda item: item.dataset_name))),
            )
    raise ValueError(
        f"No public .anno files were found for {version} in {AADR_DATAVERSE_PERSISTENT_ID}"
    )


def iter_release_versions(metadata: dict[str, object]) -> list[dict[str, object]]:
    """Return Dataverse release versions in descending publication order."""
    versions = metadata.get("data", [])
    if not isinstance(versions, list):
        raise ValueError("Unexpected Dataverse metadata: missing version history")
    return [version for version in versions if isinstance(version, dict)]


def extract_anno_files_from_release(
    dataset_version: dict[str, object],
    *,
    version_prefix: str,
) -> list[AadrAnnoFile]:
    """Extract public `.anno` files for one Dataverse dataset version."""
    files = dataset_version.get("files", [])
    if not isinstance(files, list):
        return []

    matched_files: list[AadrAnnoFile] = []
    for file_entry in files:
        if not isinstance(file_entry, dict):
            continue
        data_file = file_entry.get("dataFile", {})
        if not isinstance(data_file, dict):
            continue
        filename = str(data_file.get("filename", "")).strip()
        if not filename.startswith(version_prefix) or not filename.endswith(".anno"):
            continue
        matched_files.append(
            AadrAnnoFile(
                filename=filename,
                file_id=int(data_file["id"]),
                dataset_name=dataset_directory_name(filename),
                md5=str(data_file.get("md5", "")).strip(),
                filesize=int(data_file.get("filesize", 0) or 0),
            )
        )
    return matched_files


def validate_anno_files(files: list[AadrAnnoFile]) -> list[AadrAnnoFile]:
    """Validate resolved AADR `.anno` files before download."""
    seen_dataset_names: set[str] = set()
    for file in files:
        if not file.filename or file.file_id <= 0:
            raise ValueError("Resolved AADR release includes an invalid public .anno entry")
        if file.dataset_name in seen_dataset_names:
            raise ValueError(f"Resolved AADR release contains duplicate dataset coverage for {file.dataset_name}")
        seen_dataset_names.add(file.dataset_name)
    return files


def dataset_directory_name(filename: str) -> str:
    """Map a public AADR anno filename to its stable local dataset directory."""
    lowered = filename.casefold()
    if "_1240k_" in lowered:
        return "1240k"
    if "_ho_" in lowered:
        return "ho"
    stem = filename.removesuffix(".anno")
    return stem.split("_", 1)[-1].replace("_public", "").casefold()


def fetch_release_history_metadata(
    *,
    fetch_text_fn: Callable[..., str],
) -> dict[str, object]:
    """Fetch the Dataverse release history for the public AADR dataset."""
    return json.loads(fetch_text_fn(AADR_DATAVERSE_VERSIONS_URL, headers={"User-Agent": "Mozilla/5.0"}, insecure=True))


__all__ = [
    "AadrAnnoFile",
    "AadrReleaseResolution",
    "dataset_directory_name",
    "extract_anno_files_from_release",
    "fetch_release_history_metadata",
    "iter_release_versions",
    "resolve_aadr_release",
    "resolve_anno_files",
    "validate_anno_files",
]
