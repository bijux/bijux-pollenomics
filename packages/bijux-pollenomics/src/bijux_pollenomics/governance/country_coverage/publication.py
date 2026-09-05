"""Fail-closed atomic country-coverage publication."""

from __future__ import annotations

from contextlib import suppress
import os
from pathlib import Path
import secrets
import stat
from .constants import (
    COUNTRY_COVERAGE_ARTIFACT_ROOT,
    COUNTRY_COVERAGE_OUTPUT_PATH,
    CountryCoverageError,
)


def _write_atomic_no_follow(
    root_descriptor: int, relative_destination: Path, payload: bytes
) -> None:
    if not relative_destination.parts or relative_destination.name in {"", ".", ".."}:
        raise CountryCoverageError("country coverage output path is invalid")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    opened_directories: list[tuple[int, str, int, tuple[int, int]]] = []
    parent_descriptor = os.dup(root_descriptor)
    temporary_name: str | None = None
    temporary_descriptor = -1
    try:
        for component in relative_destination.parts[:-1]:
            try:
                child_descriptor = os.open(
                    component,
                    directory_flags,
                    dir_fd=parent_descriptor,
                )
            except FileNotFoundError:
                try:
                    os.mkdir(component, 0o755, dir_fd=parent_descriptor)
                    child_descriptor = os.open(
                        component,
                        directory_flags,
                        dir_fd=parent_descriptor,
                    )
                except OSError as error:
                    raise CountryCoverageError(
                        "cannot create country coverage output directory"
                    ) from error
            except OSError as error:
                raise CountryCoverageError(
                    "country coverage output path must not contain symlinks"
                ) from error
            child_status = os.fstat(child_descriptor)
            try:
                named_status = os.stat(
                    component,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            except OSError as error:
                os.close(child_descriptor)
                raise CountryCoverageError(
                    "country coverage output ancestor changed"
                ) from error
            if not stat.S_ISDIR(named_status.st_mode) or (
                child_status.st_dev,
                child_status.st_ino,
            ) != (named_status.st_dev, named_status.st_ino):
                os.close(child_descriptor)
                raise CountryCoverageError("country coverage output ancestor changed")
            opened_directories.append(
                (
                    parent_descriptor,
                    component,
                    child_descriptor,
                    (child_status.st_dev, child_status.st_ino),
                )
            )
            parent_descriptor = child_descriptor
        _verify_open_directory_chain(opened_directories)
        destination_name = relative_destination.name
        _validate_descriptor_destination(parent_descriptor, destination_name)
        for _ in range(100):
            candidate = f".{destination_name}.{secrets.token_hex(12)}.writing"
            try:
                temporary_descriptor = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=parent_descriptor,
                )
            except FileExistsError:
                continue
            temporary_name = candidate
            break
        if temporary_name is None:
            raise CountryCoverageError("cannot allocate country coverage output")
        with os.fdopen(temporary_descriptor, "wb") as stream:
            temporary_descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o644)
        _verify_open_directory_chain(opened_directories)
        _validate_descriptor_destination(parent_descriptor, destination_name)
        os.replace(
            temporary_name,
            destination_name,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
        )
        temporary_name = None
        os.fsync(parent_descriptor)
    finally:
        if temporary_descriptor >= 0:
            os.close(temporary_descriptor)
        if temporary_name is not None:
            with suppress(FileNotFoundError):
                os.unlink(temporary_name, dir_fd=parent_descriptor)
        for parent, _, child, _ in reversed(opened_directories):
            os.close(child)
            if parent != root_descriptor and all(
                parent != prior_child for _, _, prior_child, _ in opened_directories
            ):
                os.close(parent)
        if not opened_directories:
            os.close(parent_descriptor)


def _verify_open_directory_chain(
    opened_directories: list[tuple[int, str, int, tuple[int, int]]],
) -> None:
    for parent_descriptor, component, _, expected_identity in opened_directories:
        try:
            named_status = os.stat(
                component,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError as error:
            raise CountryCoverageError(
                "country coverage output ancestor changed"
            ) from error
        if (
            not stat.S_ISDIR(named_status.st_mode)
            or (
                named_status.st_dev,
                named_status.st_ino,
            )
            != expected_identity
        ):
            raise CountryCoverageError("country coverage output ancestor changed")


def _validate_descriptor_destination(
    parent_descriptor: int, destination_name: str
) -> None:
    try:
        destination_status = os.stat(
            destination_name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return
    if not stat.S_ISREG(destination_status.st_mode):
        raise CountryCoverageError("country coverage output must be a regular file")
    if destination_status.st_nlink != 1:
        raise CountryCoverageError("country coverage output must not be a hard link")


def _safe_output_destination(
    root: Path, output_path: Path, *, protected_paths: tuple[Path, ...]
) -> Path:
    raw_destination = output_path if output_path.is_absolute() else root / output_path
    destination = Path(os.path.abspath(raw_destination))
    if raw_destination != destination:
        raise CountryCoverageError("country coverage output path must not use aliases")
    try:
        destination.relative_to(root)
    except ValueError as error:
        raise CountryCoverageError(
            "country coverage output must remain inside the repository"
        ) from error
    product_output = root / COUNTRY_COVERAGE_OUTPUT_PATH
    artifact_root = root / COUNTRY_COVERAGE_ARTIFACT_ROOT
    if destination != product_output and not destination.is_relative_to(artifact_root):
        raise CountryCoverageError(
            "country coverage output is not an approved product or artifact path"
        )
    _reject_symlink_components(root, destination, "country coverage output path")
    for protected_path in protected_paths:
        protected = protected_path.resolve(strict=True)
        if (
            destination == protected
            or destination in protected.parents
            or protected in destination.parents
            or (destination.exists() and destination.samefile(protected))
        ):
            raise CountryCoverageError(
                "country coverage output overlaps a governed input"
            )
    if destination.exists() and not destination.is_file():
        raise CountryCoverageError("country coverage output must be a regular file")
    if destination.exists() and destination.stat().st_nlink != 1:
        raise CountryCoverageError("country coverage output must not be a hard link")
    return destination


def _reject_symlink_components(root: Path, path: Path, label: str) -> None:
    relative = path.relative_to(root)
    current = root
    for index, part in enumerate(relative.parts):
        current /= part
        if current.is_symlink():
            raise CountryCoverageError(f"{label} must not contain symlinks")
        if (
            index < len(relative.parts) - 1
            and current.exists()
            and not current.is_dir()
        ):
            raise CountryCoverageError(f"{label} ancestor must be a directory")


def _read_governed_input(root: Path, relative_path: str) -> bytes:
    path = root / relative_path
    _reject_symlink_components(root, path, "governed input path")
    if not path.is_file():
        raise CountryCoverageError(
            f"governed input must be a regular file: {relative_path}"
        )
    try:
        return path.read_bytes()
    except OSError as error:
        raise CountryCoverageError(
            f"cannot read governed input: {relative_path}"
        ) from error


def _regular_path_without_symlinks(path: Path, label: str) -> Path:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            raise CountryCoverageError(f"{label} path must not contain symlinks")
    if not absolute.is_file():
        raise CountryCoverageError(f"{label} must be a regular file")
    return absolute
