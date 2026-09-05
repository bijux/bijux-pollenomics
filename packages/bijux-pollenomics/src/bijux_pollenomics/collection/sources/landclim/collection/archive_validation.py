"""Archive-summary validation for LandClim raw receipts."""

from __future__ import annotations

from pathlib import Path

from .archive_identity import build_landclim_archive_receipt
from .authority import LANDCLIM_ARCHIVE_FILENAME
from .model import LandClimRawReceiptError
from .receipt_structure import object_rows, safe_receipt_filename


def validate_archive_identities(
    receipt: dict[str, object],
    declared_names: set[str],
    actual_entries: dict[str, Path],
) -> None:
    archive_rows = object_rows(
        receipt.get("archive_summaries"), field_name="archive_summaries"
    )
    expected_archive_names = (
        {LANDCLIM_ARCHIVE_FILENAME}
        if LANDCLIM_ARCHIVE_FILENAME in declared_names
        else set()
    )
    archive_by_filename = {
        safe_receipt_filename(row.get("filename")): row for row in archive_rows
    }
    if len(archive_by_filename) != len(archive_rows):
        raise LandClimRawReceiptError("Duplicate LandClim archive summary")
    if set(archive_by_filename) != expected_archive_names:
        raise LandClimRawReceiptError("LandClim archive summary inventory is invalid")
    for filename, expected_summary in archive_by_filename.items():
        actual_summary = build_landclim_archive_receipt(actual_entries[filename])
        if expected_summary != actual_summary:
            raise LandClimRawReceiptError(
                f"LandClim archive member summary mismatch for {filename}"
            )
