"""Expose retained source bytes without presenting Git objects as physical files."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .index import read_source_path


class ByteSource(Protocol):
    """A read-only byte source; it grants no import, execution or filesystem access."""

    def read_bytes(self) -> bytes:
        """Return the authenticated source body."""
        ...


@dataclass(frozen=True)
class ScopedSourceMember:
    """Bind one logical read to the caller's already validated source batch."""

    read_source: Callable[[str], bytes]
    member: str

    def read_bytes(self) -> bytes:
        """Reuse the scoped reader's complete custody checks and original identity."""
        return self.read_source(self.member)


@dataclass(frozen=True)
class RetainedSourceMember:
    """Resolve a declared logical capture member through its pinned Git transport."""

    repository: Path
    logical_path: Path

    def read_bytes(self) -> bytes:
        """Read bounded original bytes from the explicitly indexed capture."""
        return read_source_path(self.repository, self.logical_path)
