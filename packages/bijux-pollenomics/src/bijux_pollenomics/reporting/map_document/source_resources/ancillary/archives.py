"""Preserve source-only supporting inventories under independently pinned epochs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
    NeotomaContextArchiveBindings,
    read_neotoma_context_resource_inventory,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.reference_tables import (
    read_neotoma_reference_archive_inventory,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
    read_neotoma_unit_metadata_inventory,
)

from ..models import AtlasResourceCatalogueInput
from .models import AtlasContextArchiveInput


def load_supporting_archive_metadata(
    source: AtlasResourceCatalogueInput,
) -> tuple[dict[str, Any], ...]:
    """Inventory authentication never implies selected body or native profile checks."""
    dependency, native = source.ancillary, source.archive
    if dependency is None or dependency.archives is None:
        return ()
    if native is None:
        raise ValueError(
            "Atlas supporting archives require independent current native authority"
        )
    current = NeotomaContextArchiveBindings(
        dependency.context_directory,
        dependency.expected_context_sha256,
        native.directory,
        native.expected_manifest_sha256,
    )
    result = []
    for kind, population in (
        ("unit_metadata", dependency.archives.unit_metadata),
        ("reference_tables", dependency.archives.reference_tables),
        ("context_resources", dependency.archives.context_resources),
    ):
        for reference in population:
            original_anchors: dict[str, Any] = {}
            current_anchors: dict[str, Any] = {}
            scopes = []
            if kind == "reference_tables":
                view = read_neotoma_reference_archive_inventory(
                    reference.directory,
                    expected_manifest_sha256=reference.expected_manifest_sha256,
                )
                manifest, index = view.manifest, view.index
                scope = view.integrity_scope
            else:
                current_anchors = {
                    "context_manifest_sha256": dependency.expected_context_sha256,
                    "native_archive_manifest_sha256": native.expected_manifest_sha256,
                }
                if kind == "unit_metadata":
                    unit = read_neotoma_unit_metadata_inventory(
                        reference.directory,
                        expected_manifest_sha256=reference.expected_manifest_sha256,
                        context_directory=current.context_directory,
                        expected_context_sha256=current.expected_context_sha256,
                        native_archive_directory=current.native_archive_directory,
                        expected_native_archive_sha256=current.expected_native_archive_sha256,
                    )
                    manifest, index = unit.manifest, unit.index
                    scopes = [row["scope"] for row in index["units"]]
                    original_anchors = {
                        "roster_sha256": manifest["original_roster_sha256"]
                    }
                    scope = "archive_metadata_original_and_current_whole_unit_scope"
                else:
                    if not isinstance(reference, AtlasContextArchiveInput):
                        raise ValueError(
                            "Atlas site context requires independent original source bindings"
                        )
                    context = read_neotoma_context_resource_inventory(
                        reference.directory,
                        expected_manifest_sha256=reference.expected_manifest_sha256,
                        original=reference.original,
                        current=current,
                    )
                    manifest, index = context.manifest, context.index
                    scopes = [
                        context.scopes.account(site)
                        for site in context.source.plan.site_ids
                    ]
                    original_anchors = {
                        "context_manifest_sha256": reference.original.expected_context_sha256,
                        "native_archive_manifest_sha256": reference.original.expected_native_archive_sha256,
                    }
                    scope = "archive_metadata_original_and_current_site_scope"
            result.append(
                {
                    "archive_kind": kind,
                    "archive_manifest_sha256": reference.expected_manifest_sha256,
                    "manifest": deepcopy(manifest),
                    "index": deepcopy(index),
                    "scope_accounts": deepcopy(scopes),
                    "original_scope_anchors": original_anchors,
                    "current_scope_anchors": current_anchors,
                    "integrity_scope": scope,
                    "entity_body_hashes_verified": False,
                    "native_profiles_verified": False,
                    "source_assessments_replayed": False,
                    "scientific_admission": "not_asserted",
                    "selected_source_authority": "not_provided_by_metadata_projection",
                    "source_epoch_semantics": "literal_capture_epochs_not_a_synchronized_snapshot",
                    "native_dataset_version": "not_applicable_supporting_source_surface",
                }
            )
    return tuple(result)
