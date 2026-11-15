"""Transactional acquisition shared by the stable LandClim entry points."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import ExitStack
import os
from pathlib import Path
import secrets

from .transaction import _Directory, _tree, transact
from .validation import validate_payload


def download_assets(
    raw_dir: Path,
    urls: dict[str, str],
    fetch: Callable[[str], bytes],
    validate: Callable[[str, bytes], None],
) -> dict[str, Path]:
    """Keep all existing assets until every fetched native payload is checked."""
    for filename in urls:
        if not filename or Path(filename).name != filename or filename in (".", ".."):
            raise ValueError("LandClim raw asset filename is unsafe")

    def produce(candidate: Path) -> None:
        with ExitStack() as stack:
            directory = _Directory(candidate, stack)
            for filename, url in urls.items():
                before = _tree(directory.fd)
                payload = fetch(url)
                directory.check()
                if _tree(directory.fd) != before:
                    raise ValueError(
                        "LandClim raw asset candidate changed during download"
                    )
                validate(filename, payload)
                name = ".download-" + secrets.token_hex(12)
                handle = os.open(
                    name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory.fd,
                )
                with os.fdopen(handle, "wb") as stream:
                    stream.write(payload)
                os.rename(
                    name, filename, src_dir_fd=directory.fd, dst_dir_fd=directory.fd
                )
                directory.check()

    transact(raw_dir, produce)
    return {filename: Path(raw_dir) / filename for filename in urls}


__all__ = ["download_assets", "transact", "validate_payload"]
