"""Bounded, non-extracting inventories of received source archives."""

from __future__ import annotations

import gzip
import hashlib
import io
from pathlib import Path
import re
import stat
import tarfile
import tomllib
from typing import Any, Protocol
import zipfile


class ArchiveError(ValueError):
    """A delivery violates its declared archive or metadata limits."""


class _Readable(Protocol):
    def read(self, size: int = -1) -> bytes: ...


def _positive_integer(value: int, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ArchiveError(f"{name} must be a positive integer")
    return value


def _path(name: str, *, directory: bool = False) -> str:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ArchiveError("invalid member path")
    path = name[:-1] if directory and name.endswith("/") else name
    if any(ord(c) < 32 or ord(c) == 127 for c in path):
        raise ArchiveError("control character in member path")
    if any(p in {"", ".", ".."} or ":" in p for p in path.split("/")):
        raise ArchiveError(f"unsafe member path: {name!r}")
    return path


def _sha(path: Path, maximum: int) -> str:
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        while block := stream.read(65536):
            total += len(block)
            if total > maximum:
                raise ArchiveError("received archive byte ceiling")
            digest.update(block)
    return digest.hexdigest()


class _TarReader(io.RawIOBase):
    """Bound decompressed container bytes, including otherwise hidden PAX data."""

    def __init__(self, stream: _Readable, maximum: int) -> None:
        self.stream = stream
        self.remaining = maximum

    def read(self, size: int = -1) -> bytes:
        request = self.remaining + 1 if size < 0 else min(size, self.remaining + 1)
        block = self.stream.read(request)
        self.remaining -= len(block)
        if self.remaining < 0:
            raise ArchiveError("tar container expansion ceiling")
        return block


def _role(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    if name.upper().startswith(("LICENSE", "NOTICE", "COPYING")):
        return "license_notice"
    if path == "pyproject.toml" or name in {"PKG-INFO", "METADATA", "entry_points.txt"}:
        return "package_metadata"
    if path.startswith("integration/"):
        return "integration_adapter" if path.endswith(".py") else "integration_receipt"
    if path.endswith((".py", ".R", ".r", ".sh")):
        return "source_code"
    if path.endswith((".json", ".csv", ".xlsx", ".xls", ".npz", ".rda", ".RData")):
        return "data_or_manifest"
    return "other"


def _selected(name: str) -> bool:
    relative = name.split("/", 1)[-1]
    return relative == "pyproject.toml" or _role(relative) == "license_notice"


def _project_metadata(project: Any) -> dict[str, Any]:
    if not isinstance(project, dict):
        raise ArchiveError("pyproject project is not a table")
    selected: dict[str, Any] = {}
    for key in (
        "name",
        "version",
        "requires-python",
        "license",
        "dependencies",
        "optional-dependencies",
        "scripts",
        "gui-scripts",
        "entry-points",
    ):
        if key not in project:
            continue
        value = project[key]
        if key in {"name", "version", "requires-python"}:
            valid = isinstance(value, str)
        elif key == "dependencies":
            valid = isinstance(value, list) and all(isinstance(v, str) for v in value)
        elif key == "optional-dependencies":
            valid = isinstance(value, dict) and all(
                isinstance(k, str)
                and isinstance(v, list)
                and all(isinstance(item, str) for item in v)
                for k, v in value.items()
            )
        elif key == "license":
            valid = isinstance(value, str) or (
                isinstance(value, dict)
                and bool(value)
                and set(value) <= {"text", "file"}
                and all(isinstance(v, str) for v in value.values())
            )
        else:
            tables = (
                value.values()
                if key == "entry-points" and isinstance(value, dict)
                else [value]
            )
            valid = isinstance(value, dict) and all(
                isinstance(table, dict)
                and all(
                    isinstance(k, str) and isinstance(v, str) for k, v in table.items()
                )
                for table in tables
            )
        if not valid:
            raise ArchiveError(f"invalid selected pyproject {key} metadata")
        selected[key] = value
    return selected


def _build_metadata(build: Any) -> dict[str, Any]:
    if not isinstance(build, dict):
        raise ArchiveError("pyproject build-system is not a table")
    selected = {}
    for key in ("requires", "build-backend"):
        if key not in build:
            continue
        value = build[key]
        valid = (
            isinstance(value, str)
            if key == "build-backend"
            else isinstance(value, list) and all(isinstance(v, str) for v in value)
        )
        if not valid:
            raise ArchiveError(f"invalid selected build-system {key} metadata")
        selected[key] = value
    return selected


def archive_inventory(
    path: Path,
    *,
    max_members: int = 4096,
    max_uncompressed_bytes: int = 32 * 1024 * 1024,
    max_member_bytes: int = 16 * 1024 * 1024,
    max_metadata_bytes: int = 64 * 1024,
    max_archive_bytes: int = 32 * 1024 * 1024,
) -> dict[str, Any]:
    """Hash regular members in memory; retain only explicitly selected metadata.

    An exact common outer directory, when present, is removed for comparison.
    Container paths remain literal in ``native_path``. Links, special members,
    duplicate names, encrypted ZIPs and uncovered limits fail closed.
    """
    for name, value in (
        ("max_members", max_members),
        ("max_uncompressed_bytes", max_uncompressed_bytes),
        ("max_member_bytes", max_member_bytes),
        ("max_metadata_bytes", max_metadata_bytes),
        ("max_archive_bytes", max_archive_bytes),
    ):
        _positive_integer(value, name)
    if path.is_symlink() or not path.is_file():
        raise ArchiveError("archive must be an ordinary file")
    source_size = path.stat().st_size
    if source_size > max_archive_bytes:
        raise ArchiveError("received archive byte ceiling")
    source_sha = _sha(path, max_archive_bytes)
    entries: list[dict[str, Any]] = []
    names: set[str] = set()
    bodies: dict[str, bytes] = {}
    total = 0
    metadata_total = 0

    def accept(name: str, size: int, directory: bool, stream: _Readable | None) -> None:
        nonlocal total, metadata_total
        normalized = _path(name, directory=directory)
        if normalized in names:
            raise ArchiveError(f"duplicate member path: {normalized}")
        names.add(normalized)
        if len(names) > max_members:
            raise ArchiveError("archive member-count ceiling")
        if type(size) is not int or size < 0 or size > max_member_bytes:
            raise ArchiveError("archive member byte ceiling")
        if directory and size:
            raise ArchiveError("directory has a payload")
        total += size
        if total > max_uncompressed_bytes:
            raise ArchiveError("archive uncompressed byte ceiling")
        digest = hashlib.sha256()
        selected = not directory and _selected(normalized)
        if selected:
            metadata_total += size
            if metadata_total > max_metadata_bytes:
                raise ArchiveError("selected metadata byte ceiling")
        retained = bytearray()
        actual = 0
        if not directory:
            if stream is None:
                raise ArchiveError("missing regular-file stream")
            while block := stream.read(min(65536, size - actual + 1)):
                actual += len(block)
                if actual > size:
                    raise ArchiveError("member exceeds declared byte size")
                digest.update(block)
                if selected:
                    retained.extend(block)
            if actual != size:
                raise ArchiveError("member is shorter than declared byte size")
        if selected:
            bodies[normalized] = bytes(retained)
        entries.append(
            {
                "native_path": name,
                "normalized_path": normalized,
                "type": "directory" if directory else "file",
                "bytes": size,
                "sha256": None if directory else digest.hexdigest(),
            }
        )

    try:
        if path.name.endswith(".zip"):
            archive_format = "zip"
            with zipfile.ZipFile(path) as zip_archive:
                if len(zip_archive.infolist()) > max_members:
                    raise ArchiveError("archive member-count ceiling")
                for member in zip_archive.infolist():
                    mode = member.external_attr >> 16
                    kind = stat.S_IFMT(mode)
                    directory = member.is_dir()
                    if kind not in (0, stat.S_IFDIR if directory else stat.S_IFREG):
                        raise ArchiveError("ZIP link or special member")
                    if member.flag_bits & 1:
                        raise ArchiveError("encrypted ZIP member")
                    if member.compress_type not in (
                        zipfile.ZIP_STORED,
                        zipfile.ZIP_DEFLATED,
                    ):
                        raise ArchiveError("unsupported ZIP compression")
                    with zip_archive.open(member) as stream:
                        accept(member.filename, member.file_size, directory, stream)
        elif path.name.endswith((".tar", ".tar.gz", ".tgz")):
            compressed = path.name.endswith((".tar.gz", ".tgz"))
            archive_format = "tar_gzip" if compressed else "tar"
            opener = gzip.open if compressed else open
            with opener(path, "rb") as original:
                bounded = _TarReader(
                    original, max_uncompressed_bytes + max_members * 4096 + 10240
                )
                with tarfile.open(fileobj=bounded, mode="r|") as tar_archive:
                    for tar_member in tar_archive:
                        if (
                            not (tar_member.isfile() or tar_member.isdir())
                            or tar_member.sparse is not None
                        ):
                            raise ArchiveError("TAR link, sparse or special member")
                        tar_stream = (
                            tar_archive.extractfile(tar_member)
                            if tar_member.isfile()
                            else None
                        )
                        try:
                            accept(
                                tar_member.name,
                                tar_member.size,
                                tar_member.isdir(),
                                tar_stream,
                            )
                        finally:
                            if tar_stream is not None:
                                tar_stream.close()
        else:
            raise ArchiveError("unsupported archive format")
    except (
        tarfile.TarError,
        zipfile.BadZipFile,
        EOFError,
        OSError,
        RuntimeError,
    ) as error:
        raise ArchiveError(f"unreadable archive: {error}") from error
    if not entries or not any(e["type"] == "file" for e in entries):
        raise ArchiveError("archive has no regular files")
    roots = {e["normalized_path"].split("/", 1)[0] for e in entries}
    files = {e["normalized_path"] for e in entries if e["type"] == "file"}
    for entry in entries:
        parts = entry["normalized_path"].split("/")
        if any("/".join(parts[:i]) in files for i in range(1, len(parts))):
            raise ArchiveError("regular file is an ancestor of another member")
    root = (
        next(iter(roots))
        if len(roots) == 1 and all("/" in name for name in files)
        else None
    )
    metadata: dict[str, Any] = {
        "pyproject": {},
        "build_system": {},
        "license_notice": {},
    }
    for entry in entries:
        native = entry.pop("normalized_path")
        relative = native.removeprefix(root + "/") if root is not None else native
        if root is not None and native == root:
            relative = ""
        entry["path"] = relative
        entry["role"] = "directory" if entry["type"] == "directory" else _role(relative)
        if native in bodies:
            try:
                text = bodies[native].decode("utf-8")
                if relative == "pyproject.toml":
                    document = tomllib.loads(text)
                    metadata["pyproject"][relative] = _project_metadata(
                        document.get("project", {})
                    )
                    metadata["build_system"][relative] = _build_metadata(
                        document.get("build-system", {})
                    )
                elif _role(relative) == "license_notice":
                    metadata["license_notice"][relative] = text
            except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
                raise ArchiveError("invalid selected package metadata") from error
    if source_size != path.stat().st_size or source_sha != _sha(
        path, max_archive_bytes
    ):
        raise ArchiveError("source archive changed during inventory")
    return {
        "schema_version": "lra-delivery-archive-inventory.v1",
        "source": {"path": str(path), "bytes": source_size, "sha256": source_sha},
        "format": archive_format,
        "root": root,
        "member_count": len(entries),
        "regular_file_count": sum(e["type"] == "file" for e in entries),
        "uncompressed_bytes": total,
        "members": entries,
        "metadata": metadata,
    }


def _files(inventory: dict[str, Any]) -> dict[str, str]:
    files: dict[str, str] = {}
    for entry in inventory["members"]:
        if entry["type"] == "file":
            name = _path(entry["path"])
            if name in files or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
                raise ArchiveError("invalid or duplicate file-map entry")
            files[name] = entry["sha256"]
    return files


def _compare(left: dict[str, str], right: dict[str, str]) -> dict[str, Any]:
    common = sorted(left.keys() & right.keys())
    differing = [p for p in common if left[p] != right[p]]
    return {
        "left_file_count": len(left),
        "right_file_count": len(right),
        "left_only": sorted(left.keys() - right.keys()),
        "right_only": sorted(right.keys() - left.keys()),
        "differing": [
            {"path": p, "left_sha256": left[p], "right_sha256": right[p]}
            for p in differing
        ],
        "equal_file_count": len(common) - len(differing),
        "equal": left == right,
    }


def compare_inventory_files(
    left: dict[str, Any], right: dict[str, Any]
) -> dict[str, Any]:
    """Compare every regular file after removing any exact common outer roots."""
    return _compare(_files(left), _files(right))


def compare_adoption_manifest(
    inventory: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    """Expose every missing, extra or changed source in the maintained manifest."""
    files: dict[str, str] = {}
    for row in manifest["files"]:
        name = _path(row["source"])
        if name in files or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
            raise ArchiveError("invalid or duplicate adoption source")
        files[name] = row["sha256"]
    return _compare(_files(inventory), files)
