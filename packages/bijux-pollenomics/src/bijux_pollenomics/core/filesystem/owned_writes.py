"""Exclusive bounded writes anchored to one owned ordinary directory inode."""

from __future__ import annotations

import ctypes
import errno
import os
from pathlib import Path, PurePosixPath
import secrets
import stat
import sys
from types import TracebackType


def _rename_directory(descriptor: int, source: str, target: str) -> None:
    """Attach an owned private directory without replacing a competing entry."""
    if any(len(OwnedTreeWriter._parts(name)) != 1 for name in (source, target)):
        raise ValueError("Exclusive attachment requires literal child components")
    if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
        raise ValueError("Exclusive attachment requires an open parent directory")
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin" and hasattr(library, "renameatx_np"):
        rename, flags = library.renameatx_np, 4
    elif sys.platform == "linux" and hasattr(library, "renameat2"):
        rename, flags = library.renameat2, 1
    else:
        raise OSError(errno.ENOTSUP, "Exclusive descriptor-relative rename unsupported")
    rename.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    rename.restype = ctypes.c_int
    if rename(descriptor, os.fsencode(source), descriptor, os.fsencode(target), flags):
        error = ctypes.get_errno()
        if error in {errno.EEXIST, errno.ENOTEMPTY}:
            raise FileExistsError(error, os.strerror(error), target)
        if error in {errno.ENOSYS, errno.EINVAL, errno.ENOTSUP}:
            error = errno.ENOTSUP
        raise OSError(error, os.strerror(error), target)


