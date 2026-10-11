"""Bind repeated owner resolution to one scheduling inventory and input custody."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
import stat
from threading import Event
from typing import Any

from ..contracts import ReportRebuildError
from ..ownership import ReportOwnershipError


@dataclass(frozen=True)
class _ScheduleResolutionContext:
    repository: Path
    configuration_path: Path
    inventory_path: Path
    configuration: dict[str, Any]
    inventory: dict[str, Any]
    control_identity: dict[Path, tuple[int, ...]]
    source_identity: dict[str, tuple[int, ...]]
    external_identity: dict[Path, tuple[int, ...]]
    external_sha256: dict[Path, str]
    external_directories: dict[Path, tuple[int, ...]]
    active: Event
    safe_file: Callable[[Path, str, str], Path]
    relative_path: Callable[[Path, Path, str], str]
    digest: Callable[[Path], str]

    def matches(self, repository: Path, configuration: Path, inventory: Path) -> bool:
        return (
            self.active.is_set()
            and repository == self.repository
            and self.relative_path(repository, configuration, "owner configuration")
            == self.configuration_path.as_posix()
            and self.relative_path(repository, inventory, "report ownership")
            == self.inventory_path.as_posix()
        )

    def require_controls(self) -> None:
        for path, identity in self.control_identity.items():
            current = self.safe_file(
                self.repository, path.as_posix(), "schedule control"
            )
            if _file_identity(current) != identity:
                label = (
                    "ownership"
                    if path == self.inventory_path
                    else "owner configuration"
                )
                raise ReportRebuildError(f"{label} changed during scheduling")

    def require_sources(self) -> None:
        self.require_controls()
        for name, identity in self.source_identity.items():
            path = self.safe_file(self.repository, name, "schedule declared source")
            if _file_identity(path) != identity:
                raise ReportRebuildError(
                    "declared source changed during scheduling: " + name
                )

        for path, identity in self.external_directories.items():
            info = path.lstat()
            if not stat.S_ISDIR(info.st_mode) or _file_identity(path)[:3] != identity:
                raise ReportRebuildError("external ancestor changed during scheduling")
        for path, identity in self.external_identity.items():
            if (
                not stat.S_ISREG(path.lstat().st_mode)
                or _file_identity(path)[:4] != identity
                or self.digest(path) != self.external_sha256[path]
            ):
                raise ReportRebuildError("external input changed during scheduling")

    def observe_external(self, path: Path) -> None:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ReportRebuildError("external schedule input is not a regular file")
        identity = _file_identity(path)[:4]
        if path in self.external_identity and self.external_identity[path] != identity:
            raise ReportRebuildError("external input changed during scheduling")
        self.external_identity[path] = identity
        for parent in path.parents:
            if not stat.S_ISDIR(parent.lstat().st_mode):
                raise ReportRebuildError(
                    "external schedule input has non-real ancestor"
                )
            identity = _file_identity(parent)
            # Sibling files do not change this directory's confinement identity.
            identity = identity[:3]
            if (
                parent in self.external_directories
                and self.external_directories[parent] != identity
            ):
                raise ReportRebuildError("external ancestor changed during scheduling")
            self.external_directories[parent] = identity
        if path not in self.external_sha256:
            self.external_sha256[path] = self.digest(path)


_SCHEDULE_RESOLUTION: ContextVar[_ScheduleResolutionContext | None] = ContextVar(
    "configured_owner_schedule_resolution", default=None
)


def _file_identity(path: Path) -> tuple[int, ...]:
    info = path.lstat()
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


@contextmanager
def _owner_schedule_context(
    repository: Path,
    configuration_path: Path,
    inventory_path: Path,
    configuration: dict[str, Any],
    inventory: dict[str, Any],
    *,
    check_ownership: Callable[[Path, Path], object],
    safe_file: Callable[[Path, str, str], Path],
    relative_path: Callable[[Path, Path, str], str],
    digest: Callable[[Path], str],
) -> Iterator[None]:
    """Validate one scheduling inventory; public resolvers keep their normal API."""
    repository = repository.resolve(strict=True)
    try:
        check_ownership(repository, inventory_path)
    except ReportOwnershipError as error:
        raise ReportRebuildError(f"report ownership is invalid: {error}") from error
    controls = {
        path: _file_identity(safe_file(repository, path.as_posix(), "schedule control"))
        for path in (configuration_path, inventory_path)
    }
    names = {
        name
        for declaration in inventory["owners"]
        for name in (
            *declaration["producer_paths"],
            *declaration["producer_inputs"],
            *declaration["paths"],
        )
    }
    sources = {
        name: _file_identity(safe_file(repository, name, "schedule declared source"))
        for name in sorted(names)
    }
    active = Event()
    active.set()
    context = _ScheduleResolutionContext(
        repository,
        configuration_path,
        inventory_path,
        configuration,
        inventory,
        controls,
        sources,
        {},
        {},
        {},
        active,
        safe_file,
        relative_path,
        digest,
    )
    token = _SCHEDULE_RESOLUTION.set(context)
    try:
        yield
        context.require_sources()
    finally:
        active.clear()
        _SCHEDULE_RESOLUTION.reset(token)
