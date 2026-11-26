"""Join independently anchored ancillary metadata without opening source entities."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
    load_neotoma_ancillary_federation,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.source_projection import (
    same_source_json,
)

from ..archive_reference import _pinned
from ..models import AtlasResourceCatalogueInput
from .archives import load_supporting_archive_metadata
from .models import AtlasAncillaryMetadata, AtlasAncillarySupportingMetadata

_OWNER_FIELDS = (
    "dataset_id",
    "site_id",
    "collection_unit_id",
    "dataset_type",
    "database",
)


def load_atlas_ancillary_metadata(
    source: AtlasResourceCatalogueInput,
    *,
    catalogue: Mapping[str, Any],
) -> AtlasAncillaryMetadata | None:
    """Preserve dated metadata and exact owners without selecting observations."""
    dependency, native = source.ancillary, source.archive
    if dependency is None:
        return None
    if native is None:
        raise ValueError(
            "Atlas ancillary metadata requires an independent native archive"
        )
    federation, _ = _pinned(
        dependency.directory, "manifest.json", dependency.expected_manifest_sha256
    )
    context, _ = _pinned(
        dependency.context_directory,
        "manifest.json",
        dependency.expected_context_sha256,
    )
    archive, _ = _pinned(
        native.directory, "manifest.json", native.expected_manifest_sha256
    )
    if (
        federation.get("context_manifest_sha256") != dependency.expected_context_sha256
        or federation.get("native_archive_manifest_sha256")
        != native.expected_manifest_sha256
        or not isinstance(context.get("native_archive"), dict)
        or context["native_archive"].get("manifest_sha256")
        != native.expected_manifest_sha256
        or archive.get("catalogue_manifest_sha256") != source.expected_manifest_sha256
    ):
        raise ValueError(
            "Atlas ancillary independent context/native/catalogue anchors differ"
        )
    view = load_neotoma_ancillary_federation(
        dependency.directory,
        expected_manifest_sha256=dependency.expected_manifest_sha256,
        context_directory=dependency.context_directory,
        native_archive_directory=native.directory,
        capsule_sources=dependency.capsule_sources,
        evidence_sources=dependency.evidence_sources,
    )
    resources = {row["dataset_id"]: row for row in catalogue["resources"]}
    facets = view.manifest["declared_facets"]
    seen = set()
    for slot in view.slots:
        owner = slot["root_identity"]
        resource = resources.get(owner["dataset_id"])
        identity = (owner["dataset_id"], slot["facet"])
        if (
            resource is None
            or identity in seen
            or slot["facet"] not in facets
            or not same_source_json(
                owner, {key: resource[key] for key in _OWNER_FIELDS}
            )
        ):
            raise ValueError(
                "Atlas ancillary exact native owner or facet membership differs"
            )
        seen.add(identity)
    if seen != {(dataset, facet) for dataset in resources for facet in facets}:
        raise ValueError(
            "Atlas ancillary native resource/facet population is incomplete"
        )
    provenance = {
        "federation_manifest_sha256": dependency.expected_manifest_sha256,
        "context_manifest_sha256": dependency.expected_context_sha256,
        "native_archive_manifest_sha256": native.expected_manifest_sha256,
        "catalogue_manifest_sha256": source.expected_manifest_sha256,
        "integrity_scope": view.integrity_scope,
        "entity_body_hashes_verified": False,
        "source_assessments_replayed": False,
        "scientific_admission": "not_asserted",
        "original_preget_scope_reconstructed": False,
        "related_resource_graph_complete": False,
        "selection_authority": "not_provided_by_metadata_projection",
    }
    supporting = load_supporting_archive_metadata(source)
    values: dict[str, Any] = {
        "slots": tuple(deepcopy(view.slots)),
        "observations": tuple(deepcopy(view.observations)),
        "linked_occurrences": tuple(deepcopy(view.linked_occurrences)),
        "summary": deepcopy(view.summary),
        "provenance": provenance,
        "source_manifest": deepcopy(view.manifest),
    }

    if supporting:
        return AtlasAncillarySupportingMetadata(
            **values, supporting_archives=supporting
        )
    return AtlasAncillaryMetadata(**values)