class OwnedTreeWriter:
    """Write new files without following replaced roots or child directories.

    The constructor creates an absent root through exclusive atomic attachment.
    This writer exclusively owns its unpredictable private creation
    names; other writers may compete for canonical names. Open directory
    descriptors, exact inode checks and exclusive attachment preserve those
    competing entries. Failures retain all private owned evidence.
    """

    def __init__(self, root: Path, *, max_bytes: int, max_files: int) -> None:
        if any(
            type(value) is not int or value <= 0 for value in (max_bytes, max_files)
        ):
            raise ValueError("Owned writes require positive native finite budgets")
        if (
            sys.platform not in {"darwin", "linux"}
            or not hasattr(os, "O_NOFOLLOW")
            or not hasattr(os, "O_DIRECTORY")
            or not {os.open, os.mkdir, os.stat} <= os.supports_dir_fd
        ):
            raise OSError(
                errno.ENOTSUP, "Descriptor-bound owned writes are unsupported"
            )
        self.root = Path(root)
        self._max_bytes, self._max_files = max_bytes, max_files
        self._bytes = 0
        self._directory_creations = 0
        self._files: set[str] = set()
        self._root_fd = -1
        self._flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        if not self.root.is_absolute():
            raise ValueError("Owned staging root must be an absolute canonical path")
        parent = self.root.parent
        self._physical_directory(parent)
        initial = parent.stat(follow_symlinks=False)
        descriptor = os.open(parent, self._flags)
        try:
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (initial.st_dev, initial.st_ino):
                raise ValueError(
                    "Owned staging parent changed while opening its anchor"
                )
            if os.path.lexists(self.root):
                raise FileExistsError(self.root)
            self._root_fd = self._new_directory(descriptor, self.root.name)
            node = os.fstat(self._root_fd)
            self._identity = node.st_dev, node.st_ino
            self._directories: dict[tuple[str, ...], tuple[int, int]] = {
                (): self._identity
            }
            self.validate_attachment()
        except BaseException:
            self.close()
            raise
        finally:
            os.close(descriptor)

    @staticmethod
    def _physical_directory(path: Path) -> None:
        if (
            not path.is_absolute()
            or path.resolve(strict=True) != path
            or any(member.is_symlink() for member in (path, *path.parents))
            or not path.is_dir()
        ):
            raise ValueError(
                "Owned staging directory is absent, redirected or nonordinary"
            )

    def validate_attachment(self) -> None:
        """Require the original open inode to remain at its declared staging path."""
        if self._root_fd < 0:
            raise ValueError("Owned staging writer is closed")
        self._physical_directory(self.root)
        node = self.root.stat(follow_symlinks=False)
        opened = os.fstat(self._root_fd)
        if (
            not stat.S_ISDIR(node.st_mode)
            or (node.st_dev, node.st_ino) != self._identity
            or (opened.st_dev, opened.st_ino) != self._identity
        ):
            raise ValueError("Owned staging directory identity changed")

    @staticmethod
    def _parts(relative: str) -> tuple[str, ...]:
        if (
            type(relative) is not str
            or not relative
            or "\\" in relative
            or "\x00" in relative
        ):
            raise ValueError("Owned file path is not a canonical relative member")
        path = PurePosixPath(relative)
        if (
            path.is_absolute()
            or path.as_posix() != relative
            or not path.parts
            or ".." in path.parts
            or len(path.parts) > 32
        ):
            raise ValueError("Owned file path escapes its bounded relative namespace")
        return path.parts

    def _new_directory(self, parent: int, component: str) -> int:
        if self._directory_creations >= self._max_files * 32:
            raise ValueError("Private owned directory population exceeds its bound")
        self._directory_creations += 1
        private = ".owned-directory-" + secrets.token_hex(16)
        os.mkdir(private, dir_fd=parent)
        initial = os.stat(private, dir_fd=parent, follow_symlinks=False)
        descriptor = os.open(private, self._flags, dir_fd=parent)
        try:
            identity = initial.st_dev, initial.st_ino
            node = os.fstat(descriptor)
            if (node.st_dev, node.st_ino) != identity or os.listdir(descriptor):
                raise ValueError(
                    "Private owned directory identity or emptiness changed"
                )
            _rename_directory(parent, private, component)
            attached = os.stat(component, dir_fd=parent, follow_symlinks=False)
            if (
                not stat.S_ISDIR(attached.st_mode)
                or (attached.st_dev, attached.st_ino) != identity
                or os.listdir(descriptor)
            ):
                raise ValueError("Canonical owned directory attachment changed")
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def _directory(self, parts: tuple[str, ...], *, create: bool) -> int:
        self.validate_attachment()
        descriptor = os.dup(self._root_fd)
        prefix: tuple[str, ...] = ()
        try:
            for component in parts:
                prefix += (component,)
                if prefix not in self._directories:
                    if not create or len(self._directories) >= self._max_files * 32 + 1:
                        raise ValueError(
                            "Owned directory population exceeds its bounds"
                        )
                    child = self._new_directory(descriptor, component)
                else:
                    child = os.open(component, self._flags, dir_fd=descriptor)
                try:
                    self.validate_attachment()
                    node = os.fstat(child)
                    identity = node.st_dev, node.st_ino
                    if self._directories.get(prefix, identity) != identity:
                        raise ValueError("Owned child directory identity changed")
                    self._directories[prefix] = identity
                except BaseException:
                    os.close(child)
                    raise
                os.close(descriptor)
                descriptor = child
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def write_bytes(self, relative: str, content: bytes) -> None:
        """Create one exclusive regular file beneath the owned directory descriptors."""
        parts = self._parts(relative)
        if type(content) is not bytes:
            raise ValueError("Owned writes require an immutable byte buffer")
        if relative in self._files:
            raise FileExistsError(relative)
        if (
            self._bytes + len(content) > self._max_bytes
            or len(self._files) >= self._max_files
        ):
            raise ValueError("Owned staging writes exceed their finite budget")
        directory = self._directory(parts[:-1], create=True)
        try:
            descriptor = os.open(
                parts[-1],
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o666,
                dir_fd=directory,
            )
            try:
                node = os.fstat(descriptor)
                if not stat.S_ISREG(node.st_mode) or node.st_nlink != 1:
                    raise ValueError("Owned output is not an exclusive regular file")
                self._bytes += len(content)
                self._files.add(relative)
                remaining = memoryview(content)
                while remaining:
                    count = os.write(descriptor, remaining)
                    if count <= 0:
                        raise OSError("Owned file write made no progress")
                    remaining = remaining[count:]
                written = os.fstat(descriptor)
                canonical = os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
                if (
                    not stat.S_ISREG(canonical.st_mode)
                    or canonical.st_nlink != 1
                    or written.st_nlink != 1
                    or (canonical.st_dev, canonical.st_ino)
                    != (written.st_dev, written.st_ino)
                    or canonical.st_size != len(content)
                    or written.st_size != len(content)
                ):
                    raise ValueError(
                        "Owned canonical file leaf identity or size changed"
                    )
            finally:
                os.close(descriptor)
        finally:
            os.close(directory)
        attached = self._directory(parts[:-1], create=False)
        os.close(attached)
        self.validate_attachment()

    def close(self) -> None:
        """Release the anchor even after a refusal; never remove another writer's data."""
        if self._root_fd >= 0:
            descriptor, self._root_fd = self._root_fd, -1
            os.close(descriptor)

    def __enter__(self) -> OwnedTreeWriter:
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
