"""Authenticate explicitly supplied external report inputs without copying them."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import stat
from typing import Any
from urllib.parse import urlsplit

from .contracts import ReportRebuildError, require_relative_path

SCHEMA = "qualified-report-source-bundle.v1"
FIELDS = frozenset(
    {
        "schema_version",
        "source_id",
        "source_doi",
        "license",
        "authority_url",
        "custody",
        "files",
    }
)
FILE_FIELDS = frozenset({"path", "sha256", "size"})
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class QualifiedReportSources:
    """A checked source directory and the exact files consumed by its owner."""

    directory: Path
    inputs: dict[str, Path]
    descriptor_sha256: str


def _regular_path(path: Path, *, directory: bool = False) -> Path:
    """Refuse symlinks in the supplied path before resolving any component."""
    path = path.absolute()
    if any(part in {".", ".."} for part in path.parts):
        raise ReportRebuildError("qualified source path is not canonical")
    try:
        for ancestor in reversed(path.parents):
            if not stat.S_ISDIR(ancestor.lstat().st_mode):
                raise ReportRebuildError("qualified source has a non-real ancestor")
        mode = path.lstat().st_mode
        expected = stat.S_ISDIR if directory else stat.S_ISREG
        if not expected(mode):
            raise ReportRebuildError("qualified source is not a real regular path")
    except OSError as error:
        raise ReportRebuildError(f"qualified source is unreadable: {path}") from error
    return path


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReportRebuildError(f"duplicate qualified source key: {key}")
        result[key] = value
    return result


def _object(payload: bytes) -> dict[str, Any]:
    try:
        value = json.loads(payload, object_pairs_hook=_unique_pairs)
    except (ValueError, UnicodeError) as error:
        raise ReportRebuildError("qualified source JSON is invalid") from error
    if not isinstance(value, dict):
        raise ReportRebuildError("qualified source JSON must be an object")
    return value


def _file_spec(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or frozenset(value) != FILE_FIELDS:
        raise ReportRebuildError("qualified source file fields differ")
    require_relative_path(value["path"], "qualified source file")
    if (
        not isinstance(value["sha256"], str)
        or SHA256.fullmatch(value["sha256"]) is None
    ):
        raise ReportRebuildError("qualified source SHA256 is invalid")
    if type(value["size"]) is not int or value["size"] <= 0:
        raise ReportRebuildError("qualified source size must be positive")
    return value


def _checked_file(directory: Path, spec: dict[str, Any]) -> Path:
    path = _regular_path(directory / spec["path"])
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
                size += len(block)
    except OSError as error:
        raise ReportRebuildError(f"cannot read qualified source: {path}") from error
    if size != spec["size"] or digest.hexdigest() != spec["sha256"]:
        raise ReportRebuildError(f"qualified source bytes differ: {spec['path']}")
    return path


def _https(value: object) -> str:
    if not isinstance(value, str):
        raise ReportRebuildError("qualified source authority URL is invalid")
    try:
        parsed = urlsplit(value)
    except ValueError as error:
        raise ReportRebuildError("qualified source authority URL is invalid") from error
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
    ):
        raise ReportRebuildError("qualified source authority URL must use HTTPS")
    return value


def validated_external_report_sources(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Check a repository contract against a real external packet and receipt.

    The contract pins previously assessed custody bytes. Checking those bytes
    establishes input identity; it does not supply scientific admission or a
    new rights decision. The external store is an explicit runtime prerequisite.
    """
    repository = repository.resolve(strict=True)
    relative = require_relative_path(descriptor_path.as_posix(), "source descriptor")
    if relative.startswith("external/"):
        raise ReportRebuildError("source descriptor overlaps external input namespace")
    descriptor_file = _regular_path(repository / relative)
    payload = descriptor_file.read_bytes()
    descriptor = _object(payload)
    if frozenset(descriptor) != FIELDS or descriptor["schema_version"] != SCHEMA:
        raise ReportRebuildError("qualified source descriptor schema or fields differ")
    source_id = require_relative_path(descriptor["source_id"], "qualified source ID")
    for name in ("source_doi", "license"):
        if not isinstance(descriptor[name], str) or not descriptor[name].strip():
            raise ReportRebuildError(f"qualified source {name} is missing")
    authority = _https(descriptor["authority_url"])
    root = _regular_path(source_root, directory=True)
    if root.is_relative_to(repository) or repository.is_relative_to(root):
        raise ReportRebuildError(
            "qualified source store must be separate from repository"
        )
    directory = _regular_path(root / source_id, directory=True)
    custody = _file_spec(descriptor["custody"])
    if custody["size"] > 8 * 1024 * 1024:
        raise ReportRebuildError("qualified custody receipt exceeds size limit")
    receipt_file = _checked_file(directory, custody)
    receipt_payload = receipt_file.read_bytes()
    if (
        len(receipt_payload) != custody["size"]
        or hashlib.sha256(receipt_payload).hexdigest() != custody["sha256"]
    ):
        raise ReportRebuildError("qualified custody bytes changed before parsing")
    receipt = _object(receipt_payload)
    if (
        receipt.get("source_doi") != descriptor["source_doi"]
        or receipt.get("license") != descriptor["license"]
        or receipt.get("license_source") != authority
    ):
        raise ReportRebuildError(
            "qualified custody authority or rights identity differs"
        )
    rows = receipt.get("files")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ReportRebuildError("qualified custody files are invalid")
    if any(not isinstance(row.get("file"), str) for row in rows):
        raise ReportRebuildError("qualified custody filenames are invalid")
    receipt_files = {row.get("file"): row for row in rows}
    if len(receipt_files) != len(rows) or any(
        not isinstance(key, str) for key in receipt_files
    ):
        raise ReportRebuildError(
            "qualified custody filenames are invalid or duplicated"
        )
    files = descriptor["files"]
    if not isinstance(files, list) or not 1 <= len(files) <= 64:
        raise ReportRebuildError(
            "qualified source file list must contain 1 to 64 files"
        )
    specs = [_file_spec(value) for value in files]
    names = [spec["path"] for spec in specs]
    if names != sorted(set(names)) or custody["path"] in names:
        raise ReportRebuildError(
            "qualified source filenames must be sorted and independent"
        )
    inputs = {
        relative: descriptor_file,
        f"external/{source_id}/{custody['path']}": receipt_file,
    }
    for spec in specs:
        row = receipt_files.get(spec["path"])
        if (
            row is None
            or row.get("sha256") != spec["sha256"]
            or type(row.get("http_status")) is not int
            or row["http_status"] != 200
            or not isinstance(row.get("http"), dict)
            or row["http"].get("content-length") != str(spec["size"])
        ):
            raise ReportRebuildError("qualified source differs from custody retrieval")
        _https(row.get("url"))
        inputs[f"external/{source_id}/{spec['path']}"] = _checked_file(directory, spec)
    if descriptor_file.read_bytes() != payload:
        raise ReportRebuildError(
            "qualified source descriptor changed during validation"
        )
    return QualifiedReportSources(
        directory, inputs, hashlib.sha256(payload).hexdigest()
    )
