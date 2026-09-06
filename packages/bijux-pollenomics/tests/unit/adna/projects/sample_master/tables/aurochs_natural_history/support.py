"""Governed PRJEB75467 inputs shared by aurochs reconciliation tests."""

from __future__ import annotations

from hashlib import sha256

from tests.support.repository import REPOSITORY_ROOT

from bijux_pollenomics.adna.projects.sample_master.tables.workbook import (
    _read_xlsx_rows,
)
from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_bytes,
    read_source_artifact_text,
)


DATA_ROOT = REPOSITORY_ROOT / "data"
WORKBOOK_PATH = (
    DATA_ROOT / "adna/governance/source_library/papers/10.1038-s41586-024-08112-6/"
    "supplementary/41586_2024_8112_MOESM3_ESM.xlsx"
)
ARCHIVE_PATH = (
    DATA_ROOT
    / "adna/governance/source_library/projects/PRJEB75467/archive_metadata.html"
)


def governed_inputs() -> tuple[tuple[tuple[str, ...], ...], str, str]:
    """Return the workbook rows/digest and decompressed archive text."""
    workbook_payload = read_source_artifact_bytes(WORKBOOK_PATH)
    return (
        _read_xlsx_rows(WORKBOOK_PATH, sheet_name="Supplementary Data 1"),
        sha256(workbook_payload).hexdigest(),
        read_source_artifact_text(ARCHIVE_PATH),
    )
