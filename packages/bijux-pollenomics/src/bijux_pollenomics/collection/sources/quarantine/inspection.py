"""Resource-bounded archive identity, topology, and content inspection."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import IO
import unicodedata
from zipfile import BadZipFile, ZipFile, ZipInfo

from .models import (
    ArchiveIdentity,
    ArchiveInventory,
    ArchiveLimits,
    ArchiveMember,
    IntakeRefusal,
)

_BUFFER_BYTES = 1024 * 1024


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest without interpreting file content."""
    with path.open("rb") as stream:
        return sha256_stream(stream)


def sha256_stream(stream: IO[bytes]) -> str:
    """Hash a seekable stream and restore it to its beginning."""
    digest = hashlib.sha256()
    stream.seek(0)
    for chunk in iter(lambda: stream.read(_BUFFER_BYTES), b""):
        digest.update(chunk)
    stream.seek(0)
    return digest.hexdigest()


def _safe_member_path(name: str) -> PurePosixPath:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise IntakeRefusal("unsafe_archive_path", repr(name))
    if path.parts and path.parts[0].endswith(":"):
        raise IntakeRefusal("unsafe_archive_path", repr(name))
    return path


def _collision_key(name: str) -> str:
    path = _safe_member_path(name)
    return unicodedata.normalize("NFC", path.as_posix()).casefold()


def _member_from_zip(info: ZipInfo) -> ArchiveMember:
    _safe_member_path(info.filename)
    unix_mode = (info.external_attr >> 16) & 0xFFFF
    file_type = stat.S_IFMT(unix_mode)
    if stat.S_ISLNK(unix_mode):
        raise IntakeRefusal("archive_symlink", info.filename)
    if file_type and not (stat.S_ISREG(unix_mode) or stat.S_ISDIR(unix_mode)):
        raise IntakeRefusal("archive_special_file", info.filename)
    if info.flag_bits & 1:
        raise IntakeRefusal("encrypted_archive_member", info.filename)
    return ArchiveMember(
        path=info.filename,
        size_bytes=info.file_size,
        compressed_size_bytes=info.compress_size,
        crc32=f"{info.CRC:08x}",
        is_directory=info.is_dir(),
        is_encrypted=False,
        unix_mode=unix_mode or None,
        content_sha256=None,
    )


def _enforce_limits(members: tuple[ArchiveMember, ...], limits: ArchiveLimits) -> None:
    if len(members) > limits.maximum_members:
        raise IntakeRefusal("archive_member_limit", str(len(members)))
    expanded = sum(member.size_bytes for member in members)
    if expanded > limits.maximum_expanded_bytes:
        raise IntakeRefusal("archive_expanded_size_limit", str(expanded))
    paths = [member.path for member in members]
    if len(set(paths)) != len(paths):
        raise IntakeRefusal("duplicate_archive_member", "member paths repeat")
    collision_keys = [_collision_key(path) for path in paths]
    if len(set(collision_keys)) != len(collision_keys):
        raise IntakeRefusal(
            "colliding_archive_member", "normalized member paths repeat"
        )
    for member in members:
        if member.size_bytes > limits.maximum_member_bytes:
            raise IntakeRefusal("archive_member_size_limit", member.path)
        compressed = max(member.compressed_size_bytes, 1)
        if member.size_bytes / compressed > limits.maximum_compression_ratio:
            raise IntakeRefusal("archive_compression_ratio_limit", member.path)


def _member_sha256(archive: ZipFile, info: ZipInfo, member: ArchiveMember) -> str:
    digest = hashlib.sha256()
    copied = 0
    with archive.open(info) as source:
        while chunk := source.read(_BUFFER_BYTES):
            copied += len(chunk)
            if copied > member.size_bytes:
                raise IntakeRefusal("archive_output_size_limit", member.path)
            digest.update(chunk)
    if copied != member.size_bytes:
        raise IntakeRefusal(
            "archive_output_size_mismatch",
            f"{member.path}: expected {member.size_bytes}, got {copied}",
        )
    return digest.hexdigest()


def _manifest_digest(members: tuple[ArchiveMember, ...]) -> str:
    rows = [
        {
            "compressed_size_bytes": member.compressed_size_bytes,
            "content_sha256": member.content_sha256,
            "crc32": member.crc32,
            "is_directory": member.is_directory,
            "path": member.path,
            "size_bytes": member.size_bytes,
        }
        for member in members
    ]
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _inspect_zip_stream(
    stream: IO[bytes],
    *,
    filename: str,
    size_bytes: int,
    expected_sha256: str,
    limits: ArchiveLimits,
) -> ArchiveInventory:
    actual_sha256 = sha256_stream(stream)
    if actual_sha256 != expected_sha256:
        raise IntakeRefusal(
            "archive_digest_mismatch",
            f"expected {expected_sha256}, got {actual_sha256}",
        )
    try:
        with ZipFile(stream) as archive:
            infos = archive.infolist()
            metadata = tuple(_member_from_zip(info) for info in infos)
            _enforce_limits(metadata, limits)
            members = tuple(
                member
                if member.is_directory
                else replace(
                    member,
                    content_sha256=_member_sha256(archive, info, member),
                )
                for info, member in zip(infos, metadata, strict=True)
            )
    except BadZipFile as exc:
        raise IntakeRefusal("invalid_zip_archive", str(exc)) from exc
    if sha256_stream(stream) != actual_sha256:
        raise IntakeRefusal("archive_changed_during_inspection", filename)
    return ArchiveInventory(
        identity=ArchiveIdentity(
            filename=filename,
            size_bytes=size_bytes,
            sha256=actual_sha256,
            media_type="application/zip",
        ),
        members=members,
        expanded_bytes=sum(member.size_bytes for member in members),
        member_manifest_sha256=_manifest_digest(members),
    )


def inspect_zip_archive(
    path: Path,
    *,
    expected_sha256: str,
    limits: ArchiveLimits = ArchiveLimits(),
) -> ArchiveInventory:
    """Bind a safe ZIP inventory to the expected immutable receipt."""
    with path.open("rb") as stream:
        return _inspect_zip_stream(
            stream,
            filename=path.name,
            size_bytes=os.fstat(stream.fileno()).st_size,
            expected_sha256=expected_sha256,
            limits=limits,
        )


@contextmanager
def inspected_zip_archive(
    path: Path,
    *,
    expected_sha256: str,
    limits: ArchiveLimits = ArchiveLimits(),
) -> Iterator[tuple[ArchiveInventory, ZipFile]]:
    """Yield a ZIP reader bound to the same validated file descriptor."""
    with path.open("rb") as stream:
        inventory = _inspect_zip_stream(
            stream,
            filename=path.name,
            size_bytes=os.fstat(stream.fileno()).st_size,
            expected_sha256=expected_sha256,
            limits=limits,
        )
        stream.seek(0)
        with ZipFile(stream) as archive:
            yield inventory, archive
        if sha256_stream(stream) != inventory.identity.sha256:
            raise IntakeRefusal("archive_changed_during_read", path.name)
