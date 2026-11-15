"""Publish independently bounded literal capture capsules without native duplication."""

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
    MAX_BYTES,
    MAX_FILES,
    load_neotoma_ancillary_capsule,
    prepare_capsule,
)


def write_neotoma_ancillary_capsule(
    directory: Path,
    *,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    facet_captures: Mapping[str, Path],
    linked_captures: Mapping[str, Path] | None = None,
    predecessor_facets: Mapping[str, Path] | None = None,
    evidence_sources: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Replay original source proofs, copy pinned buffers, then verify published bytes."""
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Ancillary capsule already exists: {final}")
    kwargs: dict[str, Any] = {
        "context_directory": context_directory,
        "expected_context_sha256": expected_context_sha256,
        "native_archive_directory": native_archive_directory,
        "facet_captures": facet_captures,
        "linked_captures": linked_captures,
        "predecessor_facets": predecessor_facets,
        "evidence_sources": evidence_sources,
    }
    manifest, paths, buffers, _ = prepare_capsule(**kwargs)
    content = encoded_json(manifest)
    pin = sha256(content).hexdigest()
    staging = build_staging_output_dir(final)
    with OwnedTreeWriter(staging, max_bytes=MAX_BYTES, max_files=MAX_FILES) as writer:
        for relative, (path, maximum) in sorted(paths.items()):
            raw = _read(path, maximum)
            member = manifest["files"][relative]
            if (
                len(raw) != member["bytes"]
                or sha256(raw).hexdigest() != member["sha256"]
            ):
                raise ValueError("Ancillary capsule source copy buffer differs")
            writer.write_bytes(relative, raw)
        for relative, raw in buffers.items():
            writer.write_bytes(relative, raw)
        writer.write_bytes("manifest.json", content)
        load: dict[str, Any] = {
            "expected_manifest_sha256": pin,
            "context_directory": context_directory,
            "native_archive_directory": native_archive_directory,
            "predecessor_facets": predecessor_facets,
            "evidence_sources": evidence_sources,
        }
        publish_owned_source_tree(
            writer,
            staging=staging,
            final=final,
            validate=lambda location: load_neotoma_ancillary_capsule(location, **load),
        )
    return manifest
