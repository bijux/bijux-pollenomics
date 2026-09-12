"""Filesystem replacement primitives for complete runtime-owned trees."""

from __future__ import annotations

import ctypes
import errno
import os
from pathlib import Path
import shutil
import sys

__all__ = [
    "build_recovery_output_dir",
    "build_staging_output_dir",
    "publish_new_output_tree",
    "remove_output_tree",
    "replace_output_tree",
]


def publish_new_output_tree(
    *, final_output_root: Path, staging_output_root: Path
) -> None:
    """Publish a new tree with an atomic OS no-replace operation on one filesystem.

    Existing destinations are never replaced. Unsupported primitives/filesystems
    raise OSError with ENOTSUP; there is no check-then-replace fallback. Failed
    staging output remains available to its owning producer for diagnosis.
    """
    source, target = os.fsencode(staging_output_root), os.fsencode(final_output_root)
    if b"\x00" in source or b"\x00" in target:
        raise ValueError("NUL in output path")
    if sys.platform == "win32":
        os.rename(staging_output_root, final_output_root)
        return
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin" and hasattr(library, "renamex_np"):
        rename = library.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(source, target, 4)  # RENAME_EXCL, Darwin sys/stdio.h
    elif sys.platform.startswith("linux") and hasattr(library, "renameat2"):
        rename = library.renameat2
        rename.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename.restype = ctypes.c_int
        result = rename(-100, source, -100, target, 1)  # AT_FDCWD; RENAME_NOREPLACE
    else:
        raise OSError(
            errno.ENOTSUP,
            "Atomic no-replace publication unavailable",
            str(final_output_root),
        )
    if result:
        error = ctypes.get_errno()
        if error in {errno.EEXIST, errno.ENOTEMPTY}:
            raise FileExistsError(error, os.strerror(error), str(final_output_root))
        if error in {errno.ENOSYS, errno.EINVAL, errno.ENOTSUP}:
            raise OSError(errno.ENOTSUP, os.strerror(error), str(final_output_root))
        raise OSError(error, os.strerror(error), str(final_output_root))


def remove_output_tree(path: Path) -> None:
    """Remove one runtime-owned file or directory tree when it exists."""
    path = Path(path)
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def build_staging_output_dir(final_output_root: Path) -> Path:
    """Return the hidden sibling used to construct a complete candidate tree."""
    final_output_root = Path(final_output_root)
    return final_output_root.parent / f".{final_output_root.name}.staging"


def build_recovery_output_dir(final_output_root: Path) -> Path:
    """Return the hidden sibling that protects the prior governed tree."""
    final_output_root = Path(final_output_root)
    return final_output_root.parent / f".{final_output_root.name}.recovery"


def replace_output_tree(*, final_output_root: Path, staging_output_root: Path) -> None:
    """Replace one owned tree while restoring its predecessor on rename failure."""
    final_output_root = Path(final_output_root)
    staging_output_root = Path(staging_output_root)
    recovery_output_root = build_recovery_output_dir(final_output_root)
    remove_output_tree(recovery_output_root)

    prior_state_exists = final_output_root.exists()
    if prior_state_exists:
        final_output_root.replace(recovery_output_root)

    try:
        staging_output_root.replace(final_output_root)
    except Exception:
        if prior_state_exists and recovery_output_root.exists():
            recovery_output_root.replace(final_output_root)
        raise
    else:
        remove_output_tree(recovery_output_root)
