"""Race-safe atomic publication of canonical repository documents."""

from __future__ import annotations

import os
import secrets
from collections.abc import Callable, Mapping
from contextlib import suppress
from pathlib import Path

from ..release_evidence import ReleaseEvidenceError
from .codec import _canonical_bytes
from .repository import (
    _open_output_parent,
    _read_regular_bytes_at,
    _verify_output_parent,
)


def _publish_canonical_document(
    root: Path,
    output_path: str,
    document: Mapping[str, object],
    *,
    document_name: str,
    validate_payload: Callable[[bytes], None],
) -> None:
    payload = _canonical_bytes(document)
    parent_descriptor, destination_name, parent_parts = _open_output_parent(
        root, output_path
    )
    temporary_name = f".{destination_name}.{secrets.token_hex(16)}.writing"
    try:
        existing = _read_regular_bytes_at(
            parent_descriptor, destination_name, missing_ok=True
        )
        if existing is not None:
            if existing != payload:
                raise ReleaseEvidenceError(
                    f"{document_name} exists with different bytes: {output_path}"
                )
            _verify_output_parent(root, parent_parts, parent_descriptor)
            validate_payload(existing)
            return

        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary_name, flags, 0o600, dir_fd=parent_descriptor)
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as stream:
                stream.write(payload)
                stream.flush()
            os.fchmod(descriptor, 0o644)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        try:
            os.link(
                temporary_name,
                destination_name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError:
            existing = _read_regular_bytes_at(
                parent_descriptor, destination_name, missing_ok=False
            )
            if existing != payload:
                raise ReleaseEvidenceError(
                    f"{document_name} appeared with different bytes: {output_path}"
                ) from None
        os.unlink(temporary_name, dir_fd=parent_descriptor)
        temporary_name = ""
        os.fsync(parent_descriptor)

        written = _read_regular_bytes_at(
            parent_descriptor, destination_name, missing_ok=False
        )
        if written != payload:
            raise ReleaseEvidenceError(f"{document_name} changed during atomic write")
        _verify_output_parent(root, parent_parts, parent_descriptor)
        validate_payload(written)
    finally:
        if temporary_name:
            with suppress(FileNotFoundError):
                os.unlink(temporary_name, dir_fd=parent_descriptor)
        os.close(parent_descriptor)
