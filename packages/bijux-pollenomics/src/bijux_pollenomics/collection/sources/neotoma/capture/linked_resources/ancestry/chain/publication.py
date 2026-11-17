"""Publish source-replayed delta records under one live owned directory descriptor."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from .....publication.ownership import publish_owned_source_tree
from .....resource_catalogue.archive.files import encoded_json
from ....receipts import _safe_root
from .. import storage
from ..models import MAX_BYTES, MAX_PARTS
from .authority import ChainOperation
from .capture_inputs import check_group
from .models import (
    COLLECTIONS,
    DEFAULT_LIMITS,
    SCHEMA,
    NeotomaTaxonAncestryChainLimits,
    NeotomaTaxonAncestryChainSources,
    strongest_roles,
)
from .projection import delta, project


def derive_neotoma_taxon_ancestry_chain(
    *,
    sources: NeotomaTaxonAncestryChainSources,
    parent_chain_sha256: str | None,
    new_capture_manifest_sha256s: tuple[str, ...],
    limits: NeotomaTaxonAncestryChainLimits = DEFAULT_LIMITS,
) -> dict[str, Any]:
    """Authenticate complete source closure, preserving original seeds and epochs."""
    limits.validate()
    with ChainOperation(sources) as operation:
        return _derive(
            operation, parent_chain_sha256, new_capture_manifest_sha256s, limits
        )


def _derive(
    operation: ChainOperation,
    parent_chain_sha256: str | None,
    new_capture_manifest_sha256s: tuple[str, ...],
    limits: NeotomaTaxonAncestryChainLimits,
) -> dict[str, Any]:
    sources = operation.sources
    operation.preflight(new_capture_manifest_sha256s, parent_chain_sha256, limits)
    metadata_state, _ = operation.resolve(
        parent_chain_sha256, limits, native_replay=False
    )
    check_group(
        operation,
        metadata_state,
        parent_chain_sha256,
        new_capture_manifest_sha256s,
        limits,
    )
    operation.validate()
    state, previous = operation.resolve(parent_chain_sha256, limits)
    operation.captures(state, parent_chain_sha256, new_capture_manifest_sha256s, limits)
    current = operation.epoch(
        sources.expected_current_context_sha256,
        sources.expected_current_native_archive_sha256,
    )
    projected = project(
        state, strongest_roles(operation.history, current["roles"]), limits
    )
    return delta(
        state,
        projected,
        previous,
        parent=parent_chain_sha256,
        captures=new_capture_manifest_sha256s,
        context=sources.expected_current_context_sha256,
        native=sources.expected_current_native_archive_sha256,
        limits=limits,
    )


def load_neotoma_taxon_ancestry_chain(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    sources: NeotomaTaxonAncestryChainSources,
) -> dict[str, Any]:
    """Replay every declared dependency rather than trusting derived graph flags."""
    with ChainOperation(sources) as operation:
        operation.seal(directory)
        document = storage._readback(
            directory, expected_manifest_sha256, collections=COLLECTIONS, schema=SCHEMA
        )
        expected = _derive(
            operation,
            document["parent_chain_manifest_sha256"],
            tuple(document["new_capture_manifest_sha256s"]),
            NeotomaTaxonAncestryChainLimits(**document["limits"]),
        )
        if document != expected:
            raise ValueError(
                "Ancestry full delta differs from authenticated source closure"
            )
        return document


def publish_neotoma_taxon_ancestry_chain(
    directory: Path,
    *,
    document: dict[str, Any],
    sources: NeotomaTaxonAncestryChainSources,
) -> dict[str, Any]:
    """Retain both trees on refusal and authenticate final output before returning."""
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Ancestry chain already exists: {final}")
    with ChainOperation(sources) as operation:
        expected = _derive(
            operation,
            document["parent_chain_manifest_sha256"],
            tuple(document["new_capture_manifest_sha256s"]),
            NeotomaTaxonAncestryChainLimits(**document["limits"]),
        )
        if document != expected:
            raise ValueError("Ancestry chain source projection differs")
        return _publish_derived_chain(final, operation, expected)


def materialize_neotoma_taxon_ancestry_chain(
    directory: Path,
    *,
    sources: NeotomaTaxonAncestryChainSources,
    parent_chain_sha256: str | None,
    new_capture_manifest_sha256s: tuple[str, ...],
    limits: NeotomaTaxonAncestryChainLimits = DEFAULT_LIMITS,
) -> dict[str, Any]:
    """Derive and publish a chain while its original source authority stays live.

    Native baseline qualification occurs once within this operation. Staged and
    final output validation retain the same source seals and permission duties;
    no qualification is reusable after the operation closes.
    """
    limits.validate()
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Ancestry chain already exists: {final}")
    with ChainOperation(sources) as operation:
        expected = _derive(
            operation, parent_chain_sha256, new_capture_manifest_sha256s, limits
        )
        return _publish_derived_chain(final, operation, expected)


def _publish_derived_chain(
    final: Path, operation: ChainOperation, expected: dict[str, Any]
) -> dict[str, Any]:
    """Publish only the projection derived under this still-live source owner."""
    operation._check_live()
    manifest, buffers = storage._pack(expected, collections=COLLECTIONS, schema=SCHEMA)
    raw = encoded_json(manifest)
    pin = sha256(raw).hexdigest()
    staging = build_staging_output_dir(final)

    def validate(path: Path) -> dict[str, Any]:
        operation.validate()
        retained = storage._readback(path, pin, collections=COLLECTIONS, schema=SCHEMA)
        if retained != expected:
            raise ValueError("Ancestry staged/final source projection differs")
        operation.validate()
        return retained

    with OwnedTreeWriter(
        staging, max_bytes=MAX_BYTES, max_files=MAX_PARTS + 1
    ) as writer:
        for name, content in buffers.items():
            writer.write_bytes(name, content)
        writer.write_bytes("manifest.json", raw)
        publish_owned_source_tree(
            writer, staging=staging, final=final, validate=validate
        )
    return manifest
