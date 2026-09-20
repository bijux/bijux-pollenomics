"""Support for exact LandClim study-inventory tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from bijux_pollenomics.collection.intake.workbooks import read_xlsx_sheet_rows
from bijux_pollenomics.collection.sources.landclim.study_inventory import (
    StudyMetadataRecord,
    StudyMetadataValue,
)
from tests.support.repository import REPOSITORY_ROOT

RAW_ROOT = REPOSITORY_ROOT / "data" / "landclim" / "raw"
SHEET = "LANDCLIMII metadata file"


def rows() -> list[list[str]]:
    """Return a mutable copy of the exact governed workbook declaration."""
    source = read_xlsx_sheet_rows(RAW_ROOT / "landclim_ii_site_metadata.xlsx", SHEET)
    return deepcopy(source)


def cell(record: StudyMetadataRecord, column: str) -> StudyMetadataValue:
    """Return one typed cell from a study metadata record."""
    return next(value for value in record.values if value.column == column)


def source_path(filename: str) -> Path:
    """Return a governed raw input path."""
    return RAW_ROOT / filename
