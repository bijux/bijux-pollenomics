"""Deterministic and atomic publication of compact AADR accountability receipts."""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
import tempfile

from .validation import validate_aadr_source_accountability_receipt

_replace_file = os.replace


def canonical_aadr_source_accountability_bytes(
    receipt: Mapping[str, object],
) -> bytes:
    """Encode one validated receipt with reproducible UTF-8 JSON formatting."""
    validate_aadr_source_accountability_receipt(receipt)
    return (
        json.dumps(
            receipt,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def write_aadr_source_accountability_receipt(
    path: Path,
    receipt: Mapping[str, object],
    *,
    governed_root: Path,
) -> bytes:
    """Atomically write one compact receipt and return its exact bytes."""
    payload = canonical_aadr_source_accountability_bytes(receipt)
    destination = Path(path)
    _validate_governed_destination(destination, Path(governed_root))
    destination.parent.mkdir(parents=True, exist_ok=True)
    _validate_governed_destination(destination, Path(governed_root))
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".writing",
        dir=destination.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with temporary.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o644)
        _replace_file(temporary, destination)
        _fsync_directory(destination.parent)
    finally:
        if temporary.exists():
            temporary.unlink()
    return payload


def _validate_governed_destination(destination: Path, governed_root: Path) -> None:
    root = Path(os.path.abspath(governed_root))
    candidate = Path(os.path.abspath(destination))
    if governed_root.is_symlink() or not governed_root.is_dir():
        raise ValueError(
            "AADR accountability data root must be a non-symlink directory"
        )
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            "AADR accountability output must remain under its data root"
        ) from exc
    if not relative.parts:
        raise ValueError("AADR accountability output cannot replace its data root")

    resolved_root = root.resolve(strict=True)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("AADR accountability output cannot use a symlink")
        if current.exists():
            try:
                current.resolve(strict=True).relative_to(resolved_root)
            except ValueError as exc:
                raise ValueError(
                    "AADR accountability output must remain under its data root"
                ) from exc


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


__all__ = [
    "canonical_aadr_source_accountability_bytes",
    "write_aadr_source_accountability_receipt",
]
