"""Finite ordinary file namespaces with exactly their declared parent directories."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import stat


def validate_regular_namespace(
    root: Path, expected_files: set[str], *, max_files: int, max_bytes: int
) -> dict[str, int]:
    """Return physical sizes only after a bounded, closed, no-alias preflight."""
    if any(type(value) is not int or value <= 0 for value in (max_files, max_bytes)):
        raise ValueError("Namespace requires positive native finite budgets")
    if not isinstance(expected_files, set) or len(expected_files) > max_files:
        raise ValueError("File population exceeds its namespace bound")
    expected_directories: set[str] = set()
    for relative in expected_files:
        if (
            type(relative) is not str
            or not relative
            or "\\" in relative
            or "\x00" in relative
        ):
            raise ValueError("Namespace member is not a canonical relative path")
        path = PurePosixPath(relative)
        if (
            path.is_absolute()
            or path.as_posix() != relative
            or not path.parts
            or ".." in path.parts
            or len(path.parts) > 32
        ):
            raise ValueError("Namespace member escapes its bounded relative path")
        expected_directories.update(str(p) for p in path.parents if str(p) != ".")
    root = Path(root)
    if (
        not root.is_absolute()
        or any(path.is_symlink() for path in (root, *root.parents))
        or not root.is_dir()
    ):
        raise ValueError("Namespace root is not an ordinary directory")
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("Namespace descriptor-relative traversal is unsupported")
    initial = root.stat(follow_symlinks=False)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    seen_files: dict[str, int] = {}
    seen_directories: set[str] = set()
    visited = total = 0

    def walk(descriptor: int, prefix: str) -> None:
        nonlocal visited, total
        with os.scandir(descriptor) as entries:
            for entry in entries:
                visited += 1
                if visited > len(expected_files) + len(expected_directories):
                    raise ValueError("Namespace exceeds its bounded population")
                relative = prefix + entry.name
                node = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(node.st_mode):
                    if relative not in expected_directories:
                        raise ValueError("Namespace contains an unowned directory")
                    child = os.open(entry.name, flags, dir_fd=descriptor)
                    try:
                        opened = os.fstat(child)
                        if (opened.st_dev, opened.st_ino) != (node.st_dev, node.st_ino):
                            raise ValueError("Namespace child changed while opening")
                        seen_directories.add(relative)
                        walk(child, relative + "/")
                        attached = os.stat(
                            entry.name, dir_fd=descriptor, follow_symlinks=False
                        )
                        if not stat.S_ISDIR(attached.st_mode) or (
                            attached.st_dev,
                            attached.st_ino,
                        ) != (opened.st_dev, opened.st_ino):
                            raise ValueError(
                                "Namespace child directory attachment changed"
                            )
                    finally:
                        os.close(child)
                elif stat.S_ISREG(node.st_mode) and node.st_nlink == 1:
                    if relative not in expected_files:
                        raise ValueError("Namespace file population differs")
                    total += node.st_size
                    if total > max_bytes:
                        raise ValueError("Namespace exceeds its finite byte budget")
                    seen_files[relative] = node.st_size
                else:
                    raise ValueError("Namespace contains a nonregular entry")

    try:
        descriptor = os.open(root, flags)
        try:
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (initial.st_dev, initial.st_ino):
                raise ValueError("Namespace root changed while opening")
            walk(descriptor, "")
            attached = root.stat(follow_symlinks=False)
            if (
                not stat.S_ISDIR(attached.st_mode)
                or any(path.is_symlink() for path in (root, *root.parents))
                or (attached.st_dev, attached.st_ino) != (opened.st_dev, opened.st_ino)
            ):
                raise ValueError("Namespace root directory attachment changed")
        finally:
            os.close(descriptor)
    except OSError as error:
        raise ValueError("Namespace ordinary directory traversal failed") from error
    if set(seen_files) != expected_files or seen_directories != expected_directories:
        raise ValueError("Closed namespace population differs")
    return seen_files
