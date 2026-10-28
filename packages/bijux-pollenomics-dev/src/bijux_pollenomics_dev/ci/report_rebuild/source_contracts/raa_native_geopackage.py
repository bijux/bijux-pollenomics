"""Authenticate the existing finalized national capture without adopting its use."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ..contracts import ReportRebuildError, require_relative_path
from ..qualified_sources import (
    QualifiedReportSources,
    _checked_file,
    _file_spec,
    _object,
    _regular_path,
)

SCHEMA = "qualified-raa-native-geopackage.v1"
SOURCE_ID = "raa/lamningar-v1"
SOURCE_SHA256 = "96bbe197a84c70b64f047873ded15ce5df568198dc0794870a782decb82fed0b"
SOURCE_BYTES = 2291224576
SOURCE_URL = (
    "https://pub.raa.se/nedladdning/datauttag/lamningar_v1/l%c3%a4mningar_sverige.gpkg"
)
NAMES = {
    "capture.json",
    "lamningar_sverige.gpkg",
    "report.json",
    "request.json",
    "response.json",
}


def check_capture(capture: dict[str, Any], native: dict[str, Any]) -> None:
    """Require the original national byte identity and nonadmission flags."""
    if (
        native["sha256"] != SOURCE_SHA256
        or type(native["size"]) is not int
        or native["size"] != SOURCE_BYTES
    ):
        raise ReportRebuildError("RAÄ original national byte identity differs")
    if (
        capture.get("sha256") != SOURCE_SHA256
        or type(capture.get("byte_count")) is not int
        or capture["byte_count"] != SOURCE_BYTES
        or capture.get("file") != "lamningar_sverige.gpkg"
        or capture.get("url") != SOURCE_URL
        or capture.get("scientific_admission") is not False
        or capture.get("canonical_adoption") is not False
    ):
        raise ReportRebuildError(
            "RAÄ existing capture identity or nonadmission flags differ"
        )


def validated_raa_geopackage(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Reuse exact original bytes and receipts; no download or rights decision."""
    repository = _regular_path(repository, directory=True)
    relative = require_relative_path(
        descriptor_path.as_posix(), "RAÄ source descriptor"
    )
    descriptor_file = _regular_path(repository / relative)
    payload = descriptor_file.read_bytes()
    descriptor = _object(payload)
    if (
        set(descriptor) != {"schema_version", "source_id", "files"}
        or descriptor["schema_version"] != SCHEMA
        or descriptor["source_id"] != SOURCE_ID
    ):
        raise ReportRebuildError(
            "RAÄ source descriptor schema or source identity differs"
        )
    rows = descriptor["files"]
    if not isinstance(rows, list):
        raise ReportRebuildError("RAÄ source file population is not a list")
    specs = [_file_spec(row) for row in rows]
    names = [row["path"] for row in specs]
    if names != sorted(NAMES):
        raise ReportRebuildError("RAÄ exact five original source members required")
    root = _regular_path(source_root, directory=True)
    if root.is_relative_to(repository) or repository.is_relative_to(root):
        raise ReportRebuildError("RAÄ source store must remain outside repository")
    directory = _regular_path(root / SOURCE_ID, directory=True)
    inputs = {relative: descriptor_file}
    for spec in specs:
        if spec["path"] != "lamningar_sverige.gpkg" and spec["size"] > 8 * 1024 * 1024:
            raise ReportRebuildError("RAÄ source receipt exceeds finite metadata bound")
        inputs["external/" + SOURCE_ID + "/" + spec["path"]] = _checked_file(
            directory, spec
        )
    capture = _object(inputs["external/" + SOURCE_ID + "/capture.json"].read_bytes())
    check_capture(
        capture, next(row for row in specs if row["path"] == "lamningar_sverige.gpkg")
    )
    if _regular_path(descriptor_file).read_bytes() != payload:
        raise ReportRebuildError("RAÄ source descriptor changed during validation")
    return QualifiedReportSources(
        directory, inputs, hashlib.sha256(payload).hexdigest()
    )
