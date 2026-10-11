"""Authenticate the retained two-grid candidate beside the author snapshot."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .author_snapshot import validated_author_snapshot
from .contracts import ReportRebuildError, require_relative_path
from .qualified_sources import (
    FILE_FIELDS,
    SHA256,
    QualifiedReportSources,
    _checked_file,
    _object,
    _regular_path,
)

SCHEMA = "qualified-landclim-two-grid-packet.v1"
FIELDS = frozenset(
    {
        "schema_version",
        "source_id",
        "run_path",
        "author_descriptor",
        "author_descriptor_sha256",
        "file_count",
        "files",
    }
)
SOURCE_ID = "landclim/two-grid-process"
RUN_PATH = "run/run001"
AUTHOR_DESCRIPTOR = Path(
    "configs/ci/qualified-report-sources/landclim-author-snapshot.json"
)
AUTHOR_DESCRIPTOR_SHA256 = (
    "040bc11b10cd2486051400e1f87fd58a5a2b48a9ee5993fb7995e24625b67ff7"
)
FILE_COUNT = 70


def _spec(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or frozenset(value) != FILE_FIELDS:
        raise ReportRebuildError("two-grid packet file fields differ")
    require_relative_path(value["path"], "two-grid packet file")
    if (
        not isinstance(value["sha256"], str)
        or SHA256.fullmatch(value["sha256"]) is None
        or type(value["size"]) is not int
        or value["size"] <= 0
    ):
        raise ReportRebuildError("two-grid packet file identity differs")
    return value


def validated_landclim_two_grid_packet(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Bind the complete retained candidate and already-qualified author files."""
    repository = _regular_path(repository, directory=True)
    relative = require_relative_path(descriptor_path.as_posix(), "two-grid descriptor")
    descriptor_file = _regular_path(repository / relative)
    payload = descriptor_file.read_bytes()
    descriptor = _object(payload)
    if (
        frozenset(descriptor) != FIELDS
        or descriptor["schema_version"] != SCHEMA
        or descriptor["source_id"] != SOURCE_ID
        or descriptor["run_path"] != RUN_PATH
        or descriptor["author_descriptor"] != AUTHOR_DESCRIPTOR.as_posix()
        or descriptor["author_descriptor_sha256"] != AUTHOR_DESCRIPTOR_SHA256
        or type(descriptor["file_count"]) is not int
        or descriptor["file_count"] != FILE_COUNT
    ):
        raise ReportRebuildError("two-grid packet scope or schema differs")
    author_file = _regular_path(repository / AUTHOR_DESCRIPTOR)
    if hashlib.sha256(author_file.read_bytes()).hexdigest() != AUTHOR_DESCRIPTOR_SHA256:
        raise ReportRebuildError("two-grid author descriptor identity differs")
    author = validated_author_snapshot(repository, source_root, AUTHOR_DESCRIPTOR)
    root = _regular_path(source_root, directory=True)
    directory = _regular_path(root / SOURCE_ID / RUN_PATH, directory=True)
    values = descriptor["files"]
    if not isinstance(values, list) or len(values) != FILE_COUNT:
        raise ReportRebuildError("two-grid packet file count differs")
    specs = [_spec(value) for value in values]
    names = [spec["path"] for spec in specs]
    if names != sorted(set(names)):
        raise ReportRebuildError("two-grid packet files must be sorted and unique")
    expected = set(names)
    expected_directories = {
        parent.as_posix()
        for name in names
        for parent in Path(name).parents
        if parent != Path(".")
    }
    observed: set[str] = set()
    for entry in directory.rglob("*"):
        relative_entry = entry.relative_to(directory).as_posix()
        if entry.is_dir():
            _regular_path(entry, directory=True)
            if relative_entry not in expected_directories:
                raise ReportRebuildError("two-grid packet has an unexpected directory")
        else:
            _regular_path(entry)
            observed.add(relative_entry)
    if observed != expected:
        raise ReportRebuildError("two-grid packet directory population differs")
    inputs = {
        key: path
        for key, path in author.inputs.items()
        if key != AUTHOR_DESCRIPTOR.as_posix()
    }
    inputs[relative] = descriptor_file
    for spec in specs:
        inputs[f"external/{SOURCE_ID}/{RUN_PATH}/{spec['path']}"] = _checked_file(
            directory, spec
        )
    for spec in specs:
        _checked_file(directory, spec)
    if descriptor_file.read_bytes() != payload:
        raise ReportRebuildError("two-grid packet descriptor changed")
    return QualifiedReportSources(root, inputs, hashlib.sha256(payload).hexdigest())
