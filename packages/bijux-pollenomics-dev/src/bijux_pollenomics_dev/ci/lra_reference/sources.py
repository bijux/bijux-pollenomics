"""Verify already-acquired source archives before running any build program."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import tarfile

from .contracts import ReferenceLock, ReferenceRefusal
from .paths import local_path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_archive(path: Path, package: str, version: str) -> None:
    """Pinned archives admit only internal links to a regular file or directory."""
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            name = PurePosixPath(member.name)
            if (
                name.is_absolute()
                or ".." in name.parts
                or not (
                    member.isfile()
                    or member.isdir()
                    or member.issym()
                    or member.islnk()
                )
            ):
                raise ReferenceRefusal("Unsafe source archive member or link")
            if member.issym() or member.islnk():
                target = PurePosixPath(member.linkname)
                if target.is_absolute() or ".." in target.parts:
                    raise ReferenceRefusal("Unsafe source archive link target")
                location = name.parent / target if member.issym() else target
                destination = archive.getmember(str(location))
                if not (destination.isfile() or destination.isdir()):
                    raise ReferenceRefusal("Source archive link chain is unsupported")
        relative = (
            "R-" + version + "/VERSION" if package == "R" else package + "/DESCRIPTION"
        )
        handle = archive.extractfile(relative)
        if handle is None:
            raise ReferenceRefusal("Source version metadata absent")
        text = handle.read().decode()
        if package == "R":
            if text.strip() != version:
                raise ReferenceRefusal("R source version differs")
        else:
            fields = {
                line.split(":", 1)[0]: line.split(":", 1)[1].strip()
                for line in text.splitlines()
                if line and not line[0].isspace() and ":" in line
            }
            if fields.get("Package") != package or fields.get("Version") != version:
                raise ReferenceRefusal("Package source version differs")


def verify_sources(
    lock: ReferenceLock, cache: Path, repository: Path
) -> dict[str, Path]:
    verified = {}
    for source in lock.sources:
        path = local_path(cache / source.archive_filename)
        if (
            not path.is_file()
            or path.stat().st_size != source.byte_count
            or sha256(path) != source.sha256
        ):
            raise ReferenceRefusal(f"Source bytes missing or changed: {source.package}")
        verify_archive(path, source.package, source.version)
        verified[source.package] = path
    reference = lock.payload["reference"]
    relative = PurePosixPath(reference["repository_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ReferenceRefusal("Unsafe reference repository path")
    path = local_path(repository / relative)
    if not path.is_file() or sha256(path) != reference["sha256"]:
        raise ReferenceRefusal("DISQOVER reference archive differs")
    verify_archive(path, reference["package"], reference["version"])
    verified["disqover"] = path
    _verify_dependency_closure(lock, verified)
    return verified


def _dependency_edges(path: Path, package: str) -> list[dict[str, str | None]]:
    import re

    fields: dict[str, str] = {}
    key = None
    with tarfile.open(path) as archive:
        handle = archive.extractfile(package + "/DESCRIPTION")
        if handle is None:
            raise ReferenceRefusal("Source dependency metadata is missing")
        for line in handle.read().decode().splitlines():
            if line[:1].isspace() and key:
                fields[key] += " " + line.strip()
            elif ":" in line:
                key, value = line.split(":", 1)
                fields[key] = value.strip()
    result = []
    for kind in ("Depends", "Imports", "LinkingTo"):
        for text in fields.get(kind, "").split(","):
            text = text.strip()
            if not text:
                continue
            match = re.fullmatch(
                r"([A-Za-z][A-Za-z0-9.]*)\s*(?:\((>=|<=|==|>|<)\s*([^\)]+)\))?", text
            )
            if match is None:
                raise ReferenceRefusal("Unsupported source dependency syntax")
            name, operator, version = match.groups()
            result.append(
                {
                    "package": name,
                    "kind": kind,
                    "operator": operator,
                    "version": version,
                }
            )
    return result


def _verify_dependency_closure(lock: ReferenceLock, paths: dict[str, Path]) -> None:
    import re

    versions = {row.package: row.version for row in lock.sources}
    versions.update(lock.payload["base_packages"])
    for package, path in paths.items():
        if package == "R":
            continue
        edges = _dependency_edges(path, package)
        declared = next(
            (
                row["dependencies"]
                for row in lock.payload["packages"]
                if row["package"] == package
            ),
            None,
        )
        if declared is not None and edges != declared:
            raise ReferenceRefusal(
                "Locked dependency edges differ from actual source metadata"
            )
        for edge in edges:
            name = edge["package"]
            if not isinstance(name, str):
                raise ReferenceRefusal("Invalid dependency name")
            if name not in versions:
                raise ReferenceRefusal(
                    "Required source dependency is absent from the lock"
                )
            if edge["operator"] is None:
                continue
            actual = tuple(int(item) for item in re.split(r"[.-]", versions[name]))
            wanted = tuple(
                int(item) for item in re.split(r"[.-]", str(edge["version"]))
            )
            width = max(len(actual), len(wanted))
            actual += (0,) * (width - len(actual))
            wanted += (0,) * (width - len(wanted))
            admitted = {
                ">=": actual >= wanted,
                "<=": actual <= wanted,
                "==": actual == wanted,
                ">": actual > wanted,
                "<": actual < wanted,
            }
            if not admitted[str(edge["operator"])]:
                raise ReferenceRefusal(
                    "Locked package version violates its source dependency requirement"
                )


SOURCE_DIRECTORIES = (
    "packages/bijux-pollenomics/src",
    "packages/bijux-pollenomics-lra/src",
    "packages/bijux-pollenomics-lra/tests/reference",
    "packages/bijux-pollenomics-dev/src",
)
SOURCE_METADATA = (
    "packages/bijux-pollenomics/pyproject.toml",
    "uv.lock",
    "pyproject.toml",
    "packages/bijux-pollenomics-lra/pyproject.toml",
    "packages/bijux-pollenomics-dev/pyproject.toml",
    "packages/bijux-pollenomics-lra/vendor/disqover_0.9.14.tar.gz",
)
SOURCE_STATUS_ARGUMENTS = (
    "status",
    "--porcelain",
    "--untracked-files=all",
    "--",
    *SOURCE_DIRECTORIES,
    *SOURCE_METADATA,
    "configs/ci/lra-r-source-lock.v1.json",
)


def source_inventory(repository: Path) -> dict[str, str]:
    files: list[Path] = []
    for relative in SOURCE_DIRECTORIES:
        directory = repository / relative
        if not directory.is_dir() or directory.is_symlink():
            raise ReferenceRefusal("Required source directory is absent or symbolic")
        files.extend(
            path
            for path in directory.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    files.extend(repository / name for name in SOURCE_METADATA)
    if any(path.is_symlink() for path in files):
        raise ReferenceRefusal("Executable source closure contains symlinks")
    return {
        path.relative_to(repository).as_posix(): sha256(path) for path in sorted(files)
    }
