"""Authenticate one retained Rootsi workbook without granting analytical reuse."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .contracts import ReportRebuildError, require_relative_path
from .qualified_sources import (
    FILE_FIELDS,
    SHA256,
    QualifiedReportSources,
    _checked_file,
    _object,
    _regular_path,
)

SCHEMA = "qualified-rootsi-bokesjon-workbook.v1"
SOURCE_ID = "landclim/rootsi-workbooks"
WORKBOOK = "rootsi/BOKE.xls"
MANIFEST_SHA256 = "dde88290dbdeca7a1047db74d5fb55a85c03a68daaef53795c5da9c1aebbd510"
MANIFEST_SIZE = 13099
WORKBOOK_SHA256 = "d95da5626a877b340e365317769fa0ef39cf371687b84004a996c30353dc4bc4"
WORKBOOK_SIZE = 68096
ARCHIVE_SHA256 = "f64d4dd411bc92362c9db2701c919063c2432e53fa523052e602da5f1a86183c"
RIGHTS = "unapproved_for_analytical_reuse"
HISTORICAL_IDENTITY = "not_established"
DESCRIPTOR_FIELDS = frozenset(
    {
        "schema_version",
        "source_id",
        "archive_sha256",
        "manifest",
        "workbook",
        "source_rights_status",
        "historical_primary_input_authentication",
    }
)
MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "archive_sha256",
        "workbook_count",
        "total_workbook_bytes",
        "source_rights_status",
        "historical_primary_input_authentication",
        "members",
    }
)
MEMBER_FIELDS = frozenset({"archive_member", "bytes", "sha256"})


def _spec(
    value: object, expected_path: str, expected_sha: str, size: int
) -> dict[str, Any]:
    if not isinstance(value, dict) or frozenset(value) != FILE_FIELDS:
        raise ReportRebuildError("Rootsi source file fields differ")
    if (
        value["path"] != expected_path
        or value["sha256"] != expected_sha
        or type(value["size"]) is not int
        or value["size"] != size
    ):
        raise ReportRebuildError("Rootsi source file identity differs")
    return value


def _unchanged(path: Path, expected_sha: str, expected_size: int) -> None:
    _checked_file(
        path.parent,
        {"path": path.name, "sha256": expected_sha, "size": expected_size},
    )


def validated_rootsi_bokesjon_workbook(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Bind the original BOKE member and receipt while retaining refusal posture."""
    repository = _regular_path(repository, directory=True)
    relative = require_relative_path(descriptor_path.as_posix(), "source descriptor")
    if relative.startswith("external/"):
        raise ReportRebuildError("source descriptor overlaps external input namespace")
    descriptor_file = _regular_path(repository / relative)
    descriptor_payload = descriptor_file.read_bytes()
    descriptor = _object(descriptor_payload)
    if (
        frozenset(descriptor) != DESCRIPTOR_FIELDS
        or descriptor["schema_version"] != SCHEMA
    ):
        raise ReportRebuildError("Rootsi descriptor schema or fields differ")
    if (
        descriptor["source_id"] != SOURCE_ID
        or descriptor["archive_sha256"] != ARCHIVE_SHA256
        or descriptor["source_rights_status"] != RIGHTS
        or descriptor["historical_primary_input_authentication"] != HISTORICAL_IDENTITY
    ):
        raise ReportRebuildError("Rootsi descriptor custody or refusal posture differs")
    manifest_spec = _spec(
        descriptor["manifest"], "manifest.json", MANIFEST_SHA256, MANIFEST_SIZE
    )
    workbook_spec = _spec(
        descriptor["workbook"], WORKBOOK, WORKBOOK_SHA256, WORKBOOK_SIZE
    )
    root = _regular_path(source_root, directory=True)
    if root.is_relative_to(repository) or repository.is_relative_to(root):
        raise ReportRebuildError("Rootsi source store must be separate from repository")
    directory = _regular_path(root / SOURCE_ID, directory=True)
    manifest_file = _checked_file(directory, manifest_spec)
    manifest_payload = manifest_file.read_bytes()
    if (
        len(manifest_payload) != MANIFEST_SIZE
        or hashlib.sha256(manifest_payload).hexdigest() != MANIFEST_SHA256
    ):
        raise ReportRebuildError("Rootsi manifest changed before parsing")
    manifest = _object(manifest_payload)
    if (
        frozenset(manifest) != MANIFEST_FIELDS
        or manifest["schema_version"] != "rootsi-external-source-custody.v1"
    ):
        raise ReportRebuildError("Rootsi custody manifest schema differs")
    if (
        manifest["archive_sha256"] != ARCHIVE_SHA256
        or manifest["source_rights_status"] != RIGHTS
        or manifest["historical_primary_input_authentication"] != HISTORICAL_IDENTITY
        or type(manifest["workbook_count"]) is not int
        or manifest["workbook_count"] != 79
        or type(manifest["total_workbook_bytes"]) is not int
        or manifest["total_workbook_bytes"] != 4466176
    ):
        raise ReportRebuildError("Rootsi custody manifest identity or refusal differs")
    members = manifest["members"]
    if not isinstance(members, list) or len(members) != 79:
        raise ReportRebuildError("Rootsi custody member population differs")
    names: list[str] = []
    total = 0
    selected: dict[str, Any] | None = None
    for member in members:
        if not isinstance(member, dict) or frozenset(member) != MEMBER_FIELDS:
            raise ReportRebuildError("Rootsi custody member fields differ")
        name = require_relative_path(member["archive_member"], "Rootsi archive member")
        if not name.startswith("rootsi/") or name == "rootsi/":
            raise ReportRebuildError("Rootsi archive member path differs")
        if (
            type(member["bytes"]) is not int
            or member["bytes"] <= 0
            or not isinstance(member["sha256"], str)
            or SHA256.fullmatch(member["sha256"]) is None
        ):
            raise ReportRebuildError("Rootsi custody member size or digest differs")
        names.append(name)
        total += member["bytes"]
        if name == WORKBOOK:
            selected = member
    if names != sorted(set(names)) or total != manifest["total_workbook_bytes"]:
        raise ReportRebuildError("Rootsi custody members are not complete and unique")
    if selected != {
        "archive_member": WORKBOOK,
        "bytes": WORKBOOK_SIZE,
        "sha256": WORKBOOK_SHA256,
    }:
        raise ReportRebuildError("Rootsi selected workbook differs from custody")
    workbook_file = _checked_file(directory, workbook_spec)
    _unchanged(manifest_file, MANIFEST_SHA256, MANIFEST_SIZE)
    _unchanged(workbook_file, WORKBOOK_SHA256, WORKBOOK_SIZE)
    if _regular_path(descriptor_file).read_bytes() != descriptor_payload:
        raise ReportRebuildError("Rootsi descriptor changed during validation")
    return QualifiedReportSources(
        directory,
        {
            relative: descriptor_file,
            f"external/{SOURCE_ID}/manifest.json": manifest_file,
            f"external/{SOURCE_ID}/{WORKBOOK}": workbook_file,
        },
        hashlib.sha256(descriptor_payload).hexdigest(),
    )
