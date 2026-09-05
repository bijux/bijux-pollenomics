"""Atomic publication and immutable output-location validation."""

from __future__ import annotations
from collections.abc import Mapping
import json
import os
from pathlib import Path
import shutil
import tempfile

from .codec import _refuse
from .inputs import _path_has_symlink_component
from .models import PropagationOutputRefusalError


def _payload_record_count(payload_bytes: bytes) -> int:
    payload: object = json.loads(payload_bytes)
    if not isinstance(payload, dict):
        _refuse(
            "invalid_output_reconciliation",
            "every materialized payload must be a JSON object",
        )
    count = payload.get("record_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        _refuse(
            "invalid_output_reconciliation",
            "every materialized payload requires a non-negative record_count",
        )
    return count


def _publish_atomically(
    *,
    output_root: Path,
    allowed_output_parent: Path,
    expected_files: Mapping[str, bytes],
) -> str:
    lock_path = allowed_output_parent / f".{output_root.name}.materialization.lock"
    try:
        lock_descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError as error:
        raise PropagationOutputRefusalError(
            "materialization_lock_exists",
            f"another materialization owns {lock_path.name}",
        ) from error
    try:
        os.close(lock_descriptor)
        if output_root.exists() or output_root.is_symlink():
            if _existing_bundle_is_identical(output_root, expected_files):
                return "unchanged"
            _refuse(
                "non_identical_overwrite_refused",
                "an existing output may only be reused when every byte is identical",
            )
        staging_root = Path(
            tempfile.mkdtemp(
                prefix=f".{output_root.name}.staging-",
                dir=allowed_output_parent,
            )
        )
        try:
            for name in sorted(expected_files):
                target = staging_root / name
                with target.open("xb") as stream:
                    stream.write(expected_files[name])
                    stream.flush()
                    os.fsync(stream.fileno())
            if output_root.exists() or output_root.is_symlink():
                _refuse(
                    "non_identical_overwrite_refused",
                    "the output appeared while its candidate bundle was staged",
                )
            staging_root.rename(output_root)
        except Exception:
            if staging_root.exists():
                shutil.rmtree(staging_root)
            raise
        return "created"
    finally:
        lock_path.unlink(missing_ok=True)


def _existing_bundle_is_identical(
    output_root: Path, expected_files: Mapping[str, bytes]
) -> bool:
    if output_root.is_symlink() or not output_root.is_dir():
        return False
    actual_entries = tuple(sorted(path.name for path in output_root.iterdir()))
    if actual_entries != tuple(sorted(expected_files)):
        return False
    return all(
        not (output_root / name).is_symlink()
        and (output_root / name).is_file()
        and (output_root / name).read_bytes() == expected
        for name, expected in expected_files.items()
    )


def _validate_output_location(output_root: Path, allowed_output_parent: Path) -> None:
    if not output_root.is_absolute() or not allowed_output_parent.is_absolute():
        _refuse(
            "unsafe_output_path",
            "output_root and allowed_output_parent must be absolute paths",
        )
    if ".." in output_root.parts or ".." in allowed_output_parent.parts:
        _refuse("unsafe_output_path", "parent traversal is not allowed")
    if (
        _path_has_symlink_component(allowed_output_parent)
        or not allowed_output_parent.is_dir()
    ):
        _refuse(
            "unsafe_output_path",
            "allowed_output_parent must be an existing non-symlink directory",
        )
    resolved_parent = allowed_output_parent.resolve(strict=True)
    if resolved_parent == Path(resolved_parent.anchor):
        _refuse("unsafe_output_path", "the filesystem root cannot own an output")
    if output_root.parent != allowed_output_parent or not output_root.name:
        _refuse(
            "unsafe_output_path",
            "output_root must be one direct child of allowed_output_parent",
        )
    if _path_has_symlink_component(output_root):
        _refuse("unsafe_output_path", "an output path cannot contain a symlink")
    if output_root.parent.resolve(strict=True) != resolved_parent:
        _refuse("unsafe_output_path", "output_root escapes its allowed parent")
