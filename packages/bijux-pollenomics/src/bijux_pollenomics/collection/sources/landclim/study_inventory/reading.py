"""Read the exact LandClim II full-study metadata declaration."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
from pathlib import Path

from ....intake.workbooks import read_xlsx_sheet_rows
from ..catalog import LANDCLIM_DATASET_METADATA
from ..collection.receipt.validation import validate_landclim_raw_receipt
from .contracts import (
    LandClimStudyInventoryRefusal,
    LandClimStudyMetadataInventory,
    StudyMetadataRecord,
    StudyMetadataValue,
    _mint_inventory,
)

_WORKBOOK = "landclim_ii_site_metadata.xlsx"
_RECEIPT = "landclim_sources.json"
_SHEET = "LANDCLIMII metadata file"
_RECORD_COUNT = 1128
_DATASET_DOI = "https://doi.org/10.1594/PANGAEA.937075"
_RECEIPT_SHA256 = "eb4350724c176d0dbcb7e441f2d21489bdae1cfff7ebe3088eab27093f315677"
_WORKBOOK_SHA256 = "2d4a0cf1401e36c2606f7761cecc85c4bbc15272460c2a4926cb1702d4565ebb"
_HEADER = (
    "SiteName",
    "csvfilename",
    "siteType",
    "siteradius",
    "londd",
    "latdd",
    "Elevation",
    "LCGRID_ID",
    "Country",
    "Database/Authorname and/or data collector",
    "DataRestricted/NotRestriced",
    "nPollenSamples",
    "nTWs",
    "TopBP",
    "BotBP",
    "No. of 14C dates for model",
    "chronologySource",
    "ChronologyNotes",
    "0-100",
    "100-350",
    "350-700",
    "700-1200",
    "1200-1700",
    "1700-2200",
    "2200-2700",
    "2700-3200",
    "3200-3700",
    "3700-4200",
    "4200-4700",
    "4700-5200",
    "5200-5700",
    "5700-6200",
    "6200-6700",
    "6700-7200",
    "7200-7700",
    "7700-8200",
    "8200-8700",
    "8700-9200",
    "9200-9700",
    "9700-10200",
    "10200-10700",
    "10700-11200",
    "11200-11700",
    "LandClimProject",
)
_NUMERIC_COLUMNS = frozenset(
    {
        "siteradius",
        "londd",
        "latdd",
        "Elevation",
        "LCGRID_ID",
        "nPollenSamples",
        "nTWs",
        "TopBP",
        "BotBP",
    }
)


def read_landclim_study_inventory(raw_dir: Path) -> LandClimStudyMetadataInventory:
    """Authenticate and retain the pinned 1,128-row publication metadata sheet."""
    return _read_landclim_study_inventory(
        raw_dir,
        expected_receipt_sha256=_RECEIPT_SHA256,
        expected_workbook_sha256=_WORKBOOK_SHA256,
    )


def reopen_landclim_study_inventory(
    canonical_bytes: bytes, raw_dir: Path
) -> LandClimStudyMetadataInventory:
    """Reconstruct an inventory and require an exact canonical-byte match."""
    if type(canonical_bytes) is not bytes:
        raise LandClimStudyInventoryRefusal(
            "LandClim study inventory canonical payload must be exact bytes"
        )
    product = read_landclim_study_inventory(raw_dir)
    if product.canonical_bytes != canonical_bytes:
        raise LandClimStudyInventoryRefusal(
            "LandClim study inventory canonical payload does not match raw inputs"
        )
    return product


def _read_landclim_study_inventory(
    raw_dir: Path,
    *,
    expected_receipt_sha256: str,
    expected_workbook_sha256: str,
) -> LandClimStudyMetadataInventory:
    raw_dir = Path(raw_dir)
    receipt_path = raw_dir / _RECEIPT
    workbook_path = raw_dir / _WORKBOOK
    before_receipt = _pinned_digest(receipt_path, expected_receipt_sha256, "receipt")
    before_workbook = _pinned_digest(
        workbook_path, expected_workbook_sha256, "workbook"
    )
    validate_landclim_raw_receipt(raw_dir)
    rows = read_xlsx_sheet_rows(workbook_path, _SHEET)
    if _pinned_digest(receipt_path, before_receipt, "receipt") != before_receipt:
        raise LandClimStudyInventoryRefusal("LandClim receipt changed while reading")
    if _pinned_digest(workbook_path, before_workbook, "workbook") != before_workbook:
        raise LandClimStudyInventoryRefusal("LandClim workbook changed while reading")
    return _inventory_from_rows(
        rows,
        receipt_sha256=before_receipt,
        workbook_sha256=before_workbook,
    )


def _inventory_from_rows(
    rows: list[list[str]],
    *,
    receipt_sha256: str,
    workbook_sha256: str,
) -> LandClimStudyMetadataInventory:
    if not rows or tuple(rows[0]) != _HEADER:
        raise LandClimStudyInventoryRefusal(
            "LandClim study metadata header does not match the pinned declaration"
        )
    source_rows = rows[1:]
    if len(source_rows) != _RECORD_COUNT:
        raise LandClimStudyInventoryRefusal(
            "LandClim study metadata must contain exactly 1,128 records"
        )
    records = tuple(
        _record(row, worksheet_row=index)
        for index, row in enumerate(source_rows, start=2)
    )
    return _mint_inventory(
        receipt_sha256=_digest(receipt_sha256, "receipt"),
        workbook_sha256=_digest(workbook_sha256, "workbook"),
        dataset_doi=_dataset_doi(),
        sheet_name=_SHEET,
        header=_HEADER,
        records=records,
    )


def _record(row: list[str], *, worksheet_row: int) -> StudyMetadataRecord:
    if len(row) != len(_HEADER) or not all(type(value) is str for value in row):
        raise LandClimStudyInventoryRefusal(
            f"LandClim study metadata row {worksheet_row} has an invalid shape"
        )
    values = tuple(
        _value(column, raw, worksheet_row=worksheet_row)
        for column, raw in zip(_HEADER, row, strict=True)
    )
    by_column = {value.column: value for value in values}
    if by_column["SiteName"].kind == "null":
        raise LandClimStudyInventoryRefusal(
            f"LandClim study metadata row {worksheet_row} has no site label"
        )
    longitude = by_column["londd"].number
    latitude = by_column["latdd"].number
    if longitude is None or not Decimal("-180") <= longitude <= Decimal("180"):
        raise LandClimStudyInventoryRefusal(
            f"LandClim study metadata row {worksheet_row} has invalid longitude"
        )
    if latitude is None or not Decimal("-90") <= latitude <= Decimal("90"):
        raise LandClimStudyInventoryRefusal(
            f"LandClim study metadata row {worksheet_row} has invalid latitude"
        )
    return StudyMetadataRecord(
        worksheet_row=worksheet_row,
        source_locator=f"{_WORKBOOK}#{_SHEET}!{worksheet_row}",
        values=values,
    )


def _value(column: str, raw: str, *, worksheet_row: int) -> StudyMetadataValue:
    if raw == "":
        return StudyMetadataValue(column=column, kind="null", raw=None, number=None)
    if column not in _NUMERIC_COLUMNS:
        return StudyMetadataValue(column=column, kind="text", raw=raw, number=None)
    try:
        number = Decimal(raw)
    except InvalidOperation as error:
        raise LandClimStudyInventoryRefusal(
            f"LandClim study metadata row {worksheet_row} has invalid {column}"
        ) from error
    if not number.is_finite():
        raise LandClimStudyInventoryRefusal(
            f"LandClim study metadata row {worksheet_row} has invalid {column}"
        )
    return StudyMetadataValue(column=column, kind="number", raw=raw, number=number)


def _pinned_digest(path: Path, expected: str, label: str) -> str:
    if not path.is_file() or path.is_symlink():
        raise LandClimStudyInventoryRefusal(
            f"LandClim study metadata {label} is missing or unsafe"
        )
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != _digest(expected, label):
        raise LandClimStudyInventoryRefusal(
            f"LandClim study metadata {label} digest does not match"
        )
    return actual


def _digest(value: str, label: str) -> str:
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise LandClimStudyInventoryRefusal(
            f"LandClim study metadata {label} digest is invalid"
        )
    return value


def _dataset_doi() -> str:
    value = LANDCLIM_DATASET_METADATA["937075"]["doi"]
    if type(value) is not str or value != _DATASET_DOI:
        raise LandClimStudyInventoryRefusal(
            "LandClim study metadata dataset authority is invalid"
        )
    return value
