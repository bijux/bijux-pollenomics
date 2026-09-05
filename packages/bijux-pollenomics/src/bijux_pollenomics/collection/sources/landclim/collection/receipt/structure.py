"""Structural parsing and safe names for LandClim raw receipts."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

from ..model import LandClimRawReceiptError


def load_raw_receipt(raw_dir: Path) -> dict[str, object]:
    if not raw_dir.is_dir() or raw_dir.is_symlink():
        raise LandClimRawReceiptError(
            "LandClim raw directory must be an existing non-symlink directory"
        )
    receipt_path = raw_dir / "landclim_sources.json"
    if not receipt_path.is_file() or receipt_path.is_symlink():
        raise LandClimRawReceiptError("LandClim raw receipt is missing or unsafe")
    try:
        loaded = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LandClimRawReceiptError("LandClim raw receipt is unreadable") from error
    if not isinstance(loaded, dict):
        raise LandClimRawReceiptError("LandClim raw receipt must be a JSON object")
    receipt: dict[str, object] = loaded
    if receipt.get("schema_version") != "landclim-raw-receipt.v1":
        raise LandClimRawReceiptError("Unsupported LandClim raw receipt schema")
    if receipt.get("source") != "LandClim":
        raise LandClimRawReceiptError("LandClim raw receipt source is invalid")
    return receipt


def index_declared_assets(
    assets: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    asset_by_filename: dict[str, dict[str, object]] = {}
    for asset in assets:
        filename = safe_receipt_filename(asset.get("filename"))
        if filename in asset_by_filename:
            raise LandClimRawReceiptError(
                f"Duplicate LandClim raw receipt asset: {filename}"
            )
        asset_by_filename[filename] = asset
    return asset_by_filename


def object_rows(value: object, *, field_name: str) -> list[dict[str, object]]:
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise LandClimRawReceiptError(
            f"LandClim raw receipt {field_name} must be a list of objects"
        )
    return value


def safe_receipt_filename(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise LandClimRawReceiptError("LandClim raw receipt filename is invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 1 or path.name != value:
        raise LandClimRawReceiptError(f"Unsafe LandClim raw receipt filename: {value}")
    return value
