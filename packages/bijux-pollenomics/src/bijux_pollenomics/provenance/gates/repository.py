"""Repository-bound gate input and output identities."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ..release_evidence import ReleaseEvidenceError, hash_repository_object


def _repository_root(repository_root: Path) -> Path:
    try:
        root = repository_root.resolve(strict=True)
    except OSError as error:
        raise ReleaseEvidenceError("repository root does not exist") from error
    if not root.is_dir():
        raise ReleaseEvidenceError("repository root must be a directory")
    return root


def _input_records(root: Path, input_paths: Sequence[str]) -> list[dict[str, object]]:
    if any(not isinstance(path, str) for path in input_paths):
        raise ReleaseEvidenceError("input paths must be strings")
    paths = sorted(input_paths)
    if not paths:
        raise ReleaseEvidenceError("at least one gate input path is required")
    if len(paths) != len(set(paths)):
        raise ReleaseEvidenceError("duplicate gate input path")
    return [{"path": path, **hash_repository_object(root, path)} for path in paths]


def _output_record(root: Path, path: Path) -> dict[str, object]:
    relative = path.relative_to(root).as_posix()
    result = hash_repository_object(root, relative)
    return {"path": relative, **result}
