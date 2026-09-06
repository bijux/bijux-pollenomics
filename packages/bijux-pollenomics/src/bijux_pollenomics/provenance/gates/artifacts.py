"""Symlink-safe and atomic gate-evidence publication."""

from __future__ import annotations

import os
import stat
import tempfile
from contextlib import suppress
from pathlib import Path

from ..release_evidence import ReleaseEvidenceError
from .validation import _relative_parts


def _prepare_artifacts_directory(root: Path, relative_path: str) -> Path:
    parts = _relative_parts(relative_path)
    if not parts or parts[0] != "artifacts":
        raise ReleaseEvidenceError("gate evidence must be under artifacts/")
    current = root
    for part in parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            with suppress(FileExistsError):
                current.mkdir(mode=0o755)
            mode = current.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ReleaseEvidenceError(
                f"unsafe gate artifacts directory: {relative_path}"
            )
    return current


def _artifact_member(
    root: Path, directory: Path, relative_path: str, field: str
) -> Path:
    parts = _relative_parts(relative_path)
    path = root.joinpath(*parts)
    try:
        path.relative_to(directory)
    except ValueError as error:
        raise ReleaseEvidenceError(
            f"{field} must be inside the gate artifacts directory"
        ) from error
    current = root
    for part in parts[:-1]:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as error:
            raise ReleaseEvidenceError(f"{field} parent does not exist") from error
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ReleaseEvidenceError(f"unsafe {field}")
    if path.exists() or path.is_symlink():
        raise ReleaseEvidenceError(f"{field} must not reuse existing evidence")
    return path


def _temporary_path(directory: Path, name: str) -> Path:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{name}.", suffix=".writing", dir=directory
    )
    os.close(descriptor)
    return Path(temporary_name)


def _atomic_replace(destination: Path, payload: bytes) -> None:
    temporary = _temporary_path(destination.parent, destination.name)
    try:
        with temporary.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o644)
        os.replace(temporary, destination)
        _fsync_directory(destination.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
