"""Publish a bounded supplementary metadata view without duplicating source entities."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
    publish_new_output_tree,
)

from ...capture.receipts import _safe_root
from ...resource_catalogue.archive.files import encoded_json
from .validation import (
    MAX_BYTES,
    MAX_FILES,
    load_neotoma_ancillary_federation,
    prepare_federation,
)


def write_neotoma_ancillary_federation(
    directory: Path,
    *,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
    evidence_sources: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Publish deterministic metadata; full source replay is an explicit separate API."""
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Ancillary federation already exists: {final}")
    prepared = prepare_federation(
        context_directory=context_directory,
        expected_context_sha256=expected_context_sha256,
        native_archive_directory=native_archive_directory,
        capsule_sources=capsule_sources,
        evidence_sources=evidence_sources,
    )
    raw = encoded_json(prepared.manifest)
    digest = sha256(raw).hexdigest()
    staging = build_staging_output_dir(final)
    with OwnedTreeWriter(staging, max_bytes=MAX_BYTES, max_files=MAX_FILES) as writer:
        for relative, content in prepared.buffers.items():
            writer.write_bytes(relative, content)
        writer.write_bytes("manifest.json", raw)
    kwargs: dict[str, Any] = {
        "expected_manifest_sha256": digest,
        "context_directory": context_directory,
        "native_archive_directory": native_archive_directory,
        "capsule_sources": capsule_sources,
        "evidence_sources": evidence_sources,
    }
    load_neotoma_ancillary_federation(staging, **kwargs)
    publish_new_output_tree(final_output_root=final, staging_output_root=staging)
    load_neotoma_ancillary_federation(final, **kwargs)
    return prepared.manifest
