from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .common import fetch_binary, fetch_text


AADR_DATAVERSE_PERSISTENT_ID = "doi:10.7910/DVN/FFIDCW"
AADR_DATAVERSE_API_URL = (
    "https://dataverse.harvard.edu/api/datasets/:persistentId/"
    "?persistentId=doi:10.7910/DVN/FFIDCW"
)
AADR_DATAVERSE_VERSIONS_URL = (
    "https://dataverse.harvard.edu/api/datasets/:persistentId/versions"
    "?persistentId=doi:10.7910/DVN/FFIDCW"
)
AADR_DOWNLOAD_URL_TEMPLATE = "https://dataverse.harvard.edu/api/access/datafile/{file_id}"
REQUEST_HEADERS = {"User-Agent": "bijux-pollenomics/1.0"}


@dataclass(frozen=True)
class AadrAnnoFile:
    filename: str
    file_id: int
    dataset_name: str


@dataclass(frozen=True)
class AadrAnnoDownloadReport:
    version: str
    version_dir: Path
    downloaded_files: tuple[Path, ...]


def download_aadr_anno_files(output_root: Path, version: str) -> AadrAnnoDownloadReport:
    """Download the public AADR .anno files for one release version."""
    output_root = Path(output_root)
    version_dir = output_root / version
    version_dir.mkdir(parents=True, exist_ok=True)

    anno_files = resolve_anno_files(version=version, metadata=fetch_release_history_metadata())
    downloaded_files: list[Path] = []
    for anno_file in anno_files:
        dataset_dir = version_dir / anno_file.dataset_name
        dataset_dir.mkdir(parents=True, exist_ok=True)
        destination = dataset_dir / anno_file.filename
        destination.write_bytes(
            fetch_binary(
                AADR_DOWNLOAD_URL_TEMPLATE.format(file_id=anno_file.file_id),
                headers=REQUEST_HEADERS,
            )
        )
        downloaded_files.append(destination)

    return AadrAnnoDownloadReport(
        version=version,
        version_dir=version_dir,
        downloaded_files=tuple(downloaded_files),
    )


def resolve_anno_files(version: str, metadata: dict[str, object]) -> tuple[AadrAnnoFile, ...]:
    """Extract one release's public .anno files from the Dataverse version history."""
    version_prefix = f"{version}_"
    for dataset_version in iter_release_versions(metadata):
        matched_files = extract_anno_files_from_release(dataset_version, version_prefix=version_prefix)
        if matched_files:
            return tuple(sorted(matched_files, key=lambda item: item.dataset_name))
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
            )
        )
    return matched_files


def dataset_directory_name(filename: str) -> str:
    """Map a public AADR anno filename to its stable local dataset directory."""
    lowered = filename.casefold()
    if "_1240k_" in lowered:
        return "1240k"
    if "_ho_" in lowered:
        return "ho"
    stem = filename.removesuffix(".anno")
    return stem.split("_", 1)[-1].replace("_public", "").casefold()


def fetch_release_history_metadata() -> dict[str, object]:
    """Fetch the Dataverse release history for the public AADR dataset."""
    return json.loads(fetch_text(AADR_DATAVERSE_VERSIONS_URL, headers={"User-Agent": "Mozilla/5.0"}, insecure=True))
