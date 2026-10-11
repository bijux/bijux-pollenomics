"""Extract source-verified tables from archived supplementary bundles."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from bijux_pollenomics.adna.workflow.paths import adna_source_library_root
from bijux_pollenomics.adna.workflow.source_artifacts import write_source_artifact_bytes
from bijux_pollenomics.core.files import write_json

from ..models import SOURCE_LIBRARY_SCHEMA_VERSION

_REINDEER_ARCHIVE = "mec17274-sup-0001-Appendix S1.zip"
_REINDEER_ARCHIVE_SHA256 = (
    "179ce63b79122e62017c8df8433379929f8c160f399ff44969ef05917ad734c9"
)
_REINDEER_TABLE = "mec17274-sup-0003-Table S3.xlsx"
_REINDEER_TABLE_SHA256 = (
    "81cc00377f5898004b8f4f724c0aa1b787fdb30d7df9874b31f1a27241268462"
)


def materialize_reindeer_published_table(output_root: Path) -> None:
    """Retain the exact published-table member and its parent archive identity."""
    source_dir = (
        adna_source_library_root(Path(output_root))
        / "papers/10.1111-mec.17274/supplementary"
    )
    archive_path = source_dir / _REINDEER_ARCHIVE
    if not archive_path.is_file():
        return
    archive_bytes = archive_path.read_bytes()
    if sha256(archive_bytes).hexdigest() != _REINDEER_ARCHIVE_SHA256:
        raise ValueError("Reindeer published Appendix S1 archive changed")
    with ZipFile(archive_path) as archive:
        table_bytes = archive.read(_REINDEER_TABLE)
    if sha256(table_bytes).hexdigest() != _REINDEER_TABLE_SHA256:
        raise ValueError("Reindeer published Appendix S1 Table S3 changed")
    table_path = source_dir / _REINDEER_TABLE
    write_source_artifact_bytes(table_path, table_bytes)
    write_json(
        table_path.with_suffix(table_path.suffix + ".metadata.json"),
        {
            "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
            "artifact_kind": "supplementary_spreadsheet_member",
            "paper_doi": "10.1111/mec.17274",
            "project_accessions": ["PRJEB60484"],
            "source_archive": str(archive_path.relative_to(output_root)),
            "source_archive_sha256": _REINDEER_ARCHIVE_SHA256,
            "archive_member": _REINDEER_TABLE,
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "byte_size": len(table_bytes),
            "content_sha256": _REINDEER_TABLE_SHA256,
            "publisher_byte_parity": "unverified_publisher_download_http_403",
        },
    )
