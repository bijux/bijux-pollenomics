"""Bind the retained published EPD age table without inventing capture custody."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ..contracts import ReportRebuildError, require_relative_path
from ..qualified_sources import (
    QualifiedReportSources,
    _checked_file,
    _object,
    _regular_path,
)

SCHEMA = "qualified-pangaea-epd-age-table.v1"
SOURCE_ID = "epd/pangaea"
TABLE = "epd-age-cut-pangaea-804596.tsv"
TABLE_SHA256 = "d332d5c7921b914e84da689c918607befdb162f5c68bbcce9cd3534d1f5e58e0"
TABLE_SIZE = 3613957
DOI = "10.1594/PANGAEA.804596"
FIELDS = frozenset(
    {
        "schema_version",
        "source_id",
        "table",
        "doi",
        "license",
        "capture_custody",
        "scientific_admission",
    }
)


def validated_epd_age_table(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Authenticate one exact retained table; its acquisition history remains unestablished."""
    repository = _regular_path(repository, directory=True)
    relative = require_relative_path(descriptor_path.as_posix(), "source descriptor")
    if relative.startswith("external/"):
        raise ReportRebuildError("Published EPD descriptor overlaps external inputs")
    descriptor_file = _regular_path(repository / relative)
    payload = descriptor_file.read_bytes()
    descriptor = _object(payload)
    expected: dict[str, Any] = {
        "schema_version": SCHEMA,
        "source_id": SOURCE_ID,
        "table": {"path": TABLE, "sha256": TABLE_SHA256, "size": TABLE_SIZE},
        "doi": DOI,
        "license": "CC-BY-3.0",
        "capture_custody": "not_established",
        "scientific_admission": False,
    }
    if (
        frozenset(descriptor) != FIELDS
        or descriptor != expected
        or type(descriptor["table"].get("size")) is not int
        or descriptor["scientific_admission"] is not False
    ):
        raise ReportRebuildError(
            "Published EPD age table descriptor identity or limits differ"
        )
    root = _regular_path(source_root, directory=True)
    if root.is_relative_to(repository) or repository.is_relative_to(root):
        raise ReportRebuildError("Published EPD age table store must be external")
    directory = _regular_path(root / SOURCE_ID, directory=True)
    table = _checked_file(directory, expected["table"])
    if descriptor_file.read_bytes() != payload:
        raise ReportRebuildError("Published EPD descriptor changed during validation")
    return QualifiedReportSources(
        directory,
        {relative: descriptor_file, f"external/{SOURCE_ID}/{TABLE}": table},
        hashlib.sha256(payload).hexdigest(),
    )
