"""Authenticate publisher TSVs whose retained receipt has no HTTP capture."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re

from .contracts import ReportRebuildError, require_relative_path
from .qualified_sources import (
    QualifiedReportSources,
    _checked_file,
    _file_spec,
    _object,
    _regular_path,
)

SCHEMA = "qualified-publisher-report-tables.v1"
FIELDS = frozenset(
    {
        "schema_version",
        "source_id",
        "source",
        "parent_doi",
        "license",
        "rights",
        "retrieved_utc",
        "custody",
        "files",
    }
)
TABLE_FIELDS = frozenset({"path", "sha256", "size", "doi", "url", "columns"})
RECEIPT_FIELDS = frozenset({"source", "rights", "retrieved_utc", "files"})
RECEIPT_FILE_FIELDS = frozenset({"sha256", "bytes", "url"})
DOI = re.compile(r"10\.1594/PANGAEA\.\d+\Z")
RETRIEVED = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC\Z")
LICENSE_LINE = (
    "License:\tCreative Commons Attribution 4.0 International (CC-BY-4.0) "
    "(URI: https://creativecommons.org/licenses/by/4.0/)"
)


def _table_header(
    payload: bytes, doi: str, parent_doi: str, columns: list[str]
) -> None:
    """Check publisher identity and declared columns without parsing study rows."""
    if (
        not payload.startswith(b"/* DATA DESCRIPTION:\n")
        or b"*/\n" not in payload[:8192]
    ):
        raise ReportRebuildError("publisher table header delimiter differs")
    head, rows = payload.split(b"*/\n", 1)
    try:
        lines = head.decode("utf-8").splitlines()
        actual_columns = rows.split(b"\n", 1)[0].decode("utf-8").split("\t")
    except UnicodeError as error:
        raise ReportRebuildError("publisher table header is not UTF-8") from error
    citations = [line for line in lines if line.startswith("Citation:\t")]
    if len(citations) != 1 or f"https://doi.org/{doi}" not in citations[0]:
        raise ReportRebuildError("publisher table citation DOI differs")
    if sum(f"https://doi.org/{parent_doi}" in line for line in lines) != 1:
        raise ReportRebuildError("publisher table parent DOI differs")
    if lines.count(LICENSE_LINE) != 1:
        raise ReportRebuildError("publisher table primary license differs")
    if actual_columns != columns:
        raise ReportRebuildError("publisher table primary columns differ")


def validated_publisher_report_tables(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Bind a reviewed publisher receipt and its two consumed TSVs by bytes."""
    repository = repository.resolve(strict=True)
    relative = require_relative_path(descriptor_path.as_posix(), "source descriptor")
    if relative.startswith("external/"):
        raise ReportRebuildError("source descriptor overlaps external input namespace")
    descriptor_file = _regular_path(repository / relative)
    descriptor_payload = descriptor_file.read_bytes()
    descriptor = _object(descriptor_payload)
    if frozenset(descriptor) != FIELDS or descriptor["schema_version"] != SCHEMA:
        raise ReportRebuildError("publisher source descriptor schema or fields differ")
    source_id = require_relative_path(descriptor["source_id"], "publisher source ID")
    parent_doi = descriptor["parent_doi"]
    if not isinstance(parent_doi, str) or DOI.fullmatch(parent_doi) is None:
        raise ReportRebuildError("publisher parent DOI is invalid")
    if (
        not isinstance(descriptor["source"], str)
        or not isinstance(descriptor["rights"], str)
        or parent_doi.rsplit(".", 1)[-1] not in descriptor["source"]
        or descriptor["license"] != "CC-BY-4.0"
        or "CC BY 4.0" not in descriptor["rights"]
        or not isinstance(descriptor["retrieved_utc"], str)
        or RETRIEVED.fullmatch(descriptor["retrieved_utc"]) is None
    ):
        raise ReportRebuildError("publisher source identity or rights differ")
    root = _regular_path(source_root, directory=True)
    if root.is_relative_to(repository) or repository.is_relative_to(root):
        raise ReportRebuildError(
            "publisher source store must be separate from repository"
        )
    directory = _regular_path(root / source_id, directory=True)
    custody = _file_spec(descriptor["custody"])
    if custody["size"] > 8 * 1024 * 1024:
        raise ReportRebuildError("publisher receipt exceeds size limit")
    receipt_file = _checked_file(directory, custody)
    receipt_payload = receipt_file.read_bytes()
    if (
        len(receipt_payload) != custody["size"]
        or hashlib.sha256(receipt_payload).hexdigest() != custody["sha256"]
    ):
        raise ReportRebuildError("publisher receipt changed before parsing")
    receipt = _object(receipt_payload)
    if frozenset(receipt) != RECEIPT_FIELDS or any(
        receipt[name] != descriptor[name]
        for name in ("source", "rights", "retrieved_utc")
    ):
        raise ReportRebuildError("publisher receipt identity or fields differ")
    files = descriptor["files"]
    if not isinstance(files, list) or len(files) != 2:
        raise ReportRebuildError("publisher table pair differs")
    names: list[str] = []
    inputs = {
        relative: descriptor_file,
        f"external/{source_id}/{custody['path']}": receipt_file,
    }
    receipt_files = receipt["files"]
    if not isinstance(receipt_files, dict):
        raise ReportRebuildError("publisher receipt files are invalid")
    for table in files:
        if not isinstance(table, dict) or frozenset(table) != TABLE_FIELDS:
            raise ReportRebuildError("publisher table specification differs")
        spec = _file_spec({key: table[key] for key in ("path", "sha256", "size")})
        name = spec["path"]
        doi = table["doi"]
        url = table["url"]
        columns = table["columns"]
        if (
            not isinstance(doi, str)
            or DOI.fullmatch(doi) is None
            or name != f"PANGAEA.{doi.rsplit('.', 1)[-1]}.tab"
            or url != f"https://doi.pangaea.de/{doi}?format=textfile"
            or not isinstance(columns, list)
            or not columns
            or any(not isinstance(column, str) or not column for column in columns)
            or len(columns) != len(set(columns))
        ):
            raise ReportRebuildError("publisher table DOI, URL, or columns differ")
        row = receipt_files.get(name)
        if (
            not isinstance(row, dict)
            or frozenset(row) != RECEIPT_FILE_FIELDS
            or row != {"sha256": spec["sha256"], "bytes": spec["size"], "url": url}
        ):
            raise ReportRebuildError("publisher receipt table identity differs")
        source = _checked_file(directory, spec)
        payload = source.read_bytes()
        if (
            len(payload) != spec["size"]
            or hashlib.sha256(payload).hexdigest() != spec["sha256"]
        ):
            raise ReportRebuildError("publisher table changed before header check")
        _table_header(payload, doi, parent_doi, columns)
        inputs[f"external/{source_id}/{name}"] = source
        names.append(name)
    if (
        names != sorted(set(names))
        or set(receipt_files) != set(names)
        or custody["path"] in names
    ):
        raise ReportRebuildError("publisher table path set differs")
    if descriptor_file.read_bytes() != descriptor_payload:
        raise ReportRebuildError("publisher descriptor changed during validation")
    return QualifiedReportSources(
        directory, inputs, hashlib.sha256(descriptor_payload).hexdigest()
    )
