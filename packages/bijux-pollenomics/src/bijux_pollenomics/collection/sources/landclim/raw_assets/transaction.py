"""Descriptor-bound candidate publication retaining predecessors and failures."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import ExitStack, suppress
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import sys
from typing import TypeVar

from .....core.filesystem import recovery_storage

T = TypeVar("T")
DIRECTORY = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
REGULAR = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)


def _stamp(value: os.stat_result) -> tuple[int, ...]:
    return (
        *_identity(value),
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _identity(value: os.stat_result) -> tuple[int, int, int]:
    return value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode)


class _Directory:
    def __init__(self, path: Path, stack: ExitStack, *, create: bool = False):
        self.path = path.absolute()
        self.links: list[tuple[int, str, tuple[int, int, int]]] = []
        self.fd = os.open("/", DIRECTORY)
        stack.callback(os.close, self.fd)
        for name in self.path.parts[1:]:
            if create:
                with suppress(FileExistsError):
                    os.mkdir(name, dir_fd=self.fd)
            child = os.open(name, DIRECTORY, dir_fd=self.fd)
            stack.callback(os.close, child)
            self.links.append((self.fd, name, _identity(os.fstat(child))))
            self.fd = child

    def check(self) -> None:
        for parent, name, expected in self.links:
            if (
                _identity(os.stat(name, dir_fd=parent, follow_symlinks=False))
                != expected
            ):
                raise ValueError("LandClim transaction namespace changed")


def _tree(directory: int, *, copy_to: int | None = None) -> dict[str, object]:
    result: dict[str, object] = {}
    total = 0
    actual_total = 0

    def visit(source: int, prefix: str, target: int | None) -> None:
        nonlocal total, actual_total
        for name in sorted(os.listdir(source)):
            before = os.stat(name, dir_fd=source, follow_symlinks=False)
            relative = prefix + name
            if len(result) >= 10000:
                raise ValueError("LandClim transaction file-count limit")
            if stat.S_ISDIR(before.st_mode):
                child = os.open(name, DIRECTORY, dir_fd=source)
                copied = None
                try:
                    if target is not None:
                        os.mkdir(name, before.st_mode & 0o777, dir_fd=target)
                        copied = os.open(name, DIRECTORY, dir_fd=target)
                    if _identity(os.fstat(child)) != _identity(before):
                        raise ValueError("LandClim transaction directory changed")
                    result[relative] = _identity(before)
                    visit(child, relative + "/", copied)
                finally:
                    os.close(child)
                    if copied is not None:
                        os.close(copied)
            elif stat.S_ISREG(before.st_mode) and before.st_nlink == 1:
                total += before.st_size
                if total > 256 * 1024 * 1024:
                    raise ValueError("LandClim transaction byte limit")
                handle = os.open(name, REGULAR, dir_fd=source)
                output = None
                try:
                    if _stamp(os.fstat(handle)) != _stamp(before):
                        raise ValueError("LandClim transaction source changed")
                    if target is not None:
                        output = os.open(
                            name,
                            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                            before.st_mode & 0o777,
                            dir_fd=target,
                        )
                    digest = hashlib.sha256()
                    remaining = before.st_size
                    while block := os.read(
                        handle,
                        min(
                            1024 * 1024,
                            remaining + 1,
                            256 * 1024 * 1024 - actual_total + 1,
                        ),
                    ):
                        actual_total += len(block)
                        if len(block) > remaining or actual_total > 256 * 1024 * 1024:
                            raise ValueError(
                                "LandClim transaction actual-byte limit or source growth"
                            )
                        remaining -= len(block)
                        digest.update(block)
                        if output is not None:
                            offset = 0
                            while offset < len(block):
                                offset += os.write(output, block[offset:])
                    if (
                        remaining
                        or _stamp(os.fstat(handle)) != _stamp(before)
                        or _stamp(os.stat(name, dir_fd=source, follow_symlinks=False))
                        != _stamp(before)
                    ):
                        raise ValueError("LandClim transaction source changed")
                    result[relative] = (
                        *_identity(before),
                        before.st_size,
                        before.st_mtime_ns,
                        before.st_ctime_ns,
                        digest.hexdigest(),
                    )
                finally:
                    os.close(handle)
                    if output is not None:
                        os.close(output)
            else:
                raise ValueError("LandClim transaction refuses links or special files")

    visit(directory, "", copy_to)
    return result


def _exists(parent: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def _rename_no_replace(
    source: str,
    target: str,
    *,
    src_dir_fd: int,
    dst_dir_fd: int,
    expected_source: tuple[int, int, int],
) -> None:
    """Rename one sealed directory using the OS atomic no-replace primitive."""
    if (
        _identity(os.stat(source, dir_fd=src_dir_fd, follow_symlinks=False))
        != expected_source
    ):
        raise ValueError("LandClim transaction rename source changed")
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin" and hasattr(library, "renameatx_np"):
        rename, flag = library.renameatx_np, 4
    elif sys.platform.startswith("linux") and hasattr(library, "renameat2"):
        rename, flag = library.renameat2, 1
    else:
        raise OSError(
            errno.ENOTSUP, "LandClim atomic no-replace publication unavailable"
        )
    rename.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    rename.restype = ctypes.c_int
    if rename(src_dir_fd, os.fsencode(source), dst_dir_fd, os.fsencode(target), flag):
        error = ctypes.get_errno()
        if error in (errno.EEXIST, errno.ENOTEMPTY):
            raise FileExistsError(error, os.strerror(error), target)
        raise OSError(error, os.strerror(error), target)


def _receipt(run: _Directory, status: str, **fields: object) -> None:
    run.check()
    handle = os.open(
        status + ".json",
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=run.fd,
    )
    with os.fdopen(handle, "w") as stream:
        json.dump({"status": status, **fields}, stream, sort_keys=True)
        stream.write("\n")


def transact(
    destination: Path,
    producer: Callable[[Path], T],
    *,
    publication_root: Path | None = None,
) -> T:
    """Build, seal and replace a tree; never remove an unverified namespace.

    Predecessors and failed candidates remain outside the complete publication root.
    Namespace seals detect substitutions at producer and publication boundaries;
    this is not an OS conditional-rename primitive against hostile schedulers.
    """
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise OSError("LandClim descriptor-bound transactions are unavailable")
    destination = Path(destination).absolute()
    if ".." in destination.parts:
        raise ValueError("LandClim transaction destination is unsafe")
    scope = (
        destination if publication_root is None else Path(publication_root).absolute()
    )
    if ".." in scope.parts or not destination.is_relative_to(scope):
        raise ValueError("LandClim publication root must contain its destination")
    storage_path = recovery_storage.resolve_publication_workspace_parent(
        scope, namespace="landclim-collection"
    )
    if storage_path.is_relative_to(scope):
        raise ValueError("LandClim publication root overlaps recovery storage")
    with ExitStack() as stack:
        parent = _Directory(destination.parent, stack, create=True)
        storage = _Directory(storage_path, stack, create=True)
        if os.fstat(parent.fd).st_dev != os.fstat(storage.fd).st_dev:
            raise ValueError("LandClim transaction requires one filesystem")
        token = "capture-" + secrets.token_hex(12)
        os.mkdir(token, dir_fd=storage.fd)
        run = _Directory(storage_path / token, stack)
        os.mkdir("candidate", dir_fd=run.fd)
        candidate = _Directory(run.path / "candidate", stack)
        original = None
        before = None
        if _exists(parent.fd, destination.name):
            original = _Directory(destination, stack)
            before = _tree(original.fd, copy_to=candidate.fd)
            os.fchmod(candidate.fd, os.fstat(original.fd).st_mode & 0o777)
        moved_prior = False
        moved_candidate = False
        expected = None
        try:
            _receipt(run, "prepared", destination=str(destination))
            value = producer(candidate.path)
            parent.check()
            storage.check()
            run.check()
            candidate.check()
            expected = _tree(candidate.fd)
            _receipt(
                run,
                "sealed",
                candidate_identity=_identity(os.fstat(candidate.fd)),
                candidate=expected,
                predecessor=before,
            )
            if original is not None:
                original.check()
                if _tree(original.fd) != before:
                    raise ValueError("LandClim transaction destination changed")
                _rename_no_replace(
                    destination.name,
                    "prior",
                    src_dir_fd=parent.fd,
                    dst_dir_fd=run.fd,
                    expected_source=_identity(os.fstat(original.fd)),
                )
                moved_prior = True
                if (
                    _identity(os.stat("prior", dir_fd=run.fd, follow_symlinks=False))
                    != _identity(os.fstat(original.fd))
                    or _tree(original.fd) != before
                ):
                    raise ValueError("LandClim transaction predecessor changed")
            elif _exists(parent.fd, destination.name):
                raise ValueError("LandClim transaction destination appeared")
            candidate.check()
            parent.check()
            _rename_no_replace(
                "candidate",
                destination.name,
                src_dir_fd=run.fd,
                dst_dir_fd=parent.fd,
                expected_source=_identity(os.fstat(candidate.fd)),
            )
            moved_candidate = True
            parent.check()
            if (
                _identity(
                    os.stat(destination.name, dir_fd=parent.fd, follow_symlinks=False)
                )
                != _identity(os.fstat(candidate.fd))
                or _tree(candidate.fd) != expected
            ):
                raise ValueError("LandClim transaction publication changed")
            _receipt(
                run,
                "published",
                destination=str(destination),
                retained_predecessor=moved_prior,
            )
            return value
        except BaseException as error:
            try:
                # Retain all artifacts. A foreign replacement is never recursively removed.
                parent.check()
                run.check()
                current_is_candidate = _exists(
                    parent.fd, destination.name
                ) and _identity(
                    os.stat(destination.name, dir_fd=parent.fd, follow_symlinks=False)
                ) == _identity(os.fstat(candidate.fd))
                if moved_candidate and current_is_candidate:
                    with suppress(ValueError, FileExistsError):
                        _rename_no_replace(
                            destination.name,
                            "refused-publication",
                            src_dir_fd=parent.fd,
                            dst_dir_fd=run.fd,
                            expected_source=_identity(os.fstat(candidate.fd)),
                        )
                prior_restored = False
                if moved_prior and not _exists(parent.fd, destination.name):
                    if (
                        original is None
                        or _identity(
                            os.stat("prior", dir_fd=run.fd, follow_symlinks=False)
                        )
                        != _identity(os.fstat(original.fd))
                        or _tree(original.fd) != before
                    ):
                        raise ValueError(
                            "LandClim predecessor requires manual recovery"
                        ) from None
                    try:
                        _rename_no_replace(
                            "prior",
                            destination.name,
                            src_dir_fd=run.fd,
                            dst_dir_fd=parent.fd,
                            expected_source=_identity(os.fstat(original.fd)),
                        )
                    except FileExistsError:
                        pass
                    else:
                        prior_restored = True
                _receipt(
                    run,
                    "refused",
                    destination=str(destination),
                    predecessor_restored=prior_restored,
                    manual_predecessor_recovery=moved_prior and not prior_restored,
                    foreign_destination_preserved=_exists(parent.fd, destination.name)
                    and _identity(
                        os.stat(
                            destination.name, dir_fd=parent.fd, follow_symlinks=False
                        )
                    )
                    not in {
                        _identity(os.fstat(candidate.fd)),
                        _identity(os.fstat(original.fd))
                        if original is not None
                        else None,
                    },
                )
            except Exception as recovery_error:
                error.add_note(
                    "LandClim recovery failed: "
                    f"{type(recovery_error).__name__}: {recovery_error}"
                )
            try:
                run.check()
            except Exception:
                error.add_note(
                    f"LandClim recovery originally allocated at {run.path}; "
                    f"expected directory identity {run.links[-1][2]}; "
                    "current location unverified"
                )
            else:
                error.add_note(f"LandClim recovery state retained at {run.path}")
            raise
