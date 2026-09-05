"""Validation workflow for governed LandClim raw receipts."""

from __future__ import annotations

from pathlib import Path

from ..archive_validation import validate_archive_identities
from ..asset_identity import validate_asset_identities, validate_governed_inventory
from ..dataset_authority import validate_landclim_receipt_datasets
from ..model import LandClimRawReceiptError
from .structure import (
    index_declared_assets,
    load_raw_receipt,
    object_rows,
    safe_receipt_filename,
)


def validate_landclim_raw_receipt(raw_dir: Path) -> dict[str, object]:
    """Validate exact LandClim raw bytes and their governed source associations."""
    raw_dir = Path(raw_dir)
    receipt = load_raw_receipt(raw_dir)
    assets = object_rows(receipt.get("assets"), field_name="assets")
    asset_count = receipt.get("asset_count")
    if not isinstance(asset_count, int) or isinstance(asset_count, bool):
        raise LandClimRawReceiptError("LandClim raw receipt asset_count is invalid")
    if asset_count != len(assets):
        raise LandClimRawReceiptError("LandClim raw receipt asset_count is invalid")
    asset_by_filename = index_declared_assets(assets)
    receipt_path = raw_dir / "landclim_sources.json"
    actual_entries = {
        path.name: path for path in raw_dir.iterdir() if path.name != receipt_path.name
    }
    declared_names = set(asset_by_filename)
    validate_governed_inventory(declared_names, actual_entries)
    dataset_by_file = validate_landclim_receipt_datasets(receipt, declared_names)
    validate_asset_identities(asset_by_filename, actual_entries, dataset_by_file)
    validate_archive_identities(receipt, declared_names, actual_entries)
    return receipt


__all__ = [
    "object_rows",
    "safe_receipt_filename",
    "validate_landclim_raw_receipt",
    "validate_landclim_receipt_datasets",
]
