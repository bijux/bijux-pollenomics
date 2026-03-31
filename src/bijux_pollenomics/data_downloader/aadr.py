from __future__ import annotations

from pathlib import Path

from ..core.files import write_json
from ..core.http import fetch_binary, fetch_text
from .sources import aadr as _aadr

AADR_DATAVERSE_PERSISTENT_ID = _aadr.AADR_DATAVERSE_PERSISTENT_ID
AADR_DATAVERSE_API_URL = _aadr.AADR_DATAVERSE_API_URL
AADR_DATAVERSE_VERSIONS_URL = _aadr.AADR_DATAVERSE_VERSIONS_URL
AADR_DOWNLOAD_URL_TEMPLATE = _aadr.AADR_DOWNLOAD_URL_TEMPLATE
REQUEST_HEADERS = _aadr.REQUEST_HEADERS

AadrAnnoFile = _aadr.AadrAnnoFile
AadrReleaseResolution = _aadr.AadrReleaseResolution
AadrAnnoDownloadReport = _aadr.AadrAnnoDownloadReport

dataset_directory_name = _aadr.dataset_directory_name
extract_anno_files_from_release = _aadr.extract_anno_files_from_release
iter_release_versions = _aadr.iter_release_versions
resolve_aadr_release = _aadr.resolve_aadr_release
resolve_anno_files = _aadr.resolve_anno_files
validate_anno_files = _aadr.validate_anno_files
validate_downloaded_anno_payload = _aadr.validate_downloaded_anno_payload


def fetch_release_history_metadata() -> dict[str, object]:
    """Fetch the Dataverse release history for the public AADR dataset."""
    return _aadr.fetch_release_history_metadata(fetch_text_fn=fetch_text)


def write_release_manifest(
    path: Path,
    *,
    version: str,
    resolution: AadrReleaseResolution,
    downloaded_files: list[Path],
) -> None:
    """Persist the upstream Dataverse release metadata for one downloaded AADR version."""
    _aadr.write_release_manifest(
        path,
        version=version,
        resolution=resolution,
        downloaded_files=downloaded_files,
        write_json_fn=write_json,
    )


def download_aadr_anno_files(output_root: Path, version: str) -> AadrAnnoDownloadReport:
    """Download the public AADR .anno files for one release version."""
    return _aadr.download_aadr_anno_files(
        output_root,
        version,
        fetch_binary_fn=fetch_binary,
        fetch_release_history_metadata_fn=fetch_release_history_metadata,
        write_json_fn=write_json,
    )


__all__ = [
    "AADR_DATAVERSE_API_URL",
    "AADR_DATAVERSE_PERSISTENT_ID",
    "AADR_DATAVERSE_VERSIONS_URL",
    "AADR_DOWNLOAD_URL_TEMPLATE",
    "AadrAnnoDownloadReport",
    "AadrAnnoFile",
    "AadrReleaseResolution",
    "REQUEST_HEADERS",
    "dataset_directory_name",
    "download_aadr_anno_files",
    "extract_anno_files_from_release",
    "fetch_release_history_metadata",
    "iter_release_versions",
    "resolve_aadr_release",
    "resolve_anno_files",
    "validate_anno_files",
    "validate_downloaded_anno_payload",
    "write_release_manifest",
]
