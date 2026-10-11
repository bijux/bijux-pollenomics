"""Stream external regular files and retain portable identities without native copies."""

from __future__ import annotations

import base64
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
from typing import BinaryIO

from ...quarantine import IntakeRefusal
from .archives import archive_records
from .contracts import (
    LocalInventoryLimits,
    checked_path,
    encode,
    integer,
    relative_path,
    sha256,
)


@dataclass(frozen=True)
class FileStamp:
    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    mode: int

    @classmethod
    def from_stat(cls, value: os.stat_result) -> FileStamp:
        return cls(
            value.st_dev,
            value.st_ino,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
            value.st_mode,
        )


def source_snapshot(root: Path, limits: LocalInventoryLimits) -> dict[str, FileStamp]:
    """Include hidden files; refuse links and special nodes before any payload read."""
    root = checked_path(root)
    if root.is_symlink() or not root.is_dir():
        raise IntakeRefusal("hyde_source_root_invalid", str(root))
    result = {}

    def walk_error(error: OSError) -> None:
        raise IntakeRefusal("hyde_source_traversal_failed", str(error)) from error

    for directory, directories, files in os.walk(
        root, followlinks=False, onerror=walk_error
    ):
        for name in directories:
            if (Path(directory) / name).is_symlink():
                raise IntakeRefusal("hyde_source_symlink", name)
        for name in files:
            path = Path(directory) / name
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise IntakeRefusal("hyde_source_nonregular", str(path))
            relative = relative_path(path.relative_to(root).as_posix())
            result[relative] = FileStamp.from_stat(info)
            if len(result) > limits.maximum_files:
                raise IntakeRefusal("hyde_source_file_limit", str(len(result)))
    if not result:
        raise IntakeRefusal("hyde_source_empty", str(root))
    return dict(sorted(result.items()))


def unchanged(
    root: Path, expected: dict[str, FileStamp], limits: LocalInventoryLimits
) -> None:
    if source_snapshot(root, limits) != expected:
        raise IntakeRefusal(
            "hyde_source_changed", "Complete source file set or identity changed"
        )


@contextmanager
def stable_file(path: Path, expected: FileStamp) -> Iterator[BinaryIO]:
    """No-follow descriptor ownership brackets every hash and metadata read."""
    path = checked_path(path)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        if (
            FileStamp.from_stat(os.fstat(stream.fileno())) != expected
            or path.is_symlink()
        ):
            raise IntakeRefusal("hyde_source_changed", str(path))
        yield stream
        if (
            FileStamp.from_stat(os.fstat(stream.fileno())) != expected
            or FileStamp.from_stat(path.lstat()) != expected
        ):
            raise IntakeRefusal("hyde_source_changed", str(path))


def hash_file(path: Path, expected: FileStamp, limits: LocalInventoryLimits) -> str:
    checksum = hashlib.sha256()
    with stable_file(path, expected) as stream:
        while content := stream.read(limits.chunk_bytes):
            checksum.update(content)
    return checksum.hexdigest()


def file_record(
    root: Path, name: str, stamp: FileStamp, limits: LocalInventoryLimits
) -> dict[str, object]:
    return {
        "path": name,
        "bytes": stamp.size,
        "sha256": hash_file(root / name, stamp, limits),
        "classification": "ancillary" if Path(name).name == ".DS_Store" else "dataset",
        "archive_directory": None,
    }


def metadata_candidate(name: str) -> bool:
    native = Path(name).name.casefold()
    return native.startswith(("readme", "license", "yoda-metadata"))


def collect_sources(
    root: Path, snapshot: dict[str, FileStamp], limits: LocalInventoryLimits
) -> dict[str, object]:
    """One shared collector for initial custody and independent external replay."""
    files = []
    archives = []
    metadata = []
    captured = 0
    metadata_bytes = 0
    for name, stamp in snapshot.items():
        row = file_record(root, name, stamp, limits)
        files.append(row)
        if Path(name).suffix.casefold() == ".zip":
            with stable_file(root / name, stamp) as stream:
                entries, directory = archive_records(
                    stream, name, str(row["sha256"]), stamp.size, limits
                )
            row["archive_directory"] = directory
            archives.extend(entries)
            metadata_bytes += sum(len(encode(entry)) for entry in entries)
            if (
                len(archives) > limits.maximum_archive_members
                or metadata_bytes > limits.maximum_retained_bytes
            ):
                raise IntakeRefusal("hyde_archive_metadata_limit", name)
        if metadata_candidate(name):
            content: bytes | None = None
            if (
                stamp.size <= limits.maximum_metadata_file_bytes
                and captured + stamp.size <= limits.maximum_metadata_total_bytes
            ):
                with stable_file(root / name, stamp) as stream:
                    content = stream.read(limits.maximum_metadata_file_bytes + 1)
                if len(content) != stamp.size or sha256(content) != row["sha256"]:
                    raise IntakeRefusal("hyde_source_changed", name)
                captured += len(content)
            metadata.append(
                {
                    "path": name,
                    "sha256": row["sha256"],
                    "bytes": stamp.size,
                    "capture_status": "exact_bytes_retained"
                    if content is not None
                    else "hash_reference_size_limit",
                    "bytes_base64": base64.b64encode(content).decode("ascii")
                    if content is not None
                    else None,
                }
            )
    return {"files.json": files, "archives.json": archives, "metadata.json": metadata}


def summary(
    files: list[dict[str, object]], archives: list[dict[str, object]]
) -> dict[str, object]:
    dataset = [row for row in files if row["classification"] == "dataset"]
    return {
        "file_count": len(files),
        "byte_count": sum(integer(row["bytes"], "bytes") for row in files),
        "dataset_file_count": len(dataset),
        "dataset_byte_count": sum(integer(row["bytes"], "bytes") for row in dataset),
        "ancillary_file_count": len(files) - len(dataset),
        "archive_file_count": sum(
            Path(str(row["path"])).suffix.casefold() == ".zip" for row in files
        ),
        "archive_member_count": len(archives),
        "netcdf_named_file_count": sum(
            Path(str(row["path"])).suffix.casefold() == ".nc" for row in files
        ),
    }
