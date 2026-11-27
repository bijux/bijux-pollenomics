"""Attach one fully formed private receipt without replacing an existing entry."""

from contextlib import suppress
import json
import os
from pathlib import Path
import secrets
import stat
from typing import Any

from bijux_pollenomics.core.filesystem import DirectoryAnchor


def write_private_receipt(path: Path, payload: dict[str, Any]) -> None:
    """Commit a complete 0600 receipt by exclusive link under a 0700 parent.

    The exclusive link is the commit point. Private staging cleanup and descriptor
    close are best effort afterward; no final path is unlinked for rollback. A
    cleanup failure can leave a second private link. Same-user movement of the
    parent directory is not a hostile-concurrency pathname guarantee.
    """
    path = Path(path)
    if not path.is_absolute() or path.name in {"", ".", ".."}:
        raise ValueError("Private receipt path must be absolute")
    data = (
        json.dumps(
            payload, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False
        )
        + "\n"
    ).encode()
    if len(data) > 1024 * 1024:
        raise ValueError("Private receipt exceeds byte budget")
    anchor = DirectoryAnchor(path.parent)
    name: str | None = None
    try:
        parent = os.fstat(anchor.fd)
        if parent.st_uid != os.geteuid() or stat.S_IMODE(parent.st_mode) != 0o700:
            raise ValueError("Private receipt parent must be owner-only")
        name = ".receipt-" + secrets.token_hex(16)
        fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=anchor.fd,
        )
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            node = os.fstat(stream.fileno())
            if (
                stat.S_IMODE(node.st_mode) != 0o600
                or not stat.S_ISREG(node.st_mode)
                or node.st_nlink != 1
                or node.st_size != len(data)
            ):
                raise ValueError("Private receipt staging identity differs")
        anchor.check()
        os.link(
            name,
            path.name,
            src_dir_fd=anchor.fd,
            dst_dir_fd=anchor.fd,
            follow_symlinks=False,
        )
    finally:
        if name is not None:
            with suppress(OSError):
                os.unlink(name, dir_fd=anchor.fd)
        with suppress(OSError):
            anchor.close()
