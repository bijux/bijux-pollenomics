"""Operation-local ordinary input trees with explicit unique-byte budgets."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import stat
from types import TracebackType

from .anchors import DIRECTORY_FLAGS, DirectoryAnchor, identity


@dataclass
class _VerifiedBuffer:
    """A callback-scoped literal buffer; copied contexts cannot extend its lease."""

    path: Path
    raw: bytes
    active: bool = True


_VERIFIED_BUFFER: ContextVar[_VerifiedBuffer | None] = ContextVar(
    "verified_input_buffer", default=None
)


def _stamp(node: os.stat_result) -> tuple[int, ...]:
    return (
        *identity(node),
        node.st_nlink,
        node.st_size,
        node.st_mtime_ns,
        node.st_ctime_ns,
    )


def read_regular_file(path: Path, *, max_bytes: int) -> bytes:
    """Return one bounded literal file buffer without following a changed leaf."""
    if type(max_bytes) is not int or max_bytes < 0:
        raise ValueError("Regular input requires a nonnegative native byte bound")
    path = Path(path).absolute()
    verified = _VERIFIED_BUFFER.get()
    if verified is not None and verified.active and verified.path == path:
        if len(verified.raw) > max_bytes:
            raise ValueError("Verified input buffer exceeds its byte bound")
        return verified.raw
    with BoundedInputTree(
        path.parent, max_bytes=max_bytes or 1, max_files=1, selected=path.name
    ) as tree:
        return tree.read(path, max_bytes=max_bytes)


class BoundedInputTree:
    """Seal a finite physical namespace, retaining hashes rather than body buffers."""

    def __init__(
        self,
        root: Path,
        *,
        max_bytes: int,
        max_files: int,
        member_limits: Mapping[str, int] | None = None,
        selected: str | None = None,
    ) -> None:
        """Inventory ordinary members before any body read or semantic decode."""
        if any(type(value) is not int or value < 1 for value in (max_bytes, max_files)):
            raise ValueError("Input tree requires positive native budgets")
        if not all(hasattr(os, flag) for flag in ("O_NOFOLLOW", "O_NONBLOCK")):
            raise ValueError("Nonblocking ordinary input reads are unsupported")
        self.max_bytes, self.max_files = max_bytes, max_files
        self.member_limits = dict(member_limits or {})
        self.selected = selected
        self.anchor = DirectoryAnchor(root)
        self.root = self.anchor.path
        self.digests: dict[str, str] = {}
        try:
            self.files, self.directories = self._inventory()
        except BaseException:
            self.close()
            raise

    def _inventory(
        self,
    ) -> tuple[dict[str, tuple[int, ...]], dict[str, tuple[int, int, int]]]:
        self.anchor.check()
        files: dict[str, tuple[int, ...]] = {}
        directories: dict[str, tuple[int, int, int]] = {"": self.anchor.identity}
        total = visited = 0

        def walk(descriptor: int, prefix: str, depth: int) -> None:
            nonlocal total, visited
            if visit is None:
                raise RuntimeError("Input inventory traversal is closed")
            with os.scandir(descriptor) as entries:
                for entry in entries:
                    if (
                        self.selected is not None
                        and not prefix
                        and entry.name != self.selected
                    ):
                        continue
                    visited += 1
                    if depth > 32 or visited > self.max_files * 33:
                        raise ValueError("Input namespace exceeds its directory budget")
                    name = prefix + entry.name
                    node = entry.stat(follow_symlinks=False)
                    if stat.S_ISDIR(node.st_mode) and self.selected is None:
                        child = os.open(entry.name, DIRECTORY_FLAGS, dir_fd=descriptor)
                        try:
                            if identity(os.fstat(child)) != identity(node):
                                raise ValueError("Input directory identity changed")
                            directories[name] = identity(node)
                            visit(child, name + "/", depth + 1)
                        finally:
                            os.close(child)
                    elif stat.S_ISREG(node.st_mode) and node.st_nlink == 1:
                        total += node.st_size
                        if (
                            len(files) >= self.max_files
                            or total > self.max_bytes
                            or node.st_size
                            > self.member_limits.get(name, self.max_bytes)
                        ):
                            raise ValueError(
                                "Input tree exceeds its file or byte budget"
                            )
                        files[name] = _stamp(node)
                    else:
                        raise ValueError(
                            "Input namespace contains a nonregular or aliased member"
                        )

        visit: Callable[[int, str, int], None] | None = walk
        try:
            if self.selected is not None:
                if (
                    not self.selected
                    or Path(self.selected).name != self.selected
                    or self.selected in {".", ".."}
                ):
                    raise ValueError("Selected input member is not a literal filename")
                node = os.stat(
                    self.selected, dir_fd=self.anchor.fd, follow_symlinks=False
                )
                if not stat.S_ISREG(node.st_mode) or node.st_nlink != 1:
                    raise ValueError("Selected input is not a regular unaliased file")
                if node.st_size > self.max_bytes:
                    raise ValueError("Selected input exceeds its byte bound")
                files[self.selected] = _stamp(node)
            else:
                walk(self.anchor.fd, "", 0)
            self.anchor.check()
            return files, directories
        finally:
            # The recursive visitor cell also owns the scratch inventory.
            # Close it on success and refusal without waiting for cyclic collection.
            visit = None

    def _parent(self, name: str) -> tuple[int, str]:
        parts = Path(name).parts
        descriptor = os.dup(self.anchor.fd)
        prefix = ""
        try:
            for component in parts[:-1]:
                child = os.open(component, DIRECTORY_FLAGS, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
                prefix += component
                if identity(os.fstat(child)) != self.directories.get(prefix):
                    raise ValueError("Input child directory identity changed")
                prefix += "/"
            self.anchor.check()
            return descriptor, parts[-1]
        except BaseException:
            os.close(descriptor)
            raise

    def _name(self, path: Path) -> str:
        path = Path(path).absolute()
        if not path.is_relative_to(self.root) or ".." in path.parts:
            raise ValueError("Input member escapes its physical root")
        name = path.relative_to(self.root).as_posix()
        if name not in self.files:
            raise ValueError("Input member is absent from the closed namespace")
        return name

    def _read(self, name: str, *, retain: bool, max_bytes: int | None = None) -> bytes:
        expected = self.files[name]
        size = expected[4]
        if max_bytes is not None and (type(max_bytes) is not int or max_bytes < size):
            raise ValueError("Input member exceeds its buffer byte bound")
        parent, leaf = self._parent(name)
        descriptor = -1
        try:
            descriptor = os.open(
                leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
            )
            if _stamp(os.fstat(descriptor)) != expected:
                raise ValueError("Opened input regular file identity changed")
            count, digest = 0, sha256()
            chunks: list[bytes] = []
            while block := os.read(descriptor, min(1024 * 1024, size - count + 1)):
                count += len(block)
                if count > size:
                    raise ValueError("Input source growth exceeds its byte bound")
                digest.update(block)
                if retain:
                    chunks.append(block)
            if (
                count != size
                or _stamp(os.fstat(descriptor)) != expected
                or _stamp(os.stat(leaf, dir_fd=parent, follow_symlinks=False))
                != expected
            ):
                raise ValueError("Input source identity or size changed")
            pin = digest.hexdigest()
            if name in self.digests and self.digests[name] != pin:
                raise ValueError("Input content digest changed")
            self.digests[name] = pin
            self.anchor.check()
            return b"".join(chunks)
        except OSError as error:
            raise ValueError("Input regular file could not be opened safely") from error
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            os.close(parent)

    def read(self, path: Path, *, max_bytes: int | None = None) -> bytes:
        """Read one member under its inventoried size, not a fresh tree allowance."""
        return self._read(self._name(path), retain=True, max_bytes=max_bytes)

    def read_with(self, path: Path, reader: Callable[[Path], bytes]) -> bytes:
        """Keep dependency seams bound to the exact independently opened buffer."""
        raw = self.read(path)
        verified = _VerifiedBuffer(Path(path).absolute(), raw)
        token = _VERIFIED_BUFFER.set(verified)
        try:
            returned = reader(path)
        finally:
            verified.active = False
            verified.raw = b""
            _VERIFIED_BUFFER.reset(token)
        if type(returned) is not bytes or returned != raw:
            raise ValueError("Input reader differs from its authenticated buffer")
        parent, leaf = self._parent(self._name(path))
        try:
            if (
                _stamp(os.stat(leaf, dir_fd=parent, follow_symlinks=False))
                != self.files[self._name(path)]
            ):
                raise ValueError("Input reader changed its source member")
        finally:
            os.close(parent)
        return raw

    def check(self) -> None:
        """Recheck the complete physical namespace without silently changing seals."""
        files, directories = self._inventory()
        if files != self.files or directories != self.directories:
            raise ValueError("Input tree namespace or source identity changed")

    def validate(self) -> None:
        """Stream every member through its exact size and retained content pin."""
        self.check()
        for name in self.files:
            self._read(name, retain=False)
        self.check()

    def rebind(self, root: Path) -> None:
        """Follow an intentional attachment only when the held root inode matches."""
        anchor = DirectoryAnchor(root)
        if anchor.identity != self.anchor.identity:
            anchor.close()
            raise ValueError("Input root attachment identity changed")
        self.anchor.close()
        self.anchor, self.root = anchor, anchor.path
        self.check()

    def close(self) -> None:
        """Release the tree anchor without deleting source members."""
        self.anchor.close()

    def __enter__(self) -> BoundedInputTree:
        """Return this operation's live input seal."""
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close descriptors on normal completion and refusal."""
        self.close()
