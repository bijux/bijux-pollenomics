"""Publish one immutable copy of ancillary scientific context evidence."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
)

from ...capture.receipts import _read, _safe_root
from ...publication.ownership import publish_owned_source_tree
from ...resource_catalogue.archive.files import encoded_json
from .validation import (
    _LEGACY_SCOPE,
    MAX_BYTES,
    MAX_FILES,
    MAX_MEMBER_BYTES,
    SCHEMA,
    evidence_member,
    load_neotoma_ancillary_context,
    native_context,
)


def write_neotoma_ancillary_context(
    directory: Path,
    *,
    native_archive_directory: Path,
    expected_native_archive_sha256: str,
    legacy_rosters: Mapping[str, Path],
    exposure_authority: Path,
    expected_exposure_authority_sha256: str,
) -> dict[str, Any]:
    """Copy original buffers once, bind current-use resolvers, and publish exclusively."""
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Ancillary context already exists: {final}")
    if (
        not isinstance(legacy_rosters, Mapping)
        or not legacy_rosters
        or len(legacy_rosters) + 2 > MAX_FILES
    ):
        raise ValueError("Ancillary context legacy roster population is malformed")
    native, _, _, _ = native_context(
        native_archive_directory, expected_native_archive_sha256
    )
    authority_path = f"evidence/exposure/{expected_exposure_authority_sha256}.json"
    raw = _read(exposure_authority, MAX_MEMBER_BYTES)
    authority = evidence_member(raw, expected_exposure_authority_sha256, authority_path)
    if native["reviewed_exposure_metadata_sha256"] not in (
        None,
        expected_exposure_authority_sha256,
    ):
        raise ValueError(
            "Ancillary context exposure authority differs from current scope"
        )
    buffers = {authority_path: raw}
    legacy = {}
    for pin, path in sorted(legacy_rosters.items()):
        relative = f"rosters/{pin}.json"
        raw = _read(
            path, min(MAX_MEMBER_BYTES, MAX_BYTES - sum(map(len, buffers.values())))
        )
        member = evidence_member(raw, pin, relative)
        legacy[pin] = {**member, **_LEGACY_SCOPE}
        buffers[relative] = raw
    manifest = {
        "schema_version": SCHEMA,
        "native_archive": native,
        "exposure_authority": authority,
        "legacy_rosters": legacy,
        "files": {
            relative: {"sha256": sha256(raw).hexdigest(), "bytes": len(raw)}
            for relative, raw in buffers.items()
        },
        "source_bytes": sum(map(len, buffers.values())),
        "scientific_admission": "not_asserted",
        "native_body_copies": 0,
        "current_scope_verification": "resolver_identity_only_parent_obligations_not_replayed",
        "pre_get_scope_reconstructed": False,
        "historical_snapshot_replaced": False,
    }
    content = encoded_json(manifest)
    pin = sha256(content).hexdigest()
    staging = build_staging_output_dir(final)
    with OwnedTreeWriter(staging, max_bytes=MAX_BYTES, max_files=MAX_FILES) as writer:
        for relative, raw in buffers.items():
            writer.write_bytes(relative, raw)
        writer.write_bytes("manifest.json", content)
        publish_owned_source_tree(
            writer,
            staging=staging,
            final=final,
            validate=lambda location: load_neotoma_ancillary_context(
                location,
                expected_manifest_sha256=pin,
                native_archive_directory=native_archive_directory,
            ),
        )
    return manifest
