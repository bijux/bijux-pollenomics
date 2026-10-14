"""Confine recorded-gate and shard temporary storage to owned artifacts."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path

from ..release_evidence import ReleaseEvidenceError
from .artifacts import _prepare_artifacts_directory
from .repository import _repository_root
from .validation import _validate_gate_id


def temporary_paths(
    root: Path, artifacts_directory: str, identity: str
) -> tuple[Path, Path]:
    """Describe private temporary and pytest roots without creating anything."""
    _validate_gate_id(identity)
    parent = root / artifacts_directory / "temporary" / identity
    return parent / "tmp", parent / "pytest"


def prepare_temporary_directory(repository_root: Path, path: Path) -> Path:
    """Create an exact artifact directory after checking every existing ancestor."""
    root = _repository_root(repository_root)
    if not path.is_absolute() or ".." in path.parts or path.resolve() != path:
        raise ReleaseEvidenceError("temporary directory must be normalized and real")
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as error:
        raise ReleaseEvidenceError("temporary directory escaped repository") from error
    if relative == "artifacts":
        raise ReleaseEvidenceError("temporary directory must have a private owner")
    return _prepare_artifacts_directory(root, relative)


def prepare_execution_temporary_directories(
    root: Path, argv: Sequence[str], environment: Mapping[str, str]
) -> None:
    """Prepare declared child storage without changing its exact argv or environment."""
    paths = []
    if "TMPDIR" in environment:
        paths.append(Path(environment["TMPDIR"]))
    pytest_arguments = (
        argv[1:]
        if argv and Path(argv[0]).name in {"pytest", "py.test"}
        else argv[3:]
        if tuple(argv[1:3]) == ("-m", "pytest")
        else ()
    )
    for index, argument in enumerate(pytest_arguments):
        if argument == "--basetemp":
            if index + 1 == len(pytest_arguments):
                raise ReleaseEvidenceError("pytest basetemp requires a directory")
            paths.append(Path(pytest_arguments[index + 1]))
        elif argument.startswith("--basetemp="):
            paths.append(Path(argument.partition("=")[2]))
    if len(paths) != len(set(paths)) or any(
        a.is_relative_to(b) or b.is_relative_to(a)
        for index, a in enumerate(paths)
        for b in paths[index + 1 :]
    ):
        raise ReleaseEvidenceError("temporary storage roots must be disjoint")
    # Validate all roots before creating any of them.
    for path in paths:
        if (
            not path.is_absolute()
            or ".." in path.parts
            or path.resolve() != path
            or not path.is_relative_to(root / "artifacts")
            or path == root / "artifacts"
        ):
            raise ReleaseEvidenceError("temporary storage escaped real artifacts")
        for ancestor in (path, *path.parents):
            if ancestor.is_symlink() or (ancestor.exists() and not ancestor.is_dir()):
                raise ReleaseEvidenceError("unsafe temporary storage ancestor")
    for path in paths:
        prepare_temporary_directory(root, path)


def main(argv: Sequence[str] | None = None) -> int:
    """Prepare explicit private storage for direct maintained shard commands."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--directory", required=True, action="append", type=Path)
    args = parser.parse_args(argv)
    root = _repository_root(args.repository_root)
    for path in args.directory:
        prepare_temporary_directory(root, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
