"""Publish an absent JSON output set and roll back only owned destination links."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import ExitStack
from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import tempfile


@dataclass(frozen=True)
class _StagedJson:
    path: Path
    output: Path
    identity: tuple[int, int]
    payload: bytes


def _identity(path: Path) -> tuple[int, int] | None:
    """Identify a regular named file without following a substituted symlink."""
    try:
        status = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(status.st_mode):
        return None
    return status.st_dev, status.st_ino


def _unlink_owned(path: Path, identity: tuple[int, int]) -> None:
    """Leave replacement directory entries untouched during cleanup."""
    if _identity(path) == identity:
        path.unlink(missing_ok=True)


def _require_payload(path: Path, stage: _StagedJson) -> None:
    """Bind a named link to the staged inode and serialized payload."""
    if _identity(path) != stage.identity:
        raise ValueError(f"JSON publication inode changed: {path}")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino) != stage.identity:
            raise ValueError(f"JSON publication inode changed: {path}")
        if stream.read() != stage.payload:
            raise ValueError(f"JSON publication payload changed: {path}")
    if _identity(path) != stage.identity:
        raise ValueError(f"JSON publication inode changed: {path}")


def publish_json_outputs(outputs: Sequence[tuple[Path, dict[str, object]]]) -> None:
    """Publish complete JSON payloads without replacing existing destination entries.

    Serialization and staging finish before any output is linked. A failed link or
    identity check removes earlier links only while they still name our inode.
    Separate destination names are briefly visible during publication; callers
    requiring simultaneous visibility must use one directory-level publication.
    """
    serialized = [
        (
            path,
            (
                json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
            ).encode(),
        )
        for path, payload in outputs
    ]
    stages: list[_StagedJson] = []
    published: list[_StagedJson] = []
    with ExitStack() as handles:
        try:
            for path, payload in serialized:
                path.parent.mkdir(parents=True, exist_ok=True)
                stream = handles.enter_context(
                    tempfile.NamedTemporaryFile(
                        mode="w+b",
                        dir=path.parent,
                        prefix=f".{path.name}.pending-",
                        delete=False,
                    )
                )
                opened = os.fstat(stream.fileno())
                stage = _StagedJson(
                    Path(stream.name),
                    path,
                    (opened.st_dev, opened.st_ino),
                    payload,
                )
                stages.append(stage)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
                _require_payload(stage.path, stage)
            for stage in stages:
                _require_payload(stage.path, stage)
                os.link(stage.path, stage.output, follow_symlinks=False)
                published.append(stage)
                _require_payload(stage.output, stage)
            for stage in stages:
                _require_payload(stage.output, stage)
        except BaseException:
            for stage in reversed(published):
                _unlink_owned(stage.output, stage.identity)
            raise
        finally:
            for stage in stages:
                _unlink_owned(stage.path, stage.identity)
