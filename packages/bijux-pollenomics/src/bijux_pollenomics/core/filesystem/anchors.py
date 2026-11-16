"""Physical directory capabilities held through descriptor-relative operations."""

from __future__ import annotations

from contextlib import ExitStack, suppress
import os
from pathlib import Path
import stat
from types import TracebackType

DIRECTORY_FLAGS = (
    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
)


def identity(node: os.stat_result) -> tuple[int, int, int]:
    """Return the physical device, inode and ordinary node kind."""
    return node.st_dev, node.st_ino, stat.S_IFMT(node.st_mode)


class DirectoryAnchor:
    """Hold an ordinary directory and every ancestor without resolving aliases."""

    def __init__(
        self, path: Path, *, create: bool = False, creation_mode: int = 0o700
    ) -> None:
        """Open each literal component through its held parent descriptor."""
        if type(creation_mode) is not int or not 0 <= creation_mode <= 0o777:
            raise ValueError("Directory creation mode must be native permission bits")
        self.path = Path(path).absolute()
        if ".." in self.path.parts or not all(
            hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW")
        ):
            raise ValueError(
                "Physical directory anchors require canonical supported paths"
            )
        self._stack = ExitStack()
        self._links: list[tuple[int, str, tuple[int, int, int]]] = []
        self.fd = -1
        try:
            descriptor = os.open(self.path.anchor, DIRECTORY_FLAGS)
            self._stack.callback(os.close, descriptor)
            for component in self.path.parts[1:]:
                if create:
                    with suppress(FileExistsError):
                        os.mkdir(component, creation_mode, dir_fd=descriptor)
                before = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
                child = os.open(component, DIRECTORY_FLAGS, dir_fd=descriptor)
                self._stack.callback(os.close, child)
                if not stat.S_ISDIR(before.st_mode) or identity(before) != identity(
                    os.fstat(child)
                ):
                    raise ValueError(
                        "Physical directory identity changed while opening"
                    )
                self._links.append((descriptor, component, identity(before)))
                descriptor = child
            self.fd = descriptor
            self.identity = identity(os.fstat(descriptor))
            self.check()
        except OSError as error:
            self.close()
            raise ValueError(
                "Physical directory attachment is absent or uses a symlink"
            ) from error
        except BaseException:
            self.close()
            raise

    def check(self) -> None:
        """Refuse a closed anchor or any redirected ancestor attachment."""
        if self.fd < 0:
            raise ValueError("Physical directory anchor is closed")
        for parent, name, expected in self._links:
            if (
                identity(os.stat(name, dir_fd=parent, follow_symlinks=False))
                != expected
            ):
                raise ValueError("Physical directory attachment identity changed")
        if identity(os.fstat(self.fd)) != self.identity:
            raise ValueError("Physical directory descriptor identity changed")

    def close(self) -> None:
        """Release all held descriptors without removing any directory."""
        self.fd = -1
        self._stack.close()

    def __enter__(self) -> DirectoryAnchor:
        """Return the live directory capability."""
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the capability on success and every refusal."""
        self.close()
