"""Published reindeer sample metadata from the retained Appendix S1 bundle."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from bijux_pollenomics.adna.sources.library import ADNA_SOURCE_LIBRARY_DIR
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_bytes

from ..workbook import _read_xlsx_rows

PUBLISHED_TABLE_PATH = (
    f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1111-mec.17274/"
    "supplementary/mec17274-sup-0003-Table S3.xlsx"
)
_TABLE_SHA256 = "81cc00377f5898004b8f4f724c0aa1b787fdb30d7df9874b31f1a27241268462"
_EXPECTED_ANCIENT = {
    "B20",
    "BBH7",
    "FJL1a",
    "FJL3",
    "M44",
    "M46",
    "M68",
    "M72",
    "MB60",
    "MDV11",
    "MLM12",
    "MLM16",
    "MLM51",
    "MLM61",
    "MLM80",
    "MLM82",
    "R20",
    "R25a",
    "R29a",
    "R36",
}


def read_published_reindeer_table(
    output_root: Path,
) -> dict[str, tuple[int, tuple[str, ...]]]:
    """Return exact ancient specimen rows, preserving the source row numbers."""
    path = Path(output_root) / PUBLISHED_TABLE_PATH.removeprefix("data/")
    if not path.is_file():
        return {}
    payload = read_source_artifact_bytes(path)
    if sha256(payload).hexdigest() != _TABLE_SHA256:
        raise ValueError("Reindeer published Table S3 changed")
    receipt = json.loads(path.with_suffix(".xlsx.metadata.json").read_text())
    if (
        receipt.get("content_sha256") != _TABLE_SHA256
        or receipt.get("archive_member") != path.name
    ):
        raise ValueError("Reindeer published Table S3 receipt changed")
    rows = _read_xlsx_rows(path, sheet_name="Tabellenblatt1")
    populated = [
        (number, cells)
        for number, cells in enumerate(rows[2:], start=3)
        if cells and cells[0]
    ]
    if len(populated) != 110:
        raise ValueError("Reindeer published Table S3 population changed")
    ancient = {
        cells[0]: (number, cells)
        for number, cells in populated
        if len(cells) >= 15 and cells[7] == "ancient"
    }
    if (
        set(ancient) != _EXPECTED_ANCIENT
        or sum(cells[7] == "modern" for _, cells in populated) != 90
        or any(cells[14] != "PRJEB60484" for _, cells in ancient.values())
    ):
        raise ValueError("Reindeer published Table S3 ancient specimen set changed")
    return ancient
