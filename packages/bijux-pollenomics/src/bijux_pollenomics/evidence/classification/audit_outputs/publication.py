"""Filesystem-safe atomic publication of classification-audit bundles."""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
import shutil
import tempfile

from .constants import MANIFEST_NAME, OUTPUT_NAMES
from .models import ClassificationAuditOutputPaths, ClassificationAuditRefusalError
from .values import refuse


def validate_output_paths(
    paths: ClassificationAuditOutputPaths, allowed_output_parent: Path
) -> None:
    output_root = paths.output_root
    if not output_root.is_absolute() or not allowed_output_parent.is_absolute():
        refuse("unsafe_output_path", "audit output paths must be absolute")
    if ".." in output_root.parts or ".." in allowed_output_parent.parts:
        refuse("unsafe_output_path", "parent traversal is not allowed")
    if allowed_output_parent.is_symlink() or not allowed_output_parent.is_dir():
        refuse(
            "unsafe_output_path",
            "allowed output parent must be an existing non-symlink directory",
        )
    resolved_parent = allowed_output_parent.resolve(strict=True)
    if resolved_parent == Path(resolved_parent.anchor):
        refuse("unsafe_output_path", "filesystem root cannot own audit output")
    if output_root.parent != allowed_output_parent or output_root.is_symlink():
        refuse(
            "unsafe_output_path",
            "audit output root must be one direct non-symlink child",
        )
    declared_paths = (*paths.payload_paths(), paths.manifest)
    expected_names = (*OUTPUT_NAMES, MANIFEST_NAME)
    if (
        any(path.parent != output_root for path in declared_paths)
        or tuple(sorted(path.name for path in declared_paths))
        != tuple(sorted(expected_names))
        or len(set(declared_paths)) != len(declared_paths)
    ):
        refuse(
            "unsafe_output_path",
            "explicit audit paths must match the governed output set",
        )
    if output_root.parent.resolve(strict=True) != resolved_parent:
        refuse("unsafe_output_path", "audit output escapes its allowed parent")


def publish_atomically(
    *,
    output_root: Path,
    allowed_output_parent: Path,
    expected_files: Mapping[str, bytes],
) -> str:
    lock_path = allowed_output_parent / f".{output_root.name}.materialization.lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ClassificationAuditRefusalError(
            "materialization_lock_exists",
            f"another materialization owns {lock_path.name}",
        ) from error
    try:
        os.close(descriptor)
        if output_root.exists() or output_root.is_symlink():
            if existing_bundle_is_identical(output_root, expected_files):
                return "unchanged"
            refuse(
                "non_identical_overwrite_refused",
                "existing audit output is not byte-identical",
            )
        staging_root = Path(
            tempfile.mkdtemp(
                prefix=f".{output_root.name}.staging-",
                dir=allowed_output_parent,
            )
        )
        try:
            for name in sorted(expected_files):
                with (staging_root / name).open("xb") as stream:
                    stream.write(expected_files[name])
                    stream.flush()
                    os.fsync(stream.fileno())
            if output_root.exists() or output_root.is_symlink():
                refuse(
                    "non_identical_overwrite_refused",
                    "audit output appeared while staging",
                )
            staging_root.rename(output_root)
        except Exception:
            if staging_root.exists():
                shutil.rmtree(staging_root)
            raise
        return "created"
    finally:
        lock_path.unlink(missing_ok=True)


def existing_bundle_is_identical(
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
