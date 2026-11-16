from __future__ import annotations

from collections.abc import Callable, Mapping
import json
import re

from ....core.geospatial.geojson import as_mapping
from .constants import AADR_DATAVERSE_PERSISTENT_ID, AADR_DATAVERSE_VERSIONS_URL
from .models import AadrAnnoFile, AadrReleaseResolution

CANONICAL_AADR_DATASETS = frozenset({"1240k", "ho"})


def _literal_component(value: object, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or not value.isprintable()
    ):
        raise ValueError(f"AADR {field} must be a literal flat member")
    return value


def validate_release_version(version: str) -> str:
    """Validate a literal release directory before transport or output creation."""
    return _literal_component(version, field="release version")


def _native_file_id(value: object) -> int:
    if type(value) is int:
        file_id = value
    elif isinstance(value, str) and value.isascii() and value.isdecimal():
        try:
            file_id = int(value)
        except ValueError as error:
            raise ValueError(
                "AADR file id must be an exact positive integer"
            ) from error
    else:
        raise ValueError("AADR file id must be an exact positive integer")
    if file_id <= 0:
        raise ValueError("AADR file id must be an exact positive integer")
    return file_id


def resolve_anno_files(
    version: str, metadata: Mapping[str, object]
) -> tuple[AadrAnnoFile, ...]:
    """Extract one release's public .anno files from the Dataverse version history."""
    return resolve_aadr_release(version=version, metadata=metadata).anno_files


def resolve_aadr_release(
    version: str, metadata: Mapping[str, object]
) -> AadrReleaseResolution:
    """Resolve one requested AADR release from the Dataverse version history."""
    validate_release_version(version)
    for dataset_version in iter_release_versions(metadata):
        matched_files = extract_anno_files_from_release(
            dataset_version, version=version
        )
        if matched_files:
            return AadrReleaseResolution(
                version=version,
                dataset_version=dataset_version,
                anno_files=tuple(
                    validate_anno_files(
                        sorted(matched_files, key=lambda item: item.dataset_name)
                    )
                ),
            )
    raise ValueError(
        f"No public .anno files were found for {version} in {AADR_DATAVERSE_PERSISTENT_ID}"
    )


def iter_release_versions(metadata: Mapping[str, object]) -> list[dict[str, object]]:
    """Return Dataverse release versions in descending publication order."""
    versions = metadata.get("data", [])
    if not isinstance(versions, list):
        raise ValueError("Unexpected Dataverse metadata: missing version history")
    return [version for version in versions if isinstance(version, dict)]


def extract_anno_files_from_release(
    dataset_version: dict[str, object],
    *,
    version: str,
) -> list[AadrAnnoFile]:
    """Extract public `.anno` files, retaining missing/None sizes as unknown zero."""
    validate_release_version(version)
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
        if not is_requested_anno_filename(filename=filename, version=version):
            continue
        _literal_component(filename, field="source filename")
        dataset_name = dataset_directory_name(filename)
        if dataset_name not in CANONICAL_AADR_DATASETS:
            continue
        filesize = data_file.get("filesize")
        if filesize is None:
            filesize = 0
        if type(filesize) is not int or filesize < 0:
            raise ValueError("AADR filesize must be a nonnegative integer or unknown")
        matched_files.append(
            AadrAnnoFile(
                filename=filename,
                file_id=_native_file_id(data_file.get("id")),
                dataset_name=dataset_name,
                md5=str(data_file.get("md5", "")).strip(),
                filesize=filesize,
            )
        )
    return matched_files


def is_requested_anno_filename(*, filename: str, version: str) -> bool:
    """Return whether a filename is a canonical public .anno file for one version."""
    lowered = filename.casefold()
    version_prefix = version.casefold()
    if not lowered.endswith(".anno"):
        return False
    if "compatibility" in lowered:
        return False
    return lowered.startswith((f"{version_prefix}_", f"{version_prefix}."))


def validate_anno_files(files: list[AadrAnnoFile]) -> list[AadrAnnoFile]:
    """Validate resolved AADR `.anno` files before download."""
    seen_dataset_names: set[str] = set()
    seen_file_ids: set[int] = set()
    for file in files:
        _literal_component(file.filename, field="source filename")
        if type(file.file_id) is not int or file.file_id <= 0:
            raise ValueError(
                "Resolved AADR release includes an invalid public .anno entry"
            )
        if file.dataset_name in seen_dataset_names:
            raise ValueError(
                f"Resolved AADR release contains duplicate dataset coverage for {file.dataset_name}"
            )
        if file.dataset_name not in CANONICAL_AADR_DATASETS:
            raise ValueError("Resolved AADR release includes an unknown dataset panel")
        if file.file_id in seen_file_ids:
            raise ValueError("Resolved AADR release contains duplicate file identity")
        seen_dataset_names.add(file.dataset_name)
        seen_file_ids.add(file.file_id)
    return files


def dataset_directory_name(filename: str) -> str:
    """Map a public AADR anno filename to its stable local dataset directory."""
    tokens = [
        token
        for token in re.split(r"[._-]+", filename.removesuffix(".anno").casefold())
        if token
    ]
    if "1240k" in tokens:
        return "1240k"
    if "ho" in tokens:
        return "ho"
    stem = filename.removesuffix(".anno")
    return stem.split("_", 1)[-1].replace("_public", "").casefold()


def fetch_release_history_metadata(
    *,
    fetch_text_fn: Callable[..., str],
) -> dict[str, object]:
    """Fetch the Dataverse release history for the public AADR dataset."""
    payload = json.loads(
        fetch_text_fn(
            AADR_DATAVERSE_VERSIONS_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            insecure=False,
        )
    )
    mapping = as_mapping(payload)
    if mapping is None:
        raise ValueError(
            "Unexpected Dataverse metadata: root payload must be a JSON object"
        )
    return {str(key): value for key, value in mapping.items()}


__all__ = [
    "AadrAnnoFile",
    "AadrReleaseResolution",
    "dataset_directory_name",
    "extract_anno_files_from_release",
    "fetch_release_history_metadata",
    "is_requested_anno_filename",
    "iter_release_versions",
    "resolve_aadr_release",
    "resolve_anno_files",
    "validate_anno_files",
]
