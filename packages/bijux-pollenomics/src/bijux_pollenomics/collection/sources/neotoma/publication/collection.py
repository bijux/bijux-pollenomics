"""Closed byte inventory for the older source/normalized/review collector."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import stat
from typing import Any

from bijux_pollenomics.core.filesystem import (
    OwnedTreeWriter,
    validate_regular_namespace,
)

MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20000


class CollectionTreeWriter(OwnedTreeWriter):
    """Record every explicit file write without asserting provider HTTP custody."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, max_bytes=MAX_BYTES, max_files=MAX_FILES)
        self.members: dict[str, dict[str, Any]] = {}
        self.sealed = False

    def write_bytes(self, relative: str, content: bytes) -> None:
        if self.sealed:
            raise ValueError("Closed Neotoma collection cannot accept more writes")
        super().write_bytes(relative, content)
        self.members[relative] = {
            "bytes": len(content),
            "sha256": sha256(content).hexdigest(),
        }

    def seal(self) -> None:
        """Persist local byte identity separately from scientific source admission."""
        raw = json.dumps(
            {
                "schema_version": "neotoma-local-collection.v1",
                "files": self.members,
                "source_bytes": sum(row["bytes"] for row in self.members.values()),
                "http_custody": "not_recorded_by_legacy_collector",
                "scientific_admission": "not_asserted",
            },
            sort_keys=True,
            indent=2,
            allow_nan=False,
        ).encode("utf-8")
        self.write_bytes("collection-manifest.json", raw)
        self.sealed = True

    def validate(self, root: Path) -> None:
        """Read each bounded ordinary member through its directory descriptors."""
        if not self.sealed:
            raise ValueError("Neotoma collection byte inventory is not closed")
        sizes = validate_regular_namespace(
            root, set(self.members), max_files=MAX_FILES, max_bytes=MAX_BYTES
        )
        for name, expected in self.members.items():
            if sizes[name] != expected["bytes"]:
                raise ValueError("Neotoma collection member size differs")
            self._validate_member(root, name, expected)
        validate_regular_namespace(
            root, set(self.members), max_files=MAX_FILES, max_bytes=MAX_BYTES
        )

    @staticmethod
    def _validate_member(root: Path, name: str, expected: dict[str, Any]) -> None:
        descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            parts = Path(name).parts
            for component in parts[:-1]:
                child = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=descriptor,
                )
                os.close(descriptor)
                descriptor = child
            leaf = os.open(
                parts[-1],
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=descriptor,
            )
            with os.fdopen(leaf, "rb") as stream:
                opened = os.fstat(stream.fileno())
                if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                    raise ValueError("Neotoma collection member identity differs")
                digest, count = sha256(), 0
                while raw := stream.read(
                    min(1024 * 1024, expected["bytes"] + 1 - count)
                ):
                    digest.update(raw)
                    count += len(raw)
                    if count > expected["bytes"]:
                        break
                attached = os.stat(parts[-1], dir_fd=descriptor, follow_symlinks=False)
                if (
                    (attached.st_dev, attached.st_ino) != (opened.st_dev, opened.st_ino)
                    or attached.st_nlink != 1
                    or count != expected["bytes"]
                    or digest.hexdigest() != expected["sha256"]
                ):
                    raise ValueError("Neotoma collection member byte identity differs")
        finally:
            os.close(descriptor)
