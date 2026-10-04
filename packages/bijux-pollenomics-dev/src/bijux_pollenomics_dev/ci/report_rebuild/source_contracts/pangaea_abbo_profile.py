"""Bind the retained primary Abborrtjärnen pollen profile without inventing capture custody."""

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

SCHEMA = "qualified-pangaea-abbo-profile.v1"
SOURCE_ID = "epd/pangaea"
TABLE = "abbo-pollen-profile-pangaea-738429.tsv"
TABLE_SHA256 = "ee4671277fc4120c65f6fe4fa19fb1d302167e419d5419a55287d09c226ab154"
TABLE_SIZE = 43894
DOI = "10.1594/PANGAEA.738429"
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


def validated_abbo_profile(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Authenticate one exact retained table; its acquisition history remains unestablished."""
    repository = _regular_path(repository, directory=True)
    relative = require_relative_path(descriptor_path.as_posix(), "source descriptor")
    if relative.startswith("external/"):
        raise ReportRebuildError("ABBO descriptor overlaps external inputs")
    descriptor_file = _regular_path(repository / relative)
    payload = descriptor_file.read_bytes()
    descriptor = _object(payload)
    expected: dict[str, Any] = {
        "schema_version": SCHEMA,
        "source_id": SOURCE_ID,
        "table": {"path": TABLE, "sha256": TABLE_SHA256, "size": TABLE_SIZE},
        "doi": DOI,
        "license": "CC-BY-NC-3.0",
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
            "ABBO primary table descriptor identity or limits differ"
        )
    root = _regular_path(source_root, directory=True)
    if root.is_relative_to(repository) or repository.is_relative_to(root):
        raise ReportRebuildError("ABBO primary table store must be external")
    directory = _regular_path(root / SOURCE_ID, directory=True)
    table = _checked_file(directory, expected["table"])
    _checked_file(directory, expected["table"])
    if descriptor_file.read_bytes() != payload:
        raise ReportRebuildError("ABBO descriptor changed during validation")
    return QualifiedReportSources(
        directory,
        {relative: descriptor_file, f"external/{SOURCE_ID}/{TABLE}": table},
        hashlib.sha256(payload).hexdigest(),
    )
