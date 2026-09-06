"""Repository-confined path handling and stable file reads."""

from __future__ import annotations

import os
import stat
from collections.abc import Mapping
from contextlib import suppress
from pathlib import Path, PurePosixPath

from ..release_evidence import ReleaseEvidenceError
from .codec import _load_json


def _read_repository_json(
    repository_root: Path, relative_path: str, *, require_artifacts: bool
) -> Mapping[str, object]:
    root = _repository_root(repository_root)
    path = _existing_repository_path(
        root, relative_path, require_artifacts=require_artifacts
    )
    return _load_json(_read_regular_bytes(path))


def _open_output_parent(
    root: Path, relative_path: str
) -> tuple[int, str, tuple[str, ...]]:
    parts = _relative_parts(relative_path, require_artifacts=True)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(root, flags)
    for part in parts[:-1]:
        try:
            next_descriptor = os.open(part, flags, dir_fd=descriptor)
        except FileNotFoundError:
            with suppress(FileExistsError):
                os.mkdir(part, mode=0o755, dir_fd=descriptor)
            next_descriptor = os.open(part, flags, dir_fd=descriptor)
        except OSError as error:
            os.close(descriptor)
            raise ReleaseEvidenceError(
                f"unsafe output directory for: {relative_path}"
            ) from error
        os.close(descriptor)
        descriptor = next_descriptor
    return descriptor, parts[-1], parts[:-1]


def _verify_output_parent(
    root: Path, parent_parts: tuple[str, ...], expected_descriptor: int
) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    current = os.open(root, flags)
    try:
        for part in parent_parts:
            following = os.open(part, flags, dir_fd=current)
            os.close(current)
            current = following
        expected = os.fstat(expected_descriptor)
        observed = os.fstat(current)
        if (expected.st_dev, expected.st_ino) != (observed.st_dev, observed.st_ino):
            raise ReleaseEvidenceError("release-evidence output parent was substituted")
    except OSError as error:
        raise ReleaseEvidenceError(
            "release-evidence output parent became unsafe"
        ) from error
    finally:
        os.close(current)


def _read_regular_bytes_at(
    parent_descriptor: int, name: str, *, missing_ok: bool
) -> bytes | None:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise ReleaseEvidenceError("release-evidence output disappeared") from None
    except OSError as error:
        raise ReleaseEvidenceError("release-evidence output is unsafe") from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ReleaseEvidenceError("release-evidence output is not a regular file")
        with os.fdopen(os.dup(descriptor), "rb") as stream:
            payload = stream.read()
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ReleaseEvidenceError("release-evidence output changed while reading")
        return payload
    finally:
        os.close(descriptor)


def _existing_repository_path(
    root: Path, relative_path: str, *, require_artifacts: bool
) -> Path:
    parts = _relative_parts(relative_path, require_artifacts=require_artifacts)
    current = root
    for part in parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as error:
            raise ReleaseEvidenceError(
                f"repository path is missing: {relative_path}"
            ) from error
        if stat.S_ISLNK(mode):
            raise ReleaseEvidenceError(f"symlink paths are forbidden: {relative_path}")
    if not stat.S_ISREG(current.lstat().st_mode):
        raise ReleaseEvidenceError(
            f"repository path is not a regular file: {relative_path}"
        )
    return current


def _relative_parts(relative_path: str, *, require_artifacts: bool) -> tuple[str, ...]:
    if not relative_path or "\\" in relative_path:
        raise ReleaseEvidenceError(
            f"invalid repository-relative path: {relative_path!r}"
        )
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or pure.as_posix() != relative_path:
        raise ReleaseEvidenceError(
            f"invalid repository-relative path: {relative_path!r}"
        )
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise ReleaseEvidenceError(f"path escapes repository root: {relative_path!r}")
    if require_artifacts and (not pure.parts or pure.parts[0] != "artifacts"):
        raise ReleaseEvidenceError("release-evidence output must be under artifacts/")
    return pure.parts


def _read_regular_bytes(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ReleaseEvidenceError(
            f"could not safely open repository file: {path}"
        ) from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ReleaseEvidenceError(f"repository path is not a regular file: {path}")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            payload = stream.read()
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    current = path.lstat()
    opened_identity = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
    if opened_identity != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise ReleaseEvidenceError(f"repository file changed while reading: {path}")
    if opened_identity != (
        current.st_dev,
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
    ) or not stat.S_ISREG(current.st_mode):
        raise ReleaseEvidenceError(
            f"repository file identity changed while reading: {path}"
        )
    return payload


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _repository_root(repository_root: Path) -> Path:
    try:
        root = repository_root.resolve(strict=True)
    except OSError as error:
        raise ReleaseEvidenceError("repository root does not exist") from error
    if not root.is_dir():
        raise ReleaseEvidenceError("repository root must be a directory")
    return root
