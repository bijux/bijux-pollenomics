"""Read regular candidate members without importing generation or media execution."""

from __future__ import annotations

import os
from pathlib import Path
import stat

from .contracts import AtlasBrowserContractError


def regular_bytes(path: Path) -> bytes:
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise AtlasBrowserContractError(f"symbolic link in candidate: {path}")
    try:
        descriptor = os.open(
            path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0)
        )
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise AtlasBrowserContractError(f"nonregular candidate member: {path}")
            return stream.read()
    except OSError as error:
        raise AtlasBrowserContractError(
            f"cannot read candidate member: {path}"
        ) from error


__all__ = ["regular_bytes"]
