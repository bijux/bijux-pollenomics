"""Race-resistant repository object identity and state inspection."""

from __future__ import annotations
from contextlib import suppress
import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess  # nosec B404
from typing import cast

from .codec import _digest_bytes, _digest_json
from .models import ReleaseEvidenceError


def _repository_root(repository_root: Path) -> Path:
    try:
        root = repository_root.resolve(strict=True)
    except OSError as error:
        raise ReleaseEvidenceError("repository root does not exist") from error
    if not root.is_dir():
        raise ReleaseEvidenceError("repository root must be a directory")
    return root


def hash_repository_object(
    repository_root: Path, relative_path: str
) -> dict[str, object]:
    """Hash a safe repository-relative regular file or tree canonically."""
    return _hash_repository_object(_repository_root(repository_root), relative_path)


def _relative_path(relative_path: str) -> PurePosixPath:
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
    return pure


def _path_has_prefix(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")


def _hash_repository_object(
    root: Path,
    relative_path: str,
    *,
    exclude_python_cache: bool = False,
) -> dict[str, object]:
    descriptor = _open_repository_object(root, relative_path)
    try:
        mode = os.fstat(descriptor).st_mode
        if stat.S_ISREG(mode):
            digest, byte_size = _hash_file_descriptor(descriptor, relative_path)
            return {
                "object_type": "file",
                "output_digest": digest,
                "byte_size": byte_size,
                "file_count": 1,
            }
        if stat.S_ISDIR(mode):
            entries = _tree_entries_descriptor(
                descriptor, exclude_python_cache=exclude_python_cache
            )
            return {
                "object_type": "tree",
                "output_digest": _digest_json(entries),
                "byte_size": sum(cast(int, entry["byte_size"]) for entry in entries),
                "file_count": len(entries),
            }
    finally:
        os.close(descriptor)
    raise ReleaseEvidenceError(
        f"artifact is not a regular file or directory: {relative_path}"
    )


def _open_repository_object(root: Path, relative_path: str) -> int:
    pure = _relative_path(relative_path)
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    object_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        root_before = os.stat(root, follow_symlinks=False)
        descriptor = os.open(root, directory_flags)
        root_opened = os.fstat(descriptor)
        root_after = os.stat(root, follow_symlinks=False)
        if (
            not stat.S_ISDIR(root_opened.st_mode)
            or _object_identity(root_before) != _object_identity(root_opened)
            or _object_identity(root_opened) != _object_identity(root_after)
        ):
            raise ReleaseEvidenceError("repository root changed while opening")
        for index, part in enumerate(pure.parts):
            flags = object_flags if index == len(pure.parts) - 1 else directory_flags
            next_descriptor = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except ReleaseEvidenceError:
        with suppress(UnboundLocalError):
            os.close(descriptor)
        raise
    except OSError as error:
        with suppress(UnboundLocalError):
            os.close(descriptor)
        raise ReleaseEvidenceError(
            f"artifact path is missing or unsafe: {relative_path}"
        ) from error


def _read_repository_file(root: Path, relative_path: str) -> bytes:
    descriptor = _open_repository_object(root, relative_path)
    try:
        mode = os.fstat(descriptor).st_mode
        if not stat.S_ISREG(mode):
            raise ReleaseEvidenceError(
                f"artifact is not a regular file: {relative_path}"
            )
        return _read_file_descriptor(descriptor, relative_path)
    finally:
        os.close(descriptor)


def _read_file_descriptor(descriptor: int, label: str) -> bytes:
    before = os.fstat(descriptor)
    with os.fdopen(os.dup(descriptor), "rb") as stream:
        payload = stream.read()
    after = os.fstat(descriptor)
    if _stat_identity(before) != _stat_identity(after):
        raise ReleaseEvidenceError(f"file changed while reading: {label}")
    return payload


def _hash_file_descriptor(descriptor: int, label: str) -> tuple[str, int]:
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode):
        raise ReleaseEvidenceError(f"artifact is not a regular file: {label}")
    digest = hashlib.sha256()
    with os.fdopen(os.dup(descriptor), "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    after = os.fstat(descriptor)
    if _stat_identity(before) != _stat_identity(after):
        raise ReleaseEvidenceError(f"file changed while hashing: {label}")
    return f"sha256:{digest.hexdigest()}", before.st_size


def _tree_entries_descriptor(
    descriptor: int,
    prefix: PurePosixPath | None = None,
    *,
    exclude_python_cache: bool = False,
) -> list[dict[str, object]]:
    if prefix is None:
        prefix = PurePosixPath()
    before = os.fstat(descriptor)
    entries: list[dict[str, object]] = []
    try:
        names = sorted(os.listdir(descriptor))
    except OSError as error:
        raise ReleaseEvidenceError("could not safely list artifact tree") from error
    for name in names:
        relative = prefix / name
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            child = os.open(name, flags, dir_fd=descriptor)
        except OSError as error:
            raise ReleaseEvidenceError(
                f"could not safely open artifact tree member: {relative.as_posix()}"
            ) from error
        try:
            member = os.fstat(child)
            path_member = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if (member.st_dev, member.st_ino) != (
                path_member.st_dev,
                path_member.st_ino,
            ):
                raise ReleaseEvidenceError(
                    f"artifact tree member changed: {relative.as_posix()}"
                )
            if (
                stat.S_ISREG(member.st_mode)
                and exclude_python_cache
                and name.endswith((".pyc", ".pyo"))
            ):
                continue
            if stat.S_ISREG(member.st_mode):
                digest, byte_size = _hash_file_descriptor(child, relative.as_posix())
                entries.append(
                    {
                        "path": relative.as_posix(),
                        "output_digest": digest,
                        "byte_size": byte_size,
                    }
                )
            elif stat.S_ISDIR(member.st_mode):
                entries.extend(
                    _tree_entries_descriptor(
                        child,
                        relative,
                        exclude_python_cache=exclude_python_cache,
                    )
                )
            else:
                raise ReleaseEvidenceError(
                    f"special file in artifact tree: {relative.as_posix()}"
                )
        finally:
            os.close(child)
    after = os.fstat(descriptor)
    if _stat_identity(before) != _stat_identity(after):
        raise ReleaseEvidenceError("artifact tree changed while hashing")
    return entries


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _object_identity(value: os.stat_result) -> tuple[int, int]:
    return (value.st_dev, value.st_ino)


def _repository_state(root: Path, mode: str) -> dict[str, object]:
    if mode == "fixture":
        return {
            "mode": "fixture",
            "head_commit": None,
            "head_tree": None,
            "dirty": False,
            "status_digest": None,
            "tracked_paths_digest": None,
            "tracked_diff_digest": None,
            "untracked_objects": [],
        }

    def run(*arguments: str) -> bytes:
        try:
            # The executable is fixed and arguments are internal repository probes.
            completed = subprocess.run(  # nosec B603
                ("git", "-C", str(root), *arguments),
                check=True,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                shell=False,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            raise ReleaseEvidenceError(
                "product release evidence requires an inspectable Git worktree"
            ) from error
        return completed.stdout

    top_level = run("rev-parse", "--show-toplevel").decode().strip()
    if Path(top_level).resolve() != root:
        raise ReleaseEvidenceError("release evidence root is not the Git worktree root")
    head_commit = run("rev-parse", "HEAD").decode().strip()
    head_tree = run("rev-parse", "HEAD^{tree}").decode().strip()
    status = run("status", "--porcelain=v1", "-z", "--untracked-files=all")
    tracked_paths = run("ls-files", "-z")
    tracked_diff = run("diff", "--binary", "HEAD", "--")
    untracked_paths = [
        item.decode("utf-8")
        for item in run("ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
        if item
    ]
    untracked_objects = [
        {"path": path, **_hash_repository_object(root, path)}
        for path in sorted(untracked_paths)
    ]
    return {
        "mode": "product",
        "head_commit": head_commit,
        "head_tree": head_tree,
        "dirty": bool(status),
        "status_digest": _digest_bytes(status),
        "tracked_paths_digest": _digest_bytes(tracked_paths),
        "tracked_diff_digest": _digest_bytes(tracked_diff),
        "untracked_objects": untracked_objects,
    }
