"""Bind the two retained Rootsi native-count members without analytical admission."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..contracts import ReportRebuildError, require_relative_path
from ..qualified_sources import (
    QualifiedReportSources,
    _checked_file,
    _object,
    _regular_path,
)
from ..rootsi_workbook import validated_rootsi_bokesjon_workbook

SCHEMA = "qualified-rootsi-native-workbook.v1"
BASE_DESCRIPTOR = Path(
    "configs/ci/qualified-report-sources/rootsi-bokesjon-workbook.json"
)
MEMBERS = {
    "rootsi/ABB.xls": (
        74240,
        "205e7f77adde19b2c590d222acdd526d472e76ac22d0b8f27f7728acf451fa49",
    ),
    "rootsi/BUS.xls": (
        59904,
        "f807c5dc0b624db382ce81959ea7d48c348b637018faa873b7ab9ad1f23e197e",
    ),
}


def validated_rootsi_native_workbook(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Reuse the full frozen manifest contract, then authenticate one exact member."""
    repository = _regular_path(repository, directory=True)
    relative = require_relative_path(descriptor_path.as_posix(), "source descriptor")
    if relative.startswith("external/") or descriptor_path == BASE_DESCRIPTOR:
        raise ReportRebuildError("Rootsi native descriptor overlaps protected inputs")
    descriptor_file = _regular_path(repository / relative)
    payload = descriptor_file.read_bytes()
    descriptor = _object(payload)
    if set(descriptor) != {"schema_version", "base_descriptor", "workbook"}:
        raise ReportRebuildError("Rootsi native descriptor fields differ")
    spec = descriptor["workbook"]
    if (
        descriptor["schema_version"] != SCHEMA
        or descriptor["base_descriptor"] != BASE_DESCRIPTOR.as_posix()
        or not isinstance(spec, dict)
        or set(spec) != {"path", "size", "sha256"}
        or not isinstance(spec["path"], str)
        or spec["path"] not in MEMBERS
    ):
        raise ReportRebuildError("Rootsi native workbook selection differs")
    size, digest = MEMBERS[spec["path"]]
    if (
        type(spec["size"]) is not int
        or spec["size"] != size
        or spec["sha256"] != digest
    ):
        raise ReportRebuildError("Rootsi native workbook identity differs")
    qualified = validated_rootsi_bokesjon_workbook(
        repository, source_root, BASE_DESCRIPTOR
    )
    manifest_file = qualified.directory / "manifest.json"
    manifest = _object(manifest_file.read_bytes())
    matches = [
        row for row in manifest["members"] if row["archive_member"] == spec["path"]
    ]
    if matches != [{"archive_member": spec["path"], "bytes": size, "sha256": digest}]:
        raise ReportRebuildError("Rootsi native member differs from frozen manifest")
    workbook = _checked_file(qualified.directory, spec)
    after = validated_rootsi_bokesjon_workbook(repository, source_root, BASE_DESCRIPTOR)
    _checked_file(qualified.directory, spec)
    if after != qualified or _regular_path(descriptor_file).read_bytes() != payload:
        raise ReportRebuildError("Rootsi native inputs changed during qualification")
    return QualifiedReportSources(
        qualified.directory,
        {
            **qualified.inputs,
            relative: descriptor_file,
            f"external/landclim/rootsi-workbooks/{spec['path']}": workbook,
        },
        hashlib.sha256(payload).hexdigest(),
    )
