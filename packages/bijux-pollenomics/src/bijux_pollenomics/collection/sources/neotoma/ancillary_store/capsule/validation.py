"""Full capsule replay authenticates all entity buffers after metadata preflight."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ...capture.facets.replay import replay_neotoma_facet_capture
from ...capture.linked_resources.models import SCOPED_LINKED_SCHEMA
from ...capture.linked_resources.replay import replay_neotoma_linked_resources
from ..linked_evidence.sources import full_evidence_inputs
from .inventory import MAX_BYTES as MAX_BYTES
from .inventory import MAX_FILES as MAX_FILES
from .inventory import (
    prepare_capsule_metadata,
    read_neotoma_ancillary_capsule_inventory,
)
from .models import NeotomaAncillaryCapsule


def prepare_capsule(
    *,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    facet_captures: Mapping[str, Path],
    linked_captures: Mapping[str, Path] | None = None,
    predecessor_facets: Mapping[str, Path] | None = None,
    evidence_sources: Mapping[str, Path] | None = None,
) -> tuple[
    dict[str, Any], dict[str, tuple[Path, int]], dict[str, bytes], dict[str, Any]
]:
    """Validate finite metadata closure, then replay every owned/predecessor entity."""
    prepared = prepare_capsule_metadata(
        context_directory=context_directory,
        expected_context_sha256=expected_context_sha256,
        native_archive_directory=native_archive_directory,
        facet_captures=facet_captures,
        linked_captures=linked_captures,
        predecessor_facets=predecessor_facets,
        evidence_sources=evidence_sources,
        max_bytes=MAX_BYTES,
        max_files=MAX_FILES,
    )
    for digest, root in sorted(prepared.facet_sources.items()):
        replay_neotoma_facet_capture(
            root,
            expected_manifest_sha256=digest,
            scope_inputs=prepared.context.current_scope_inputs,
        )
    for digest, root in sorted(prepared.linked_sources.items()):
        control = prepared.controls[digest]
        if prepared.documents[digest]["schema_version"] == SCOPED_LINKED_SCHEMA:
            inputs = full_evidence_inputs(
                control,
                prepared.context,
                evidence_sources,
                {**(predecessor_facets or {}), **prepared.facet_sources},
            )
        else:
            inputs = {
                "source_facets": {
                    pin: prepared.facet_sources[pin]
                    for pin in control["plan"]["source_facet_manifest_sha256s"]
                },
                "scope_inputs": prepared.context.current_scope_inputs,
            }
        replay_neotoma_linked_resources(root, expected_manifest_sha256=digest, **inputs)
    return prepared.manifest, prepared.paths, prepared.buffers, prepared.index


def load_neotoma_ancillary_capsule(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    predecessor_facets: Mapping[str, Path] | None = None,
    evidence_sources: Mapping[str, Path] | None = None,
) -> NeotomaAncillaryCapsule:
    """Require complete maintained replay; a metadata inventory is never sufficient."""
    metadata = read_neotoma_ancillary_capsule_inventory(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        context_directory=context_directory,
        native_archive_directory=native_archive_directory,
        predecessor_facets=predecessor_facets,
        evidence_sources=evidence_sources,
    )
    _, _, _, index = prepare_capsule(
        context_directory=context_directory,
        expected_context_sha256=metadata.manifest["context_manifest_sha256"],
        native_archive_directory=native_archive_directory,
        facet_captures=metadata.facet_sources,
        linked_captures=metadata.linked_sources,
        predecessor_facets=predecessor_facets,
        evidence_sources=evidence_sources,
    )
    # The inventory authenticates every nonbody buffer; replay authenticates each body.
    return NeotomaAncillaryCapsule(
        metadata.manifest, index, metadata.facet_sources, metadata.linked_sources
    )
