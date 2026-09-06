from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path

from .primitives import _positive_int, _regular_non_symlink, _safe_relative_path


def _valid_landclim_receipt(path: Path, payload: Mapping[str, object]) -> bool:
    assets = payload.get("assets")
    if (
        payload.get("schema_version") != "landclim-raw-receipt.v1"
        or payload.get("source") != "LandClim"
        or not isinstance(assets, list)
        or payload.get("asset_count") != len(assets)
        or not assets
    ):
        return False
    try:
        return all(
            isinstance(record, dict)
            and isinstance(record.get("filename"), str)
            and _safe_relative_path(record["filename"])
            and _regular_non_symlink(asset_path := path.parent / record["filename"])
            and record.get("size_bytes") == asset_path.stat().st_size
            and record.get("sha256")
            == hashlib.sha256(asset_path.read_bytes()).hexdigest()
            for record in assets
        )
    except OSError:
        return False


def _valid_boundary_receipt(path: Path, payload: Mapping[str, object]) -> bool:
    artifacts = payload.get("country_artifacts")
    normalized = payload.get("normalized_artifact")
    if (
        payload.get("schema_version") != "natural-earth-boundary-receipt.v1"
        or payload.get("source") != "Natural Earth"
        or not isinstance(artifacts, dict)
        or set(artifacts) != {"Sweden", "Denmark", "Norway", "Finland"}
        or not isinstance(normalized, dict)
    ):
        return False
    try:
        countries_valid = all(
            isinstance(record, dict)
            and isinstance(record.get("path"), str)
            and _safe_relative_path(record["path"])
            and _regular_non_symlink(artifact_path := path.parent / record["path"])
            and record.get("sha256")
            == hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            and _positive_int(record.get("feature_count")) is not None
            for record in artifacts.values()
        )
        normalized_relative = normalized.get("path")
        if not isinstance(normalized_relative, str) or not _safe_relative_path(
            normalized_relative
        ):
            return False
        normalized_path = path.parent.parent / normalized_relative
        return (
            countries_valid
            and _regular_non_symlink(normalized_path)
            and normalized.get("sha256")
            == hashlib.sha256(normalized_path.read_bytes()).hexdigest()
            and _positive_int(normalized.get("feature_count")) is not None
        )
    except OSError:
        return False


def _valid_aadr_receipt(path: Path, payload: Mapping[str, object]) -> bool:
    files = payload.get("downloaded_files")
    records = payload.get("anno_files")
    if (
        payload.get("source") != "AADR"
        or not isinstance(files, list)
        or not isinstance(records, list)
        or not files
        or len(files) != len(records)
    ):
        return False
    relative_paths = [item for item in files if isinstance(item, str)]
    record_names = [
        record.get("filename") for record in records if isinstance(record, dict)
    ]
    if (
        len(relative_paths) != len(files)
        or len(relative_paths) != len(set(relative_paths))
        or len(record_names) != len(records)
        or len(record_names) != len(set(record_names))
        or any(not _safe_relative_path(item) for item in relative_paths)
        or {Path(item).name for item in relative_paths} != set(record_names)
    ):
        return False
    record_by_name = {
        str(record["filename"]): record
        for record in records
        if isinstance(record, dict)
    }
    try:
        return all(
            _regular_non_symlink(artifact_path := path.parent / relative_path)
            and (record := record_by_name.get(artifact_path.name)) is not None
            and record.get("filesize") == artifact_path.stat().st_size
            and record.get("md5")
            == hashlib.md5(
                artifact_path.read_bytes(), usedforsecurity=False
            ).hexdigest()
            for relative_path in relative_paths
        )
    except OSError:
        return False
