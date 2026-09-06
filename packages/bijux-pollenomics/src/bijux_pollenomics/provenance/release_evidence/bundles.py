"""Manifest bundle inventories and payload-closure validation."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from collections.abc import Mapping
from pathlib import Path, PurePosixPath

from .codec import (
    _digest_bytes,
    _int_field,
    _mapping,
    _require_unique,
    _string_field,
)
from .models import (
    _RAW_SHA256_PATTERN,
    ArtifactInput,
    ReleaseEvidenceError,
    _BundleInventory,
    _ReleaseEvidencePolicy,
)
from .repository import (
    _object_identity,
    _open_repository_object,
    _read_file_descriptor,
    _stat_identity,
)


def _validate_manifest_bundle_closures(
    root: Path,
    artifacts: Mapping[str, ArtifactInput],
    policy: _ReleaseEvidencePolicy,
) -> None:
    for inventory in policy.bundle_inventories:
        artifact = artifacts[inventory.artifact_identity]
        manifest_path = PurePosixPath(artifact.path)
        directory_path = manifest_path.parent.as_posix()
        descriptor = _open_repository_object(root, directory_path)
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISDIR(before.st_mode):
                raise ReleaseEvidenceError(
                    f"bundle parent is not a directory: {artifact.identity}"
                )
            _require_public_directory_identity(
                root, directory_path, descriptor, before, artifact.identity
            )
            try:
                observed_names = sorted(os.listdir(descriptor))
            except OSError as error:
                raise ReleaseEvidenceError(
                    f"could not safely list bundle: {artifact.identity}"
                ) from error
            _require_public_directory_identity(
                root, directory_path, descriptor, before, artifact.identity
            )
            expected_names = sorted((*inventory.filenames, manifest_path.name))
            if observed_names != expected_names:
                raise ReleaseEvidenceError(
                    f"bundle file inventory mismatch: {artifact.identity}"
                )
            payloads = {
                name: _read_bundle_member(descriptor, name, artifact.identity)
                for name in expected_names
            }
            after = os.fstat(descriptor)
            if _stat_identity(before) != _stat_identity(after):
                raise ReleaseEvidenceError(
                    f"bundle changed while validating: {artifact.identity}"
                )
            _require_public_directory_identity(
                root, directory_path, descriptor, before, artifact.identity
            )

            _validate_bundle_payload_closure(
                artifact, manifest_path, inventory, payloads
            )
            _require_public_directory_identity(
                root, directory_path, descriptor, before, artifact.identity
            )
        finally:
            os.close(descriptor)


def _require_public_directory_identity(
    root: Path,
    directory_path: str,
    held_descriptor: int,
    expected: os.stat_result,
    artifact_identity: str,
) -> None:
    try:
        public_descriptor = _open_repository_object(root, directory_path)
    except ReleaseEvidenceError as error:
        raise ReleaseEvidenceError(
            f"public bundle directory changed: {artifact_identity}"
        ) from error
    try:
        held = os.fstat(held_descriptor)
        public = os.fstat(public_descriptor)
        if (
            not stat.S_ISDIR(held.st_mode)
            or not stat.S_ISDIR(public.st_mode)
            or _stat_identity(held) != _stat_identity(expected)
            or _stat_identity(public) != _stat_identity(expected)
        ):
            raise ReleaseEvidenceError(
                f"public bundle directory changed: {artifact_identity}"
            )
    finally:
        os.close(public_descriptor)


def _validate_bundle_payload_closure(
    artifact: ArtifactInput,
    manifest_path: PurePosixPath,
    inventory: _BundleInventory,
    payloads: Mapping[str, bytes],
) -> None:
    manifest_payload = payloads[manifest_path.name]
    if _digest_bytes(manifest_payload) != artifact.output_digest:
        raise ReleaseEvidenceError(
            f"bundle manifest identity changed: {artifact.identity}"
        )
    manifest = _json_object(manifest_payload, f"{artifact.identity} manifest")
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ReleaseEvidenceError(
            f"bundle manifest files are missing: {artifact.identity}"
        )
    if manifest.get("payload_file_count") != len(inventory.filenames):
        raise ReleaseEvidenceError(
            f"bundle payload count mismatch: {artifact.identity}"
        )
    normalized_entries: list[tuple[str, str, int]] = []
    for raw_entry in entries:
        entry = _mapping(raw_entry, "bundle manifest entry")
        if set(entry) != {"path", "sha256", "record_count"}:
            raise ReleaseEvidenceError(
                f"bundle manifest entry fields are invalid: {artifact.identity}"
            )
        filename = _string_field(entry, "path")
        digest = _string_field(entry, "sha256")
        record_count = _int_field(entry, "record_count")
        if _RAW_SHA256_PATTERN.fullmatch(digest) is None or record_count < 0:
            raise ReleaseEvidenceError(
                f"bundle manifest entry identity is invalid: {artifact.identity}"
            )
        normalized_entries.append((filename, digest, record_count))
    entry_filenames = [entry[0] for entry in normalized_entries]
    if entry_filenames != list(inventory.filenames):
        raise ReleaseEvidenceError(
            f"bundle manifest inventory mismatch: {artifact.identity}"
        )
    _require_unique(entry_filenames, "bundle manifest filename")
    for filename, expected_digest, expected_record_count in normalized_entries:
        payload = payloads[filename]
        if hashlib.sha256(payload).hexdigest() != expected_digest:
            raise ReleaseEvidenceError(
                f"bundle member digest mismatch: {artifact.identity}: {filename}"
            )
        document = _json_object(
            payload, f"{artifact.identity} bundle member {filename}"
        )
        observed_record_count = document.get("record_count")
        if (
            isinstance(observed_record_count, bool)
            or not isinstance(observed_record_count, int)
            or observed_record_count < 0
            or observed_record_count != expected_record_count
        ):
            raise ReleaseEvidenceError(
                f"bundle member record count mismatch: {artifact.identity}: {filename}"
            )
    digest_input = "".join(
        f"{filename}\0{digest}\0{record_count}\n"
        for filename, digest, record_count in normalized_entries
    ).encode("utf-8")
    if manifest.get("bundle_digest") != hashlib.sha256(digest_input).hexdigest():
        raise ReleaseEvidenceError(
            f"bundle digest reconciliation mismatch: {artifact.identity}"
        )


def _read_bundle_member(
    directory_descriptor: int, filename: str, artifact_identity: str
) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(filename, flags, dir_fd=directory_descriptor)
    except OSError as error:
        raise ReleaseEvidenceError(
            f"bundle member is missing or unsafe: {artifact_identity}: {filename}"
        ) from error
    try:
        opened = os.fstat(descriptor)
        linked = os.stat(filename, dir_fd=directory_descriptor, follow_symlinks=False)
        if not stat.S_ISREG(opened.st_mode) or _object_identity(
            opened
        ) != _object_identity(linked):
            raise ReleaseEvidenceError(
                f"bundle member is not a stable regular file: "
                f"{artifact_identity}: {filename}"
            )
        return _read_file_descriptor(
            descriptor, f"{artifact_identity} bundle member {filename}"
        )
    finally:
        os.close(descriptor)


def _json_object(payload: bytes, label: str) -> Mapping[str, object]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseEvidenceError(f"duplicate JSON field in {label}: {key}")
            result[key] = value
        return result

    try:
        document = json.loads(payload, object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(f"invalid JSON in {label}") from error
    if not isinstance(document, Mapping):
        raise ReleaseEvidenceError(f"JSON object required in {label}")
    return document
