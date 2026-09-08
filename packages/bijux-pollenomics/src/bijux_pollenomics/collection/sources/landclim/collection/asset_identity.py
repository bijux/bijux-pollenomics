"""Filesystem inventory and byte identity checks for LandClim raw assets."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..catalog import LANDCLIM_DATASET_METADATA
from .authority import (
    LANDCLIM_ASSET_DATASET_IDS,
    LANDCLIM_ASSET_SOURCE_URLS,
    LANDCLIM_REQUIRED_ASSETS,
)
from .model import LandClimRawReceiptError


def validate_governed_inventory(
    declared_names: set[str], actual_entries: dict[str, Path]
) -> None:
    missing_required = sorted(LANDCLIM_REQUIRED_ASSETS - declared_names)
    unknown_declared = sorted(declared_names - set(LANDCLIM_ASSET_DATASET_IDS))
    if missing_required or unknown_declared:
        raise LandClimRawReceiptError(
            "LandClim governed asset set is invalid; "
            f"missing_required={missing_required}; unknown={unknown_declared}"
        )
    actual_names = set(actual_entries)
    if declared_names != actual_names:
        missing = sorted(declared_names - actual_names)
        unlisted = sorted(actual_names - declared_names)
        raise LandClimRawReceiptError(
            f"LandClim raw asset inventory mismatch; missing={missing}; unlisted={unlisted}"
        )


def validate_asset_identities(
    asset_by_filename: dict[str, dict[str, object]],
    actual_entries: dict[str, Path],
    dataset_by_file: dict[str, str],
) -> None:
    for filename in sorted(asset_by_filename):
        _validate_asset_identity(
            filename,
            asset_by_filename[filename],
            actual_entries[filename],
            dataset_by_file,
        )


def _validate_asset_identity(
    filename: str,
    asset: dict[str, object],
    path: Path,
    dataset_by_file: dict[str, str],
) -> None:
    if not path.is_file() or path.is_symlink():
        raise LandClimRawReceiptError(
            f"LandClim raw asset is missing or unsafe: {filename}"
        )
    expected_dataset_id = LANDCLIM_ASSET_DATASET_IDS.get(filename)
    if expected_dataset_id is None:
        raise LandClimRawReceiptError(
            f"LandClim raw receipt contains an unknown asset: {filename}"
        )
    _validate_source_association(filename, asset, expected_dataset_id, dataset_by_file)
    _validate_byte_identity(filename, asset, path.read_bytes())


def _validate_source_association(
    filename: str,
    asset: dict[str, object],
    expected_dataset_id: str,
    dataset_by_file: dict[str, str],
) -> None:
    expected_doi = LANDCLIM_DATASET_METADATA[expected_dataset_id]["doi"]
    if (
        asset.get("dataset_id") != expected_dataset_id
        or dataset_by_file.get(filename) != expected_dataset_id
        or asset.get("dataset_doi") != expected_doi
    ):
        raise LandClimRawReceiptError(
            f"LandClim dataset/DOI association is invalid for {filename}"
        )
    if asset.get("source_url") != LANDCLIM_ASSET_SOURCE_URLS[filename]:
        raise LandClimRawReceiptError(f"LandClim source URL is invalid for {filename}")


def _validate_byte_identity(
    filename: str, asset: dict[str, object], payload: bytes
) -> None:
    size_bytes = asset.get("size_bytes")
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool):
        raise LandClimRawReceiptError(
            f"LandClim raw asset size is invalid for {filename}"
        )
    if size_bytes != len(payload):
        raise LandClimRawReceiptError(
            f"LandClim raw asset size mismatch for {filename}"
        )
    if asset.get("sha256") != hashlib.sha256(payload).hexdigest():
        raise LandClimRawReceiptError(
            f"LandClim raw asset digest mismatch for {filename}"
        )
