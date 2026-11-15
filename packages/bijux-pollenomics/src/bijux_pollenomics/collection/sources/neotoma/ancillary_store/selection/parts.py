"""Bounded operation-local metadata buffers and physical source identity seals."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from hashlib import sha256
import json
from pathlib import Path
import stat
from typing import Any

from ...capture.receipts import _read, _safe_root

MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20000


class VerifiedParts:
    """Private metadata cache; hits never replace independent source identities."""

    def __init__(self, max_bytes: int = MAX_BYTES, max_files: int = MAX_FILES) -> None:
        if any(
            type(value) is not int or not 0 < value <= ceiling
            for value, ceiling in ((max_bytes, MAX_BYTES), (max_files, MAX_FILES))
        ):
            raise ValueError(
                "Operation metadata cache limits exceed their existing ceilings"
            )
        self.max_bytes, self.max_files = max_bytes, max_files
        self.roots: dict[Path, tuple[int, int]] = {}
        self.files: dict[Path, tuple[int, int, int, int, int]] = {}
        self.buffers: dict[tuple[Path, str, str], bytes] = {}
        self.values: dict[str, Any] = {}
        self.retained_bytes = 0
        self.closed = False

    def _open(self) -> None:
        if self.closed:
            raise ValueError("Operation metadata cache is closed")

    def root(self, root: Path) -> None:
        self._open()
        root = _safe_root(root)
        if root.resolve(strict=True) != root:
            raise ValueError("Operation input root is not its physical path")
        node = root.stat(follow_symlinks=False)
        if not stat.S_ISDIR(node.st_mode):
            raise ValueError(
                "Operation input root is not an ordinary physical directory"
            )
        observed = node.st_dev, node.st_ino
        if root in self.roots and self.roots[root] != observed:
            raise ValueError("Operation input root identity changed")
        self.roots[root] = observed

    def seal(self, path: Path, size: int | None = None) -> None:
        self._open()
        path = _safe_root(path)
        if path.resolve(strict=True) != path:
            raise ValueError("Operation metadata member is not its physical path")
        node = path.stat(follow_symlinks=False)
        if (
            not stat.S_ISREG(node.st_mode)
            or node.st_nlink != 1
            or size is not None
            and node.st_size != size
        ):
            raise ValueError(
                "Operation metadata member physical identity or size differs"
            )
        observed = (
            node.st_dev,
            node.st_ino,
            node.st_size,
            node.st_mtime_ns,
            node.st_ctime_ns,
        )
        if path in self.files and self.files[path] != observed:
            raise ValueError("Operation metadata member identity changed")
        if path not in self.files and len(self.files) >= self.max_files:
            raise ValueError("Operation metadata member count exceeds cache budget")
        self.files[path] = observed

    def declarations(
        self, root: Path, files: Mapping[str, Any], *, bodies: bool = False
    ) -> None:
        for name, member in files.items():
            if bodies or not name.endswith(".body"):
                path = root / name
                if not path.is_relative_to(root) or ".." in Path(name).parts:
                    raise ValueError(
                        "Operation metadata declaration escapes source root"
                    )
                self.seal(path, member["bytes"])

    def read(
        self, path: Path, digest: str, bound: int, *, source: str = "metadata"
    ) -> bytes:
        self._open()
        if path.suffix == ".body":
            raise ValueError(
                "Operation metadata cache cannot open a native entity body"
            )
        self.seal(path)
        size = self.files[path][2]
        if type(bound) is not int or not 0 <= size <= bound:
            raise ValueError("Operation metadata member exceeds its byte bound")
        key = path, source, digest
        if key not in self.buffers:
            if self.retained_bytes + size > self.max_bytes:
                raise ValueError("Operation metadata buffers exceed cache byte budget")
            raw = _read(path, bound)
            if sha256(raw).hexdigest() != digest:
                raise ValueError("Operation metadata member digest differs")
            self.seal(path)
            self.buffers[key] = raw
            self.retained_bytes += len(raw)
        return self.buffers[key]

    def memo(self, key: str, load: Callable[[], Any]) -> Any:
        self._open()
        if key not in self.values:
            value = load()
            size = len(json.dumps(value, sort_keys=True, allow_nan=False).encode())
            if self.retained_bytes + size > self.max_bytes:
                raise ValueError("Operation metadata values exceed cache byte budget")
            self.values[key] = value
            self.retained_bytes += size
        return self.values[key]

    def validate(self) -> None:
        self._open()
        for root in tuple(self.roots):
            self.root(root)
        for path in tuple(self.files):
            self.seal(path)

    def close(self) -> None:
        self.buffers.clear()
        self.values.clear()
        self.files.clear()
        self.roots.clear()
        self.closed = True
