"""Publish a complete directory with the operating system's no-replace guarantee."""

from __future__ import annotations

import ctypes
import errno
import os
from pathlib import Path
import sys

from ..engine.errors import LRARefusal


def publish_directory(stage: Path, destination: Path) -> None:
    """Rename on one filesystem, refusing unsupported primitives and existing paths.

    A separate existence check cannot protect against another writer. Darwin's
    renamex_np(RENAME_EXCL) and Linux's renameat2(RENAME_NOREPLACE) provide that
    guarantee in the rename itself. Windows os.rename also refuses existing paths.
    No replace-capable fallback is used when a filesystem lacks this operation.
    """
    if sys.platform == "win32":
        try:
            os.rename(stage, destination)
        except FileExistsError as exc:
            raise LRARefusal("lra_output_exists", str(destination)) from exc
        return
    library = ctypes.CDLL(None, use_errno=True)
    source = os.fsencode(stage)
    target = os.fsencode(destination)
    if b"\x00" in source or b"\x00" in target:
        raise LRARefusal("invalid_lra_output_path", "NUL in output path")
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
        raise LRARefusal("atomic_publication_unavailable", sys.platform)
    if result:
        error = ctypes.get_errno()
        if error in {errno.EEXIST, errno.ENOTEMPTY}:
            raise LRARefusal("lra_output_exists", str(destination))
        if error in {errno.ENOSYS, errno.EINVAL, errno.ENOTSUP}:
            raise LRARefusal("atomic_publication_unavailable", os.strerror(error))
        raise OSError(error, os.strerror(error), str(destination))
