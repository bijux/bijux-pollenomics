"""Governed pig-panel inputs shared by focused tests."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.projects.sample_master.tables.workbook import (
    _read_xlsx_rows,
)
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_text
from tests.support.repository import REPOSITORY_ROOT

DATA_ROOT = REPOSITORY_ROOT / "data"
WORKBOOK_SOURCE_PATH = (
    "data/adna/governance/source_library/papers/10.1073-pnas.1901169116/"
    "supplementary/pnas.1901169116.sd01.xlsx"
)
ARCHIVE_SOURCE_PATH = (
    "data/adna/governance/source_library/projects/PRJEB30282/archive_metadata.html"
)


def governed_inputs() -> tuple[tuple[tuple[str, ...], ...], str]:
    """Read the governed workbook and logical archive capture."""
    workbook = REPOSITORY_ROOT / WORKBOOK_SOURCE_PATH
    archive = REPOSITORY_ROOT / ARCHIVE_SOURCE_PATH
    return (
        _read_xlsx_rows(Path(workbook), sheet_name="Sheet1"),
        read_source_artifact_text(Path(archive)),
    )
