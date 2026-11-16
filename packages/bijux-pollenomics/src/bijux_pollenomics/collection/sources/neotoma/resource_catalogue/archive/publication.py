"""Publish one complete archive through descriptor-bound writes and atomic no-replace."""

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
from ...capture.resources import NeotomaRetainedSource
from ...publication.ownership import publish_owned_source_tree
from ..publication import load_neotoma_resource_catalogue
from .files import (
    MAX_BYTES,
    MAX_FILES,
    MAX_MANIFEST_BYTES,
    encoded_json,
)
from .inputs import preflight_archive_inputs
from .validation import load_neotoma_source_archive


def write_neotoma_source_archive(
    directory: Path,
    *,
    catalogue_directory: Path,
    expected_catalogue_manifest_sha256: str,
    capture_sources: Mapping[str, Path],
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
    original_relational_root: Path | None = None,
) -> dict[str, Any]:
    """Copy verified original buffers once; downloads point to those same entities.

    Full maintained replay validates exposure roles before numerical entities.
    Complete capsules retain failures and original labels. The index provides
    download links only for successful complete public development entities.
    """
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Neotoma source archive already exists: {final}")
    catalogue_root = _safe_root(catalogue_directory)
    prepared = preflight_archive_inputs(
        catalogue_root,
        expected_catalogue_manifest_sha256=expected_catalogue_manifest_sha256,
        capture_sources=capture_sources,
        retained_sources=retained_sources,
        original_relational_root=original_relational_root,
        max_bytes=MAX_BYTES,
        max_files=MAX_FILES,
        max_manifest_bytes=MAX_MANIFEST_BYTES,
    )
    load_neotoma_resource_catalogue(
        catalogue_root,
        expected_manifest_sha256=expected_catalogue_manifest_sha256,
        capture_sources=capture_sources,
        retained_sources=retained_sources,
        original_relational_root=original_relational_root,
        require_source_bodies=True,
    )
    staging = build_staging_output_dir(final)
    manifest = prepared.manifest
    with OwnedTreeWriter(staging, max_bytes=MAX_BYTES, max_files=MAX_FILES) as writer:
        for relative, (path, maximum) in prepared.paths.items():
            member = manifest["files"][relative]
            content = _read(path, min(maximum, member["bytes"]))
            if (
                len(content) != member["bytes"]
                or sha256(content).hexdigest() != member["sha256"]
            ):
                raise ValueError("Source archive input identity differs")
            writer.write_bytes(relative, content)
        writer.write_bytes("downloads/index.json", prepared.index)
        content = encoded_json(manifest)
        digest = sha256(content).hexdigest()
        writer.write_bytes("manifest.json", content)
        publish_owned_source_tree(
            writer,
            staging=staging,
            final=final,
            validate=lambda location: load_neotoma_source_archive(
                location,
                expected_manifest_sha256=digest,
                original_relational_root=original_relational_root,
            ),
        )
    return manifest
