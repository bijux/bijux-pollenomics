"""Selective archive extraction bound to a freshly validated receipt."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
from typing import IO
from zipfile import ZipFile

from .inspection import (
    _BUFFER_BYTES,
    _inspect_zip_stream,
    _safe_member_path,
    sha256_stream,
)
from .models import ArchiveInventory, ArchiveLimits, ArchiveMember, IntakeRefusal


def extract_zip_members(
    archive_path: Path,
    destination: Path,
    inventory: ArchiveInventory,
    member_paths: tuple[str, ...],
    *,
    limits: ArchiveLimits = ArchiveLimits(),
) -> tuple[Path, ...]:
    """Copy explicitly selected regular members after fresh validation."""
    if destination.is_symlink() or not destination.is_dir():
        raise IntakeRefusal("invalid_extraction_target", str(destination))
    if any(destination.iterdir()):
        raise IntakeRefusal("extraction_target_not_empty", str(destination))
    if len(set(member_paths)) != len(member_paths):
        raise IntakeRefusal("duplicate_member_selection", "member paths repeat")
    outputs: list[Path] = []
    staging = destination / ".extraction-staging"
    staging.mkdir()
    try:
        with archive_path.open("rb") as stream:
            try:
                current = _inspect_zip_stream(
                    stream,
                    filename=archive_path.name,
                    size_bytes=os.fstat(stream.fileno()).st_size,
                    expected_sha256=inventory.identity.sha256,
                    limits=limits,
                )
            except IntakeRefusal as exc:
                if exc.reason_code == "archive_digest_mismatch":
                    raise IntakeRefusal(
                        "archive_changed_after_inspection", str(archive_path)
                    ) from exc
                raise
            if current != inventory:
                raise IntakeRefusal("archive_inventory_mismatch", str(archive_path))
            by_path = {member.path: member for member in current.members}
            selected: list[tuple[str, PurePosixPath]] = []
            for name in member_paths:
                member = by_path.get(name)
                if member is None or member.is_directory:
                    raise IntakeRefusal("unsupported_member_selection", name)
                selected.append((name, _safe_member_path(name)))
            stream.seek(0)
            with ZipFile(stream) as archive:
                for name, relative in selected:
                    member = by_path[name]
                    staged = staging.joinpath(*relative.parts)
                    staged.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(name) as source, staged.open("xb") as target:
                        _copy_member(source, target, member, limits)
                    outputs.append(destination.joinpath(*relative.parts))
            if sha256_stream(stream) != inventory.identity.sha256:
                raise IntakeRefusal(
                    "archive_changed_during_extraction", str(archive_path)
                )
    except Exception:
        shutil.rmtree(staging)
        raise
    for staged_output, output in zip(
        (staging.joinpath(*relative.parts) for _, relative in selected),
        outputs,
        strict=True,
    ):
        output.parent.mkdir(parents=True, exist_ok=True)
        staged_output.replace(output)
    shutil.rmtree(staging)
    return tuple(outputs)


def _copy_member(
    source: IO[bytes],
    target: IO[bytes],
    member: ArchiveMember,
    limits: ArchiveLimits,
) -> None:
    copied = 0
    digest = hashlib.sha256()
    while chunk := source.read(_BUFFER_BYTES):
        copied += len(chunk)
        if copied > member.size_bytes or copied > limits.maximum_member_bytes:
            raise IntakeRefusal("archive_output_size_limit", member.path)
        digest.update(chunk)
        target.write(chunk)
    if copied != member.size_bytes:
        raise IntakeRefusal(
            "archive_output_size_mismatch",
            f"{member.path}: expected {member.size_bytes}, got {copied}",
        )
    if member.content_sha256 is None or digest.hexdigest() != member.content_sha256:
        raise IntakeRefusal("archive_member_digest_mismatch", member.path)
